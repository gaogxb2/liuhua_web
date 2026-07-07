from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    folder_path: Optional[str] = None
    extract_zip: bool = False


class LookupRequest(BaseModel):
    barcode1: Optional[str] = None
    barcode2: Optional[str] = None


class MapRegionItem(BaseModel):
    name: str
    ratio: float
    fault_count: int
    total_count: int


class MapStatsResponse(BaseModel):
    level: str
    items: List[MapRegionItem]
    map_provinces: List[str] = []
    display_year: Optional[int] = None
    display_month: Optional[int] = None
    overall: Dict[str, Any]


class FaultRateItem(BaseModel):
    province: str
    city: str = ""
    fault_count: int
    total_count: int
    ratio: float


class LookupResponse(BaseModel):
    provinces: List[FaultRateItem]
    cities: List[FaultRateItem]
    matched_count: int


class AlertItem(BaseModel):
    province: str
    city: str
    fault_count: int
    total_count: int
    ratio: float


class CodeBarItem(BaseModel):
    code_value: int
    code_hex: str
    board_count: int


class FaultTrendItem(BaseModel):
    time: str
    ratio: float
    fault_count: int
    total_count: int


class CodeSumTrendPoint(BaseModel):
    time_label: str
    year: int
    month: int
    code_sum: int
    site_name: str = ""


class CodeSumTrendSeries(BaseModel):
    chip: str
    site_name: str
    label: str
    points: List[CodeSumTrendPoint]


class CodeSumTrendResponse(BaseModel):
    series: List[CodeSumTrendSeries]


class FilterOptionsResponse(BaseModel):
    chips: List[str]
    provinces: List[str]
    city_map: Dict[str, List[str]]
    years: List[int]
    year_month_map: Dict[int, List[int]] = Field(default_factory=dict)
    site_names: List[str] = Field(default_factory=list)
    latest_year: Optional[int] = None
    latest_month: Optional[int] = None
    folder_path: str = ""


class AnalyzeResponse(BaseModel):
    total_boards: int
    folder_path: str
    filters: FilterOptionsResponse
