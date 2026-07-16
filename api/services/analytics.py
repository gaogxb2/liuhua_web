import os
import sys
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from data_processor import DataProcessor, AGENT_DEBUG_LOG_PATH, DEBUG_SESSION_LOG_PATH

DEFAULT_FOLDER = os.path.join(_ROOT, "logs")

_processor = DataProcessor()
_current_df = None
_board_records: List[Dict[str, Any]] = []
_last_folder = DEFAULT_FOLDER


def _parse_list(value: Optional[str]) -> Optional[List[str]]:
    if not value or not str(value).strip():
        return None
    items = [v.strip() for v in str(value).split(",") if v.strip()]
    return items or None


def _parse_int_list(value: Optional[str]) -> Optional[List[int]]:
    items = _parse_list(value)
    if not items:
        return None
    result = []
    for item in items:
        try:
            result.append(int(item))
        except (TypeError, ValueError):
            continue
    return result or None


def get_default_folder() -> str:
    return DEFAULT_FOLDER


def get_last_folder() -> str:
    return _last_folder


def require_board_records() -> List[Dict[str, Any]]:
    if not _board_records:
        raise ValueError("请先执行分析")
    return _board_records


def _filter_records(
    chips: Optional[str] = None,
    provinces: Optional[str] = None,
    cities: Optional[str] = None,
    site: Optional[str] = None,
) -> List[Dict[str, Any]]:
    records = require_board_records()
    return _processor._filter_board_records(
        records,
        chips=_parse_list(chips),
        provinces=_parse_list(provinces),
        cities=_parse_list(cities),
        site_names=_parse_list(site),
    )


def _empty_map_stats() -> Dict[str, Any]:
    return {
        'level': 'province',
        'items': [],
        'map_provinces': [],
        'display_year': None,
        'display_month': None,
        'display_months': [],
        'overall': {'ratio': 0.0, 'fault_count': 0, 'total_count': 0},
    }


def analyze_folder(folder_path: str, extract_zip: bool = False) -> Dict[str, Any]:
    global _current_df, _board_records, _last_folder

    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"目录不存在: {folder_path}")

    _last_folder = folder_path
    _current_df = _processor.analyze_folder(folder_path, extract_zip=extract_zip)
    if _current_df is None or _current_df.empty:
        _board_records = []
        raise ValueError("没有找到符合条件的文件")

    _board_records = _processor.build_board_records(_current_df, analyze_root=_last_folder)
    filters = _processor.get_filter_options(_board_records)
    filters["folder_path"] = _last_folder
    filters.setdefault("site_names", [])
    # #region agent log
    try:
        import json as _json
        with open(AGENT_DEBUG_LOG_PATH, "a", encoding="utf-8") as _df:
            _df.write(_json.dumps({"sessionId": "a5fec5", "hypothesisId": "S1", "location": "analytics.py:analyze_folder", "message": "filters site_names", "data": {"site_names_count": len(filters.get("site_names", [])), "sample": filters.get("site_names", [])[:5]}, "timestamp": int(__import__("time").time() * 1000)}, ensure_ascii=False) + "\n")
    except OSError:
        pass
    # #endregion

    return {
        "total_boards": len(_board_records),
        "folder_path": _last_folder,
        "filters": filters,
    }


