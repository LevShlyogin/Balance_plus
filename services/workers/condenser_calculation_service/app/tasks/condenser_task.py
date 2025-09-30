import traceback
from typing import List
from app import celery_app
from app.schemas import CalculationInputV1_2, CalculationResultsV1_2
from app.calculator.berman import BermanStrategy
from app.calculator.metro_vickers import MetroVickersStrategy
from app.calculator.vku import VKUStrategy
from app.calculator.table_pressure import TablePressureStrategy
from app.utils.io import load_input_file, load_geometry_data, save_results_file
from app.utils.validation import validate_strategy_parameters
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name='calculation.condenser', queue='condenser_calculation_queue')
def calculate_condenser(
    self,
    correlation_id: str,
    repo_url: str,
    branch: str,
    commit_hash: str,
    input_files: List[str],
    output_file: str,
) -> str:
    """
    Основная Celery-задача для расчёта конденсатора.
    
    Args:
        correlation_id: Уникальный ID для трассировки
        repo_url: URL Git-репозитория
        branch: Ветка репозитория
        commit_hash: Хеш коммита входных данных
        input_files: Список путей к входным файлам
        output_file: Путь к выходному файлу
    
    Returns:
        Статус выполнения задачи
    """
    try:
        logger.info(f"[{correlation_id}] Starting condenser calculation task")
        logger.info(f"[{correlation_id}] Commit: {commit_hash}, Input: {input_files[0]}")
        
        # === Шаг 1: Загрузка входных данных ===
        input_path = input_files[0]
        input_data = load_input_file(input_path)
        model = CalculationInputV1_2.model_validate(input_data)
        
        logger.info(f"[{correlation_id}] Strategy: {model.calculation_strategy}")
        
        # === Шаг 2: Загрузка и объединение геометрии ===
        if model.geometry_source.type == "reference":
            geometry_path = model.geometry_source.path
            geometry_data = load_geometry_data(geometry_path)
            logger.info(f"[{correlation_id}] Loaded geometry from: {geometry_path}")
        else:
            raise NotImplementedError("Inline geometry is not supported in v1.2")
        
        # Объединённый словарь входных данных
        params = {
            **geometry_data,
            **model.parameters
        }
        
        strategy = model.calculation_strategy
        
        # === Шаг 3: Выбор и выполнение стратегии ===
        validate_strategy_parameters(params, strategy)
        
        if strategy == "berman":
            results = BermanStrategy().calculate(params)
            results_wrapped = {"berman_results": results}
        elif strategy == "metro_vickers":
            results = MetroVickersStrategy().calculate(params)
            results_wrapped = {"metro_vickers_results": results}
        elif strategy == "vku":
            vku = VKUStrategy(
                mass_flow_steam_nom=params['mass_flow_steam_nom'],
                degree_dryness_steam_nom=params['degree_dryness_steam_nom']
            )
            results = vku.calculate(params)
            results_wrapped = {"vku_results": results}
        elif strategy == "table_pressure":
            results = TablePressureStrategy().calculate(params)
            results_wrapped = {"table_pressure_results": results}
        else:
            raise ValueError(f"Unknown calculation strategy: {strategy}")
        
        logger.info(f"[{correlation_id}] Calculation completed successfully")
        
        # === Шаг 4: Подготовка выходного JSON ===
        sources_copy = {
            "geometry": {
                "project_path": model.geometry_source.source_info.project_path,
                "commit_hash": model.geometry_source.source_info.commit_hash,
                "path": model.geometry_source.path
            },
            "parameters": {
                "project_path": model.parameters_source.source_info.project_path,
                "commit_hash": model.parameters_source.source_info.commit_hash,
                "path": model.parameters_source.path
            }
        }
        
        output_model = CalculationResultsV1_2(
            schema_version="1.2",
            input_commit_hash=commit_hash,
            calculation_strategy=strategy,
            meta={
                "target_project": {
                    "path": model.meta.target_project_path,
                    "attributes": {}
                },
                "sources": sources_copy
            },
            results=results_wrapped
        )
        
        output_dict = output_model.model_dump(by_alias=True)
        
        # === Шаг 5: Сохранение ===
        save_results_file(output_dict, output_file)
        logger.info(f"[{correlation_id}] Results saved to: {output_file}")
        
        return "SUCCESS"
    
    except FileNotFoundError as e:
        logger.error(f"[{correlation_id}] File not found: {e}")
        self.update_state(state="FAILURE", meta={"error": str(e)})
        raise
    
    except ValueError as e:
        logger.error(f"[{correlation_id}] Validation error: {e}")
        self.update_state(state="FAILURE", meta={"error": str(e)})
        raise
    
    except Exception as e:
        traceback_str = traceback.format_exc()
        logger.error(f"[{correlation_id}] Unexpected error: {traceback_str}")
        
        # Retry для сетевых ошибок (например, Git push)
        if "push" in str(e).lower() or "network" in str(e).lower():
            logger.warning(f"[{correlation_id}] Retrying due to transient error")
            raise self.retry(exc=e, countdown=60, max_retries=3)
        
        self.update_state(state="FAILURE", meta={"error": traceback_str})
        raise