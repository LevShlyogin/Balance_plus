from pydantic import BaseModel, Field
from typing import Literal, Dict, Any, Optional


# ============================
# 🔁 Reusable Components
# ============================

class SourceInfo(BaseModel):
    project_path: str
    commit_hash: str


# ============================
# 📥 Input Schema (condenser_input.json)
# ============================

class InputMeta(BaseModel):
    target_project_path: str


class GeometrySource(BaseModel):
    type: Literal["reference"]
    source_info: SourceInfo
    path: str


class ParametersSource(BaseModel):
    type: Literal["reference"]
    source_info: SourceInfo
    path: Optional[str] = None


class CalculationInputV1_2(BaseModel):
    schema_version: Literal["1.2"]
    meta: InputMeta = Field(alias="_meta")
    geometry_source: GeometrySource
    parameters_source: ParametersSource
    calculation_strategy: Literal["berman", "metro_vickers", "vku", "table_pressure"]
    parameters: Dict[str, Any]

    class Config:
        populate_by_name = True
        extra = "forbid"


# ============================
# 📤 Output Schema (condenser_results.json)
# ============================

class TargetProjectMeta(BaseModel):
    path: str
    attributes: Dict[str, Any] = {}


class SourceDetails(BaseModel):
    project_path: str
    commit_hash: str
    path: Optional[str] = None


class SourcesMeta(BaseModel):
    geometry: SourceDetails
    parameters: SourceDetails


class OutputMeta(BaseModel):
    target_project: TargetProjectMeta
    sources: SourcesMeta


class CalculationResultsV1_2(BaseModel):
    schema_version: Literal["1.2"]
    input_commit_hash: str
    calculation_strategy: str
    meta: OutputMeta = Field(alias="_meta")
    results: Dict[str, Any]

    class Config:
        populate_by_name = True
        extra = "forbid"