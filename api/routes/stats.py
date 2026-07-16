from typing import Optional

from fastapi import APIRouter, HTTPException

from api.schemas import AlertItem, FilterOptionsResponse, MapStatsResponse
from api.services import analytics

router = APIRouter(prefix="/api", tags=["stats"])


def _handle_service_error(exc: Exception):
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    raise exc


@router.get("/chips")
def get_chips(
    chip: Optional[str] = None,
    province: Optional[str] = None,
    city: Optional[str] = None,
    site: Optional[str] = None,
    years: Optional[str] = None,
    months: Optional[str] = None,
):
    try:
        options = analytics.get_filter_options(
            chip=chip, province=province, city=city, site=site, years=years, months=months,
        )
        return {"chips": options["chips"]}
    except ValueError as exc:
        _handle_service_error(exc)


@router.get("/filters", response_model=FilterOptionsResponse)
def get_filters(
    chip: Optional[str] = None,
    province: Optional[str] = None,
    city: Optional[str] = None,
    site: Optional[str] = None,
    years: Optional[str] = None,
    months: Optional[str] = None,
):
    try:
        return FilterOptionsResponse(**analytics.get_filter_options(
            chip=chip, province=province, city=city, site=site, years=years, months=months,
        ))
    except ValueError as exc:
        _handle_service_error(exc)


@router.get("/map", response_model=MapStatsResponse)
def get_map(
    chip: Optional[str] = None,
    province: Optional[str] = None,
    city: Optional[str] = None,
    site: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    months: Optional[str] = None,
):
    try:
        return MapStatsResponse(**analytics.get_map_stats(
            chip=chip, province=province, city=city, site=site,
            year=year, month=month, months=months,
        ))
    except ValueError as exc:
        _handle_service_error(exc)


@router.get("/alerts", response_model=list[AlertItem])
def get_alerts(
    chip: Optional[str] = None,
    province: Optional[str] = None,
    city: Optional[str] = None,
    site: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    months: Optional[str] = None,
):
    try:
        return analytics.get_alerts(
            chip=chip, province=province, city=city, site=site,
            year=year, month=month, months=months,
        )
    except ValueError as exc:
        _handle_service_error(exc)