def get_filter_options(
    chip: Optional[str] = None,
    province: Optional[str] = None,
    city: Optional[str] = None,
    site: Optional[str] = None,
    years: Optional[str] = None,
    months: Optional[str] = None,
) -> Dict[str, Any]:
    """按当前已选维度联动计算各下拉可选项（计算某一维时排除该维自身条件）。"""
    all_records = require_board_records()
    chips = _parse_list(chip)
    provinces = _parse_list(province)
    cities = _parse_list(city)
    sites = _parse_list(site)
    year_list = _parse_int_list(years)
    month_list = _parse_int_list(months)

    def _facet(*exclude: str) -> List[Dict[str, Any]]:
        kw: Dict[str, Any] = {}
        if "chips" not in exclude:
            kw["chips"] = chips
        if "provinces" not in exclude:
            kw["provinces"] = provinces
        if "cities" not in exclude:
            kw["cities"] = cities
        if "site_names" not in exclude:
            kw["site_names"] = sites
        if "years" not in exclude:
            kw["years"] = year_list
        if "months" not in exclude:
            kw["months"] = month_list
        return _processor._filter_board_records(all_records, **kw)

    chip_opts = _processor.get_filter_options(_facet("chips"))
    site_opts = _processor.get_filter_options(_facet("site_names"))
    province_opts = _processor.get_filter_options(_facet("provinces"))
    city_opts = _processor.get_filter_options(_facet("cities"))
    year_opts = _processor.get_filter_options(_facet("years"))
    month_opts = _processor.get_filter_options(_facet("months"))
    all_options = _processor.get_filter_options(all_records)

    options = {
        "chips": chip_opts["chips"],
        "site_names": site_opts["site_names"],
        "provinces": province_opts["provinces"],
        "city_map": city_opts["city_map"],
        "standalone_cities": city_opts["standalone_cities"],
        "years": year_opts["years"],
        "year_month_map": month_opts["year_month_map"],
        "latest_year": all_options.get("latest_year"),
        "latest_month": all_options.get("latest_month"),
        "folder_path": _last_folder,
    }
    # #region agent log
    try:
        import json as _json
        with open(DEBUG_SESSION_LOG_PATH, "a", encoding="utf-8") as _df:
            _df.write(_json.dumps({
                "sessionId": "c939a3",
                "runId": "post-fix",
                "hypothesisId": "H1-H2-H4",
                "location": "analytics.py:get_filter_options",
                "message": "cascading filter options computed",
                "data": {
                    "params": {
                        "chip": chip, "province": province, "city": city,
                        "site": site, "years": years, "months": months,
                    },
                    "all_record_count": len(all_records),
                    "returned_chips": len(options["chips"]),
                    "returned_sites": len(options["site_names"]),
                    "returned_provinces": options["provinces"],
                    "returned_years": options["years"],
                    "returned_year_month_map": options["year_month_map"],
                    "overwrote_from_all": False,
                },
                "timestamp": int(__import__("time").time() * 1000),
            }, ensure_ascii=False) + "\n")
    except OSError:
        pass
    # #endregion
    return options


def _resolve_month_list(
    month: Optional[int] = None,
    months: Optional[str] = None,
) -> Optional[List[int]]:
    month_list = _parse_int_list(months)
    if month_list:
        return month_list
    if month is not None:
        return [month]
    return None


