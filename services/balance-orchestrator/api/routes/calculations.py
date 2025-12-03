import json
from datetime import datetime
from fastapi import APIRouter, HTTPException
from schemas.calculation import CalculationSaveRequest
from gitlab_adapter import gitlab_client
from slugify import slugify

router = APIRouter(prefix="/calculations", tags=["Calculations"])

@router.post("/save")
async def save_calculation_result(req: CalculationSaveRequest):
    """
    Сохраняет результаты расчёта в Git.
    Путь: calculations/{app_type}/{timestamp}/
    """
    try:
        # 1. Получаем задачу для формирования имени ветки
        issue = gitlab_client.get_issue(req.task_iid)
        
        safe_slug = slugify(issue["title"], max_length=40) or "task"
        branch_name = f"issue/{req.task_iid}-{safe_slug}"
        
        # Проверка существования ветки
        if not gitlab_client.branch_exists(branch_name):
             raise HTTPException(status_code=400, detail=f"Ветка {branch_name} не найдена. Начните работу над задачей.")

        # 2. Формируем уникальную папку для этого запуска расчёта
        # Если в output_data есть timestamp, берем его, иначе текущий
        ts_str = req.output_data.get('calc_timestamp') or datetime.now().isoformat()
        # Делаем timestamp безопасным для имени папки (убираем двоеточия)
        folder_name = ts_str.replace(':', '-').replace('.', '-')
        
        base_path = f"calculations/{req.app_type}/{folder_name}"
        
        # 3. Готовим файлы
        files_to_commit = {
            f"{base_path}/input.json": json.dumps(req.input_data, indent=2, ensure_ascii=False),
            f"{base_path}/result.json": json.dumps(req.output_data, indent=2, ensure_ascii=False)
        }

        # 4. Коммитим
        commit = gitlab_client.create_commit_multiple(
            files=files_to_commit,
            commit_message=f"Calc Result: {req.commit_message}",
            branch=branch_name
        )

        return {
            "status": "saved", 
            "commit_id": commit.id, 
            "path": base_path,
            "web_url": commit.web_url
        }

    except Exception as e:
        print(f"Error saving calculation: {e}")
        raise HTTPException(status_code=500, detail=str(e))