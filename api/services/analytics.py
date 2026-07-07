import os
import sys
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from data_processor import DataProcessor

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

    _board_records = _processor.build_board_records(_current_df)
    filters = _processor.get_filter_options(_board_records)
    filters["folder_path"] = _last_folder
    filters.setdefault("site_names", [])
    # #region agent log
    try:
        import json as _json
        with open("/Users/xianbo/vulcanization/.cursor/debug-a5fec5.log", "a", encoding="utf-8") as _df:
            _df.write(_json.dumps({"sessionId": "a5fec5", "hypothesisId": "S1", "location": "analytics.py:analyze_folder", "message": "filters site_names", "data": {"site_names_count": len(filters.get("site_names", [])), "sample": filters.get("site_names", [])[:5]}, "timestamp": int(__import__("time").time() * 1000)}, ensure_ascii=False) + "\n")
    except OSError:
        pass
    # #endregion

    return {
        "total_boards": len(_board_records),
        "folder_path": _last_folder,
        "filters": filters,
    }


def get_filter_options(chip: Optional[str] = None) -> Dict[str, Any]:
    all_records = require_board_records()
    filtered = _filter_records(chips=chip)
    options = _processor.get_filter_options(filtered)
    all_options = _processor.get_filter_options(all_records)
    options["chips"] = all_options["chips"]
    options["years"] = all_options["years"]
    options["year_month_map"] = all_options["year_month_map"]
    options["site_names"] = all_options["site_names"]
    options["latest_year"] = all_options.get("latest_year")
    options["latest_month"] = all_options.get("latest_month")
    options["folder_path"] = _last_folder
    return options


def get_map_stats(
    chip: Optional[str] = None,
    province: Optional[str] = None,
    city: Optional[str] = None,
    site: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> Dict[str, Any]:
    if year is None or month is None:
        return _empty_map_stats()

    records = _filter_records(chips=chip, provinces=province, cities=city, site=site)
    records = _processor._filter_board_records(records, year=year, month=month)
    result = _processor.get_vulcanization_map_stats(
        records,
        provinces=_parse_list(province),
        cities=_parse_list(city),
    )
    result['display_year'] = year
    result['display_month'] = month
    # #region agent log
    try:
        import json as _json
        with open("/Users/xianbo/vulcanization/.cursor/debug-a5fec5.log", "a", encoding="utf-8") as _df:
            _df.write(_json.dumps({"sessionId": "a5fec5", "hypothesisId": "H1", "location": "analytics.py:get_map_stats", "message": "map stats ratios", "data": {"year": year, "month": month, "overall": result.get("overall"), "items": result.get("items", [])[:5], "record_count": len(records)}, "timestamp": int(__import__("time").time() * 1000)}, ensure_ascii=False) + "\n")
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
) -> List[Dict[str, Any]]:
    if year is None or month is None:
        return []

    records = _filter_records(chips=chip, provinces=province, cities=city, site=site)
    records = _processor._filter_board_records(records, year=year, month=month)
    return _processor.get_alerts(records)


def get_code_bar_chart(
    chip: Optional[str] = None,
    province: Optional[str] = None,
    city: Optional[str] = None,
    site: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> List[Dict[str, Any]]:
    if year is None or month is None:
        return []

    records = require_board_records()
    return _processor.get_code_distribution(
        records,
        chips=_parse_list(chip),
        provinces=_parse_list(province),
        cities=_parse_list(city),
        site_names=_parse_list(site),
        year=year,
        month=month,
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
        with open("/Users/xianbo/vulcanization/.cursor/debug-a5fec5.log", "a", encoding="utf-8") as _df:
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