def get_map_stats(
    chip: Optional[str] = None,
    province: Optional[str] = None,
    city: Optional[str] = None,
    site: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    months: Optional[str] = None,
) -> Dict[str, Any]:
    month_list = _resolve_month_list(month=month, months=months)
    if year is None or not month_list:
        return _empty_map_stats()

    records = _filter_records(chips=chip, provinces=province, cities=city, site=site)
    records = _processor._filter_board_records(records, year=year, months=month_list)
    raw_count = len(records)
    dedupe_by_sn = len(month_list) > 1
    result = _processor.get_vulcanization_map_stats(
        records,
        provinces=_parse_list(province),
        cities=_parse_list(city),
        dedupe_by_sn=dedupe_by_sn,
    )
    result['display_year'] = year
    result['display_month'] = month_list[0] if len(month_list) == 1 else None
    result['display_months'] = month_list
    # #region agent log
    try:
        import json as _json
        with open(AGENT_DEBUG_LOG_PATH, "a", encoding="utf-8") as _df:
            _df.write(_json.dumps({"sessionId": "a5fec5", "hypothesisId": "H1", "location": "analytics.py:get_map_stats", "message": "map stats ratios", "data": {"year": year, "month": month, "months": month_list, "overall": result.get("overall"), "items": result.get("items", [])[:5], "record_count": len(records)}, "timestamp": int(__import__("time").time() * 1000)}, ensure_ascii=False) + "\n")
        with open(DEBUG_SESSION_LOG_PATH, "a", encoding="utf-8") as _df:
            _df.write(_json.dumps({
                "sessionId": "c939a3",
                "runId": "post-fix",
                "hypothesisId": "H3-H4",
                "location": "analytics.py:get_map_stats",
                "message": "map multi-month sn dedupe",
                "data": {
                    "year": year,
                    "months": month_list,
                    "dedupe_by_sn": dedupe_by_sn,
                    "raw_record_count": raw_count,
                    "stat_record_count": result.get("overall", {}).get("total_count"),
                    "displayed_total_count": result.get("overall", {}).get("total_count"),
                    "displayed_fault_count": result.get("overall", {}).get("fault_count"),
                    "items": result.get("items", [])[:5],
                },
                "timestamp": int(__import__("time").time() * 1000),
            }, ensure_ascii=False) + "\n")
    except OSError:
        pass
    # #endregion
    return result


def get_alerts(
    chip: Optional[str] = None,
    province: Optional[str] = None,
    city: Optional[str] = None,
    site: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    months: Optional[str] = None,
) -> List[Dict[str, Any]]:
    month_list = _resolve_month_list(month=month, months=months)
    if year is None or not month_list:
        return []

    records = _filter_records(chips=chip, provinces=province, cities=city, site=site)
    records = _processor._filter_board_records(records, year=year, months=month_list)
    return _processor.get_alerts(records, dedupe_by_sn=len(month_list) > 1)


def get_code_bar_chart(
    chip: Optional[str] = None,
    province: Optional[str] = None,
    city: Optional[str] = None,
    site: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    months: Optional[str] = None,
) -> List[Dict[str, Any]]:
    month_list = _resolve_month_list(month=month, months=months)
    if year is None or not month_list:
        return []

    records = require_board_records()
    return _processor.get_code_distribution(
        records,
        chips=_parse_list(chip),
        provinces=_parse_list(province),
        cities=_parse_list(city),
        site_names=_parse_list(site),
        year=year,
        months=month_list,
        dedupe_by_sn=len(month_list) > 1,
    )


def get_code_sum_trend(
    chip: Optional[str] = None,
    province: Optional[str] = None,
    city: Optional[str] = None,
    site: Optional[str] = None,
    years: Optional[str] = None,
    months: Optional[str] = None,
) -> Dict[str, Any]:
    chips = _parse_list(chip)
    if not chips:
        return {'series': []}

    records = require_board_records()
    series = _processor.get_code_sum_trend(
        records,
        chips=chips,
        provinces=_parse_list(province),
        cities=_parse_list(city),
        site_names=_parse_list(site),
        years=_parse_int_list(years),
        months=_parse_int_list(months),
    )
    # #region agent log
    try:
        import json as _json
        with open(AGENT_DEBUG_LOG_PATH, "a", encoding="utf-8") as _df:
            _df.write(_json.dumps({"sessionId": "a5fec5", "hypothesisId": "T2", "location": "analytics.py:get_code_sum_trend", "message": "trend result", "data": {"chips": chips, "years": years, "months": months, "series_count": len(series), "points": [len(s.get("points", [])) for s in series]}, "timestamp": int(__import__("time").time() * 1000)}, ensure_ascii=False) + "\n")
    except OSError:
        pass
    # #endregion
    return {'series': series}


def export_excel() -> str:
    if _current_df is None or _current_df.empty:
        raise ValueError("没有可导出的数据，请先执行分析")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(tempfile.gettempdir(), f"分析结果_{timestamp}.xlsx")
    _processor.save_to_excel(_current_df.copy(), output_path)
    return output_path
