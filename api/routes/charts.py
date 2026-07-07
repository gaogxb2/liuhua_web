from typing import Optional

from fastapi import APIRouter, HTTPException

from api.schemas import CodeBarItem, CodeSumTrendResponse
from api.services import analytics

router = APIRouter(prefix="/api/charts", tags=["charts"])


@router.get("/code-bar", response_model=list[CodeBarItem])
def code_bar(
    chip: Optional[str] = None,
    province: Optional[str] = None,
    city: Optional[str] = None,
    site: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
):
    try:
        return analytics.get_code_bar_chart(
            chip=chip, province=province, city=city, site=site, year=year, month=month,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/code-sum-trend", response_model=CodeSumTrendResponse)
def code_sum_trend(
    chip: Optional[str] = None,
    province: Optional[str] = None,
    city: Optional[str] = None,
    site: Optional[str] = None,
    years: Optional[str] = None,
    months: Optional[str] = None,
):
    try:
        return CodeSumTrendResponse(**analytics.get_code_sum_trend(
            chip=chip, province=province, city=city, site=site, years=years, months=months,
        ))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
