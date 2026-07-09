import json
import json
import os
import sys
import zipfile
import shutil
import pandas as pd
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Set


from geo_city_data import GEOJSON_CITY_NAMES, GEOJSON_CITY_ALIASES, _GEO_CITY_MATCH_ORDER

# 调试日志写在项目根目录，便于跨机器查看
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
AGENT_DEBUG_LOG_PATH = os.path.join(_PROJECT_ROOT, "debug.log")


# 中国省级行政区名称集合（含简称与全称，用于文件夹名子串匹配）
CHINA_PROVINCES: Set[str] = {
    '北京市', '天津市', '上海市', '重庆市',
    '河北省', '山西省', '辽宁省', '吉林省', '黑龙江省',
    '江苏省', '浙江省', '安徽省', '福建省', '江西省', '山东省',
    '河南省', '湖北省', '湖南省', '广东省', '海南省',
    '四川省', '贵州省', '云南省', '陕西省', '甘肃省', '青海省', '台湾省',
    '内蒙古自治区', '广西壮族自治区', '西藏自治区', '宁夏回族自治区', '新疆维吾尔自治区',
    '香港特别行政区', '澳门特别行政区',
    '北京', '天津', '上海', '重庆',
    '河北', '山西', '辽宁', '吉林', '黑龙江',
    '江苏', '浙江', '安徽', '福建', '江西', '山东',
    '河南', '湖北', '湖南', '广东', '海南',
    '四川', '贵州', '云南', '陕西', '甘肃', '青海', '台湾',
    '内蒙古', '广西', '西藏', '宁夏', '新疆', '香港', '澳门',
}

# 中国地级行政区名称集合（地级市、自治州、盟、地区等）
CHINA_CITIES: Set[str] = {
    '北京市', '天津市', '上海市', '重庆市',
    '石家庄市', '唐山市', '秦皇岛市', '邯郸市', '邢台市', '保定市', '张家口市', '承德市', '沧州市', '廊坊市', '衡水市',
    '太原市', '大同市', '阳泉市', '长治市', '晋城市', '朔州市', '晋中市', '运城市', '忻州市', '临汾市', '吕梁市',
    '呼和浩特市', '包头市', '乌海市', '赤峰市', '通辽市', '鄂尔多斯市', '呼伦贝尔市', '巴彦淖尔市', '乌兰察布市',
    '沈阳市', '大连市', '鞍山市', '抚顺市', '本溪市', '丹东市', '锦州市', '营口市', '阜新市', '辽阳市', '盘锦市', '铁岭市', '朝阳市', '葫芦岛市',
    '长春市', '吉林市', '四平市', '辽源市', '通化市', '白山市', '松原市', '白城市',
    '哈尔滨市', '齐齐哈尔市', '鸡西市', '鹤岗市', '双鸭山市', '大庆市', '伊春市', '佳木斯市', '七台河市', '牡丹江市', '黑河市', '绥化市',
    '南京市', '无锡市', '徐州市', '常州市', '苏州市', '南通市', '连云港市', '淮安市', '盐城市', '扬州市', '镇江市', '泰州市', '宿迁市',
    '杭州市', '宁波市', '温州市', '嘉兴市', '湖州市', '绍兴市', '金华市', '衢州市', '舟山市', '台州市', '丽水市',
    '合肥市', '芜湖市', '蚌埠市', '淮南市', '马鞍山市', '淮北市', '铜陵市', '安庆市', '黄山市', '滁州市', '阜阳市', '宿州市', '六安市', '亳州市', '池州市', '宣城市',
    '福州市', '厦门市', '莆田市', '三明市', '泉州市', '漳州市', '南平市', '龙岩市', '宁德市',
    '南昌市', '景德镇市', '萍乡市', '九江市', '新余市', '鹰潭市', '赣州市', '吉安市', '宜春市', '抚州市', '上饶市',
    '济南市', '青岛市', '淄博市', '枣庄市', '东营市', '烟台市', '潍坊市', '济宁市', '泰安市', '威海市', '日照市', '临沂市', '德州市', '聊城市', '滨州市', '菏泽市',
    '郑州市', '开封市', '洛阳市', '平顶山市', '安阳市', '鹤壁市', '新乡市', '焦作市', '濮阳市', '许昌市', '漯河市', '三门峡市', '南阳市', '商丘市', '信阳市', '周口市', '驻马店市',
    '武汉市', '黄石市', '十堰市', '宜昌市', '襄阳市', '鄂州市', '荆门市', '孝感市', '荆州市', '黄冈市', '咸宁市', '随州市',
    '长沙市', '株洲市', '湘潭市', '衡阳市', '邵阳市', '岳阳市', '常德市', '张家界市', '益阳市', '郴州市', '永州市', '怀化市', '娄底市',
    '广州市', '韶关市', '深圳市', '珠海市', '汕头市', '佛山市', '江门市', '湛江市', '茂名市', '肇庆市', '惠州市', '梅州市', '汕尾市', '河源市', '阳江市', '清远市', '东莞市', '中山市', '潮州市', '揭阳市', '云浮市',
    '南宁市', '柳州市', '桂林市', '梧州市', '北海市', '防城港市', '钦州市', '贵港市', '玉林市', '百色市', '贺州市', '河池市', '来宾市', '崇左市',
    '海口市', '三亚市', '三沙市', '儋州市',
    '成都市', '自贡市', '攀枝花市', '泸州市', '德阳市', '绵阳市', '广元市', '遂宁市', '内江市', '乐山市', '南充市', '眉山市', '宜宾市', '广安市', '达州市', '雅安市', '巴中市', '资阳市',
    '贵阳市', '六盘水市', '遵义市', '安顺市', '毕节市', '铜仁市',
    '昆明市', '曲靖市', '玉溪市', '保山市', '昭通市', '丽江市', '普洱市', '临沧市',
    '拉萨市', '日喀则市', '昌都市', '林芝市', '山南市', '那曲市',
    '西安市', '铜川市', '宝鸡市', '咸阳市', '渭南市', '延安市', '汉中市', '榆林市', '安康市', '商洛市',
    '兰州市', '嘉峪关市', '金昌市', '白银市', '天水市', '武威市', '张掖市', '平凉市', '酒泉市', '庆阳市', '定西市', '陇南市',
    '西宁市', '海东市',
    '银川市', '石嘴山市', '吴忠市', '固原市', '中卫市',
    '乌鲁木齐市', '克拉玛依市', '吐鲁番市', '哈密市',
    '台北市', '高雄市', '台中市', '台南市',
    '香港', '澳门',
}

MUNICIPALITY_KEYWORDS: Dict[str, str] = {
    '北京': '北京市',
    '天津': '天津市',
    '上海': '上海市',
    '重庆': '重庆市',
}

# GeoJSON 省级标准名称（与 DataV 地图一致）
GEOJSON_PROVINCE_NAMES: Set[str] = {
    '北京市', '天津市', '河北省', '山西省', '内蒙古自治区', '辽宁省', '吉林省', '黑龙江省',
    '上海市', '江苏省', '浙江省', '安徽省', '福建省', '江西省', '山东省', '河南省',
    '湖北省', '湖南省', '广东省', '广西壮族自治区', '海南省', '重庆市', '四川省',
    '贵州省', '云南省', '西藏自治区', '陕西省', '甘肃省', '青海省', '宁夏回族自治区',
    '新疆维吾尔自治区', '台湾省', '香港特别行政区', '澳门特别行政区',
}

# 匹配时优先较长名称
_PROVINCE_MATCH_ORDER = sorted(CHINA_PROVINCES, key=len, reverse=True)
_CITY_MATCH_ORDER = sorted(CHINA_CITIES, key=len, reverse=True)


class DataProcessor:
    def __init__(self, config_path: str = None):
        """
        初始化数据处理器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        if config_path is None:
            # 默认配置文件路径（与data_processor.py同目录）
            # 支持 PyInstaller 打包后的路径
            if getattr(sys, 'frozen', False):
                # 如果是打包后的exe，使用sys._MEIPASS获取临时目录
                base_path = sys._MEIPASS
            else:
                # 如果是普通运行，使用__file__所在目录
                base_path = os.path.dirname(__file__)
            config_path = os.path.join(base_path, "vulcanization", "config.json")
            # 如果上面的路径不存在，尝试直接在同目录查找
            if not os.path.exists(config_path):
                config_path = os.path.join(base_path, "config.json")
        
        self.config_path = config_path
        self.config = self.load_config()
        # 用于缓存文件内容和匹配结果，避免重复读取和匹配
        self._file_cache = {}
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            # 如果配置文件不存在，返回默认配置
            return {"path_keywords": []}
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}")
    
    def _normalize_province_name(self, name: str) -> str:
        if not name:
            return ""
        name = name.strip()
        if name.endswith(('省', '市', '自治区', '特别行政区')):
            return name
        aliases = {
            '内蒙古': '内蒙古自治区',
            '广西': '广西壮族自治区',
            '西藏': '西藏自治区',
            '宁夏': '宁夏回族自治区',
            '新疆': '新疆维吾尔自治区',
        }
        if name in aliases:
            return aliases[name]
        return f"{name}省"

    def _normalize_city_name(self, name: str) -> str:
        if not name:
            return ""
        name = name.strip()
        if name.endswith('市') or name in ('北京市', '上海市', '天津市', '重庆市'):
            return name
        return f"{name}市"

    def _to_geo_province_name(self, name: str) -> str:
        """将识别到的省份名规范为 GeoJSON 区域名；无法识别则保留原文件夹名。"""
        if not name:
            return ""
        name = name.strip()
        if name in GEOJSON_PROVINCE_NAMES:
            return name
        if name in CHINA_PROVINCES:
            return self._normalize_province_name(name)
        return name

    def _match_geo_city_name(self, text: str) -> str:
        """将文件夹名/城市名匹配为 DataV GeoJSON 地级标准名称。"""
        if not text:
            return ""
        text = text.strip()
        if text in GEOJSON_CITY_NAMES:
            return text
        if text in GEOJSON_CITY_ALIASES:
            return GEOJSON_CITY_ALIASES[text]
        for name in _GEO_CITY_MATCH_ORDER:
            if name in text:
                return name
        for name in _GEO_CITY_MATCH_ORDER:
            if name.endswith('市'):
                base = name[:-1]
                if len(base) >= 2 and text.startswith(base):
                    return name
        for suffix, strip_len in (('地区', 2), ('盟', 1), ('自治州', 3)):
            for name in _GEO_CITY_MATCH_ORDER:
                if name.endswith(suffix):
                    base = name[:-strip_len]
                    if len(base) >= 2 and (text.startswith(base) or base in text):
                        return name
        for alias, full in sorted(GEOJSON_CITY_ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
            if alias != full and alias in text and full in GEOJSON_CITY_NAMES:
                return full
        if not text.endswith('市'):
            with_suffix = text + '市'
            if with_suffix in GEOJSON_CITY_NAMES:
                return with_suffix
            if with_suffix in GEOJSON_CITY_ALIASES:
                return GEOJSON_CITY_ALIASES[with_suffix]
        return ""

    def _to_geo_city_name(self, name: str) -> str:
        """将识别到的城市名规范为 GeoJSON 区域名；无法识别则保留原文件夹名。"""
        if not name:
            return ""
        matched = self._match_geo_city_name(name.strip())
        result = matched if matched else name.strip()
        # #region agent log
        if name.strip() and name.strip() != result:
            try:
                with open(AGENT_DEBUG_LOG_PATH, "a", encoding="utf-8") as _df:
                    _df.write(json.dumps({
                        "sessionId": "1d1172",
                        "runId": "geo-cities",
                        "hypothesisId": "H1",
                        "location": "data_processor.py:_to_geo_city_name",
                        "message": "city normalized to geojson",
                        "data": {"input": name, "output": result, "in_geojson": result in GEOJSON_CITY_NAMES},
                        "timestamp": int(__import__("time").time() * 1000),
                    }, ensure_ascii=False) + "\n")
            except OSError:
                pass
        # #endregion
        return result

    def _match_longest_in_set(self, text: str, ordered_names: List[str]) -> str:
        """在 text 中查找最长匹配的行政区划名称（相连子串）。"""
        if not text:
            return ""
        for name in ordered_names:
            if name in text:
                return name
        return ""

    def _match_city_from_folder(self, text: str) -> str:
        """在文件夹名中匹配城市，返回 GeoJSON 地级标准名称。"""
        if not text:
            return ""
        matched = self._match_geo_city_name(text)
        if matched:
            return matched
        matched = self._match_longest_in_set(text, _CITY_MATCH_ORDER)
        if matched:
            return matched
        for name in _CITY_MATCH_ORDER:
            if name.endswith('市'):
                base = name[:-1]
                if len(base) >= 2 and text.startswith(base):
                    return name
        if not text.endswith('市'):
            matched = self._match_longest_in_set(text + '市', _CITY_MATCH_ORDER)
            if matched:
                return matched
        return ""

    def _extract_municipality_city(self, text: str) -> str:
        """若文件夹名含直辖市关键词，返回标准市名。"""
        if not text:
            return ""
        for keyword, full_name in MUNICIPALITY_KEYWORDS.items():
            if keyword in text:
                return full_name
        return ""

    def _parse_location_from_path(self, relative_path: str, filename: str = "") -> Tuple[str, str]:
        """从分析目录相对路径的下两级/下三级文件夹名解析省、市。

        - 下两级文件夹名（parts[1]）：匹配省集合；无匹配则用整个文件夹名
        - 下三级文件夹名（parts[2]）：匹配市集合；无匹配则用整个文件夹名
        - 下两级或三级含直辖市关键词：省、市均设为直辖市标准名（同时进入省份与城市筛选项）
        """
        parts = [p for p in Path(relative_path).parts if p and p != '.']
        if parts and '.' in parts[-1]:
            folder_parts = parts[:-1]
        else:
            folder_parts = parts

        level2 = folder_parts[1] if len(folder_parts) > 1 else ""
        level3 = folder_parts[2] if len(folder_parts) > 2 else ""

        province = ""
        city = ""
        province_match_type = ""
        city_match_type = ""
        matched_province_raw = ""
        matched_city_raw = ""
        unmatched_province_folder = ""
        unmatched_city_folder = ""

        muni_l2 = self._extract_municipality_city(level2)
        muni_l3 = self._extract_municipality_city(level3)

        if muni_l2:
            province = muni_l2
            city = muni_l2
            province_match_type = "municipality_l2"
            city_match_type = "municipality_l2"
            matched_province_raw = muni_l2
            matched_city_raw = muni_l2
        else:
            if level2:
                matched_province = self._match_longest_in_set(level2, _PROVINCE_MATCH_ORDER)
                if matched_province:
                    province = matched_province
                    province_match_type = "province_set"
                    matched_province_raw = matched_province
                else:
                    province = level2
                    province_match_type = "fallback_whole_folder"
                    unmatched_province_folder = level2

        if muni_l3:
            city = muni_l3
            city_match_type = "municipality_l3"
            matched_city_raw = muni_l3
            if muni_l2:
                pass
            else:
                province = muni_l3
                province_match_type = "municipality_l3"
                matched_province_raw = muni_l3
        elif level3:
            matched_city = self._match_city_from_folder(level3)
            if matched_city:
                city = matched_city
                city_match_type = "city_geo_match"
                matched_city_raw = matched_city
            else:
                city = level3
                city_match_type = "fallback_whole_folder"
                unmatched_city_folder = level3

        province_before_geo = province
        city_before_geo = city
        province = self._to_geo_province_name(province)
        city = self._to_geo_city_name(city)

        # #region agent log
        try:
            with open(AGENT_DEBUG_LOG_PATH, "a", encoding="utf-8") as _df:
                _df.write(json.dumps({
                    "sessionId": "1d1172",
                    "runId": "path-parse",
                    "hypothesisId": "LOC",
                    "location": "data_processor.py:_parse_location_from_path",
                    "message": "省市区路径解析",
                    "data": {
                        "relative_path": relative_path,
                        "level2_folder": level2,
                        "level3_folder": level3,
                        "province_match_type": province_match_type,
                        "city_match_type": city_match_type,
                        "matched_province_raw": matched_province_raw,
                        "matched_city_raw": matched_city_raw,
                        "unmatched_province_folder": unmatched_province_folder,
                        "unmatched_city_folder": unmatched_city_folder,
                        "province_before_geo": province_before_geo,
                        "city_before_geo": city_before_geo,
                        "province_final": province,
                        "city_final": city,
                    },
                    "timestamp": int(__import__("time").time() * 1000),
                }, ensure_ascii=False) + "\n")
        except OSError:
            pass
        # #endregion

        if province or city:
            return province, city

        if filename:
            return self._parse_location_from_filename(filename)
        return "", ""

    def _parse_location_from_filename(self, filename: str) -> Tuple[str, str]:
        """从文件名解析发货省份和城市。

        支持格式：
        - xxx省_xxx市_工程师报告xx.txt
        - xxx代表处_xxx市_运营商_工程师报告xx.txt
        """
        province, city = "", ""
        pattern_used = "none"

        delegate_match = re.match(r'^(.+?)代表处_([^_]+市)_[^_]+_工程师报告', filename)
        if delegate_match:
            region = delegate_match.group(1)
            city = delegate_match.group(2)
            if region.endswith(('省', '市', '自治区')):
                province = region
            elif region in ('内蒙古', '广西', '西藏', '宁夏', '新疆'):
                province = f"{region}自治区"
            else:
                province = f"{region}省"
            pattern_used = "delegate_office"
        else:
            legacy_match = re.match(r'^([^_]+)_([^_]+)_工程师报告', filename)
            if legacy_match:
                province, city = legacy_match.group(1), legacy_match.group(2)
                pattern_used = "legacy_two_part"

        province = self._to_geo_province_name(province)
        city = self._to_geo_city_name(city)
        return province, city
    
    def get_location_stats(
        self,
        df: pd.DataFrame,
        province: Optional[str] = None,
        city: Optional[str] = None,
    ) -> Dict[str, Any]:
        """按文件名去重后统计各省市的报告文件数量"""
        empty_result = {
            "total_files": 0,
            "by_province": {},
            "by_city": {},
            "city_map": {},
            "provinces": [],
            "cities": [],
            "records": [],
        }
        if df.empty or '文件名' not in df.columns:
            return empty_result
        
        work = df.copy()
        if '省份' not in work.columns:
            def resolve_location(row):
                path = str(row.get('文件路径', '') or '')
                filename = str(row.get('文件名', '') or '')
                if path:
                    return self._parse_location_from_path(path, filename)
                return self._parse_location_from_filename(filename)

            locations = work.apply(resolve_location, axis=1)
            work['省份'] = locations.apply(lambda x: x[0])
            work['城市'] = locations.apply(lambda x: x[1])
        
        file_df = work.drop_duplicates(subset=['文件名'], keep='first')
        
        city_map: Dict[str, List[str]] = {}
        for _, row in file_df.iterrows():
            p, c = row.get('省份', ''), row.get('城市', '')
            if p and c:
                city_map.setdefault(p, [])
                if c not in city_map[p]:
                    city_map[p].append(c)
        for p in city_map:
            city_map[p] = sorted(city_map[p])
        
        filtered = file_df
        if province:
            filtered = filtered[filtered['省份'] == province]
        if city:
            filtered = filtered[filtered['城市'] == city]
        
        by_province: Dict[str, int] = {}
        for p, count in filtered.groupby('省份').size().items():
            if p:
                by_province[str(p)] = int(count)
        
        by_city: Dict[str, int] = {}
        for _, row in filtered.iterrows():
            p, c = row.get('省份', ''), row.get('城市', '')
            if c:
                key = f"{p}|{c}" if p else c
                by_city[key] = by_city.get(key, 0) + 1
        
        display_columns = [
            '文件名', '省份', '城市', '匹配值', '版本号', '时间', '温度', '条码1', '条码2', '条码3'
        ]
        existing_columns = [col for col in display_columns if col in filtered.columns]
        records = filtered[existing_columns].fillna("").to_dict(orient='records')
        
        return {
            "total_files": len(filtered),
            "by_province": by_province,
            "by_city": by_city,
            "city_map": city_map,
            "provinces": sorted([p for p in file_df['省份'].unique() if p]),
            "cities": sorted([c for c in filtered['城市'].unique() if c]),
            "records": records,
        }
    
    def _check_path_keywords_match(self, file_path: str) -> bool:
        """
        检查文件路径是否匹配到配置的关键词
        
        Args:
            file_path: 文件路径（相对路径或绝对路径）
            
        Returns:
            True表示匹配到关键词，False表示未匹配
        """
        path_keywords_config = self.config.get("path_keywords", {})
        
        # 检查路径关键词（只检查use_for_filter为true的关键词）
        # 支持两种格式：对象格式 {"keyword": [...], "use_for_filter": true} 和字符串数组（向后兼容）
        filter_keywords = []
        if isinstance(path_keywords_config, dict):
            # 对象格式：{"keyword": [...], "use_for_filter": true/false}
            if path_keywords_config.get("use_for_filter", False):
                keywords = path_keywords_config.get("keyword", [])
                if isinstance(keywords, list):
                    filter_keywords = [k for k in keywords if isinstance(k, str)]
        elif isinstance(path_keywords_config, list):
            # 字符串数组格式（向后兼容）：默认use_for_filter为true
            filter_keywords = [k for k in path_keywords_config if isinstance(k, str)]
        
        # 如果没有配置关键词，认为匹配（不删除）
        if not filter_keywords:
            return True
        
        # 检查路径中是否包含所有用于过滤的关键词
        file_path_lower = file_path.lower()
        for keyword in filter_keywords:
            if keyword and keyword.lower() not in file_path_lower:
                return False
        
        return True
    
    def should_analyze(self, file_path: str, file_item: Path = None) -> bool:
        """
        判断文件路径是否应该被分析
        只有当路径包含所有配置的关键词时才会被分析
        如果配置了用于过滤的匹配项，还需要检查文件内容是否匹配
        
        Args:
            file_path: 文件路径（相对路径或绝对路径）
            file_item: 文件Path对象，用于读取文件内容（可选）
            
        Returns:
            True表示应该分析，False表示跳过
        """
        # 检查路径关键词匹配
        if not self._check_path_keywords_match(file_path):
            return False
        
        # 检查用于过滤的匹配项
        extract_patterns = self.config.get("extract_patterns", [])
        filter_patterns = [p for p in extract_patterns if p.get("use_for_filter", False)]
        
        if filter_patterns and file_item and file_item.is_file():
            # 读取文件内容（使用缓存）
            content = self._read_file_content(file_item)
            if not content:
                # 如果无法读取文件，跳过
                return False
            
            # 检查每个用于过滤的匹配项
            for pattern_config in filter_patterns:
                found, matches = self._match_pattern(content, pattern_config)
                if not found or not matches:
                    # 没找到起始/结束字段，或者正则表达式没有匹配到任何内容，不分析
                    return False
        
        return True
    
    def _read_file_content(self, file_path: Path) -> str:
        """
        读取文件内容，使用缓存避免重复读取
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容字符串，如果读取失败返回空字符串
        """
        file_key = str(file_path)
        if file_key not in self._file_cache:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    self._file_cache[file_key] = f.read()
            except Exception:
                self._file_cache[file_key] = ""
        return self._file_cache[file_key]
    
    def _match_pattern(self, content: str, pattern_config: Dict[str, Any]) -> tuple:
        """
        对单个匹配项进行匹配
        
        Args:
            content: 文件内容
            pattern_config: 匹配项配置
            
        Returns:
            (是否找到起始和结束字段, 匹配到的结果列表)
        """
        start_field = pattern_config.get("start_field", "")
        end_field = pattern_config.get("end_field", "")
        regex_pattern = pattern_config.get("regex", "")
        
        if not start_field or not end_field or not regex_pattern:
            return (False, [])
        
        # 查找第一个起始字段和第一个结束字段之间的内容
        start_idx = content.find(start_field)
        if start_idx == -1:
            return (False, [])
        
        # 从起始字段之后开始查找结束字段
        search_start = start_idx + len(start_field)
        end_idx = content.find(end_field, search_start)
        if end_idx == -1:
            return (False, [])
        
        # 提取起始字段和结束字段之间的内容
        extracted_content = content[search_start:end_idx]
        
        # 使用正则表达式提取匹配的数字
        matches = re.findall(regex_pattern, extracted_content)
        # re.findall返回的是捕获组的内容列表（如果只有一个捕获组，返回字符串列表）
        # 如果正则表达式有多个捕获组，返回元组列表；如果只有一个捕获组，返回字符串列表
        if matches and isinstance(matches[0], tuple):
            numbers = [str(match[0]) for match in matches]
        else:
            numbers = [str(match) for match in matches]
        print("numbers:",numbers)
        return (True, numbers)
    
    def _match_secondary_pattern(self, content: str, number: str, secondary_config: Dict[str, Any]) -> List[str]:
        """
        对每个数字进行二次匹配
        
        Args:
            content: 文件内容
            number: 要匹配的数字
            secondary_config: 二次匹配配置，包含start_field, end_field, regex
            
        Returns:
            匹配到的结果列表
        """
        if not secondary_config:
            return []
        
        start_field = secondary_config.get("start_field", "")
        end_field = secondary_config.get("end_field", "")
        regex_template = secondary_config.get("regex", "")
        
        if not start_field or not end_field or not regex_template:
            return []
        
        # 替换 start_field 和 end_field 中的 {number} 占位符
        start_field = start_field.replace("{number}", number)
        end_field = end_field.replace("{number}", number)
        
        # 找到段落
        print("start_field:",start_field)
        start_idx = content.find(start_field)
        print("start_idx:",start_idx)
        if start_idx == -1:
            return []
        
        # 从起始字段之后开始查找结束字段
        search_start = start_idx + len(start_field)
        print("search_start:",search_start)
        end_idx = content.find(end_field, search_start)
        print("end_idx:",end_idx)
        if end_idx == -1:
            return []
        
        # 提取段落内容
        paragraph_content = content[search_start:end_idx]
        
        # 将正则表达式模板中的 {number} 替换为实际数字（转义）
        regex_pattern = regex_template.replace("{number}", re.escape(number))
        print("regex_pattern:", regex_pattern)
        print("paragraph_content length:", len(paragraph_content))
        # 检查是否需要使用 DOTALL 标志（如果正则表达式中包含 .* 等需要匹配换行符的模式）
        use_dotall = secondary_config.get("use_dotall", False)
        if not use_dotall and ('.*' in regex_template or '.+?' in regex_template):
            use_dotall = True
        
        # 执行匹配
        if use_dotall:
            matches = re.findall(regex_pattern, paragraph_content, re.DOTALL)
        else:
            matches = re.findall(regex_pattern, paragraph_content)
        print("total matches found:", len(matches))

        # 返回匹配到的结果，如果没有匹配到则返回空列表
        if not matches:
            print("no matches")
            return []
        print("matches:",matches)
        
        # 检查是否只匹配第一个结果
        match_all = secondary_config.get("match_all", False)  # 默认只匹配第一个
        print("match_all setting:", match_all)
        
        # 处理多个捕获组的情况
        if isinstance(matches[0], tuple):
            # 如果有多个捕获组，将所有捕获组用空格连接
            results = [' '.join(str(m) for m in match) for match in matches]
        else:
            # 如果只有一个捕获组，直接返回
            results = [str(match) for match in matches]
        
        # 如果 match_all 为 False，只返回第一个结果
        if not match_all and results:
            return [results[0]]
        
        return results
    
    def _match_secondary_pattern_detailed(self, content: str, number: str, secondary_config: Dict[str, Any]) -> List[List[str]]:
        """
        对每个数字进行二次匹配，返回详细的匹配结果（保留多个捕获组）
        
        Args:
            content: 文件内容
            number: 要匹配的数字
            secondary_config: 二次匹配配置，包含start_field, end_field, regex
            
        Returns:
            匹配到的结果列表，每个结果是一个列表（多个捕获组）或字符串（单个捕获组）
        """
        if not secondary_config:
            return []
        
        start_field = secondary_config.get("start_field", "")
        end_field = secondary_config.get("end_field", "")
        regex_template = secondary_config.get("regex", "")
        
        if not start_field or not end_field or not regex_template:
            return []
        
        # 检查是否只替换 regex 中的 {number}（不替换 start_field 中的）
        only_replace_in_regex = secondary_config.get("only_replace_in_regex", False)
        
        # 替换 start_field 和 end_field 中的 {number} 占位符（除非配置了 only_replace_in_regex）
        if not only_replace_in_regex:
            start_field = start_field.replace("{number}", number)
            end_field = end_field.replace("{number}", number)
        
        # 找到段落
        start_idx = content.find(start_field)
        if start_idx == -1:
            return []
        
        # 从起始字段之后开始查找结束字段
        search_start = start_idx + len(start_field)
        end_idx = content.find(end_field, search_start)
        if end_idx == -1:
            return []
        
        # 提取段落内容
        paragraph_content = content[search_start:end_idx]
        
        # 将正则表达式模板中的 {number} 替换为实际数字（转义）
        regex_pattern = regex_template.replace("{number}", re.escape(number))
        
        # 检查是否需要使用 DOTALL 标志
        use_dotall = secondary_config.get("use_dotall", False)
        if not use_dotall and ('.*' in regex_template or '.+?' in regex_template):
            use_dotall = True
        
        # 执行匹配
        if use_dotall:
            matches = re.findall(regex_pattern, paragraph_content, re.DOTALL)
        else:
            matches = re.findall(regex_pattern, paragraph_content)
        
        if not matches:
            return []
        
        # 检查是否只匹配第一个结果
        match_all = secondary_config.get("match_all", False)
        
        # 处理多个捕获组的情况，保留原始结构
        if isinstance(matches[0], tuple):
            # 如果有多个捕获组，返回元组列表转换为列表列表
            results = [[str(m) for m in match] for match in matches]
        else:
            # 如果只有一个捕获组，每个结果包装成列表
            results = [[str(match)] for match in matches]
        
        # 如果 match_all 为 False，只返回第一个结果
        if not match_all and results:
            return [results[0]]
        
        return results
    
    def _format_fourth_match(self, fourth_match: List[str]) -> str:
        """
        格式化fourth_match的结果
        输入格式1（match_all=False）：["macroX,dsY", "0xZ"]
        输入格式2（match_all=True）：["macroX,dsY 0xZ | macroX2,dsY2 0xZ2 | ..."]
        输出格式：f"macroX laneY 0xP"，其中0xP是0xZ的bit0-5的值
        如果有多个匹配，用 " | " 连接
        
        Args:
            fourth_match: fourth_match的匹配结果列表
            
        Returns:
            格式化后的字符串
        """
        if not fourth_match:
            return ""
        
        # 如果只有一个元素且包含 " | "，说明是match_all=True的情况
        if len(fourth_match) == 1 and " | " in fourth_match[0]:
            # 分割多个匹配
            matches_str = fourth_match[0].split(" | ")
            formatted_matches = []
            for match_str in matches_str:
                # 每个匹配格式：macroX,dsY 0xZ
                parts = match_str.strip().split()
                if len(parts) >= 2:
                    macro_ds = parts[0]  # macroX,dsY
                    hex_str = parts[1]   # 0xZ
                    formatted = self._format_single_fourth_match(macro_ds, hex_str)
                    if formatted:
                        formatted_matches.append(formatted)
            return " | ".join(formatted_matches) if formatted_matches else ""
        
        # 如果是两个元素，说明是match_all=False的情况
        if len(fourth_match) >= 2:
            macro_ds = fourth_match[0]  # macroX,dsY
            hex_str = fourth_match[1]   # 0xZ
            return self._format_single_fourth_match(macro_ds, hex_str) or " ".join(fourth_match)
        
        return " ".join(fourth_match)
    
    def _parse_code_macro_lane(self, code: str) -> Dict[str, str]:
        """
        解析code值，提取所有 macro X lane Y 0xZ 格式的内容
        
        Args:
            code: code值字符串，可能包含多个用 | 分隔的项
            
        Returns:
            字典，键为 "macro X lane Y"，值为 "0xZ"
        """
        result = {}
        if not code:
            return result
        
        # 正则表达式匹配 "macro X lane Y 0xZ" 格式
        # 支持格式：
        # - macro 1 lane 1 0x11 (有空格)
        # - macro1 lane1 0x11 (macro和数字之间无空格，lane和数字之间无空格)
        # - macro1lane1 0x11 (macro和数字之间无空格，lane和数字之间无空格，macro和lane之间也无空格)
        # - macro1 lane 1 0x11 (macro和数字之间无空格，lane和数字之间有空格)
        # - macro 1lane1 0x11 (macro和数字之间有空格，lane和数字之间无空格)
        # 使用 \s* 允许0个或多个空白字符，确保完全支持无空格格式
        pattern = r'macro\s*(\d+)\s*lane\s*(\d+)\s+(0x[0-9A-Fa-f]+)'
        matches = re.findall(pattern, code)
        
        for match in matches:
            macro_num = match[0]
            lane_num = match[1]
            hex_value = match[2]
            column_name = f"macro {macro_num} lane {lane_num}"
            result[column_name] = hex_value
        
        return result
    
    def _add_dynamic_macro_lane_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        根据code列的值，动态添加 macro X lane Y 列
        
        Args:
            df: 原始DataFrame
            
        Returns:
            添加了动态列的DataFrame
        """
        if df.empty or 'code' not in df.columns:
            return df
        
        # 收集所有唯一的 macro X lane Y 组合
        all_macro_lane_columns = set()
        row_macro_lane_data = []
        
        for idx, row in df.iterrows():
            code_value = str(row.get('code', ''))
            parsed = self._parse_code_macro_lane(code_value)
            all_macro_lane_columns.update(parsed.keys())
            row_macro_lane_data.append(parsed)
        
        # 按macro和lane的数字排序（macro小的在左边，macro相同时lane小的在左边）
        sorted_columns = sorted(all_macro_lane_columns, key=lambda x: (
            int(re.search(r'macro\s*(\d+)', x).group(1)),
            int(re.search(r'lane\s*(\d+)', x).group(1))
        ))
        
        # 为每个列创建数据
        for col_name in sorted_columns:
            col_data = []
            for parsed in row_macro_lane_data:
                col_data.append(parsed.get(col_name, ''))
            df[col_name] = col_data
        
        # 重新调整列顺序：将动态列放在code列之后，按macro和lane排序
        if sorted_columns:
            # 获取当前所有列
            all_columns = list(df.columns)
            
            # 找到code列的位置
            if 'code' in all_columns:
                code_index = all_columns.index('code')
                # 分离动态列和其他列
                other_columns = [col for col in all_columns if col not in sorted_columns]
                # 重新排列：code列之前的列 + code列 + 动态列（已排序）+ code列之后的列
                new_column_order = other_columns[:code_index] + ['code'] + sorted_columns + other_columns[code_index+1:]
                # 重新排列DataFrame的列
                df = df[new_column_order]
        
        return df
    
    def _check_code_contains_hex_range(self, code: str) -> int:
        """
        检查 code 中是否包含 0x1 到 0x16 之间的任意值
        
        Args:
            code: code 字符串
            
        Returns:
            如果包含 0x1 到 0x16 之间的任意值返回 1，否则返回 0
        """
        if not code:
            return 0
        
        # 匹配 0x1 到 0x16 之间的十六进制值
        # 0x1, 0x2, ..., 0x9, 0xa, 0xb, ..., 0xf, 0x10, 0x11, ..., 0x16
        # 使用正则表达式匹配这些值（不区分大小写）
        # 使用负向前瞻确保后面不是十六进制字符，避免匹配 0x1a 中的 0x1
        pattern = r'0x(?:1[0-6]|[1-9a-fA-F])(?![\da-fA-F])'
        if re.search(pattern, code, re.IGNORECASE):
            return 1
        return 0
    
    def _format_single_fourth_match(self, macro_ds: str, hex_str: str) -> str:
        """
        格式化单个fourth_match结果
        
        Args:
            macro_ds: "macroX,dsY" 格式的字符串
            hex_str: "0xZ" 格式的十六进制字符串
            
        Returns:
            格式化后的字符串：f"macroX laneY 0xP"
        """
        # 解析macroX,dsY
        macro_match = re.search(r'macro(\d+)', macro_ds)
        ds_match = re.search(r'ds(\d+)', macro_ds)
        
        if not macro_match or not ds_match:
            return ""
        
        macro_num = macro_match.group(1)
        ds_num = ds_match.group(1)
        
        # 解析十六进制数
        try:
            # 转换为整数
            if hex_str.startswith('0x') or hex_str.startswith('0X'):
                hex_value = int(hex_str, 16)
            else:
                # 如果不是十六进制格式，尝试直接转换
                hex_value = int(hex_str, 16) if all(c in '0123456789ABCDEFabcdef' for c in hex_str) else int(hex_str)
            
            # 提取bit0-5（即对0x3F进行按位与操作）
            bit0_5_value = hex_value & 0x3F
            
            # 格式化输出：macroX laneY 0xP
            return f"macro{macro_num} lane{ds_num} 0x{bit0_5_value:X}"
        except (ValueError, TypeError):
            return ""
    
    def extract_pattern_from_file(self, file_path: Path) -> Dict[str, Any]:
        """
        从文件中提取匹配模式的内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            包含提取结果的字典，键为模式名称，值为包含详细匹配信息的列表
        """
        result = {}
        extract_patterns = self.config.get("extract_patterns", [])
        
        if not extract_patterns:
            return result
        
        # 读取文件内容（使用缓存，避免重复读取）
        content = self._read_file_content(file_path)
        if not content:
            # 如果无法读取文件，返回空结果
            return result
        
        # 处理每个提取模式
        for pattern_config in extract_patterns:
            start_field = pattern_config.get("start_field", "")
            end_field = pattern_config.get("end_field", "")
            
            found, numbers = self._match_pattern(content, pattern_config)
            if not found or not numbers:
                result[f"{start_field}_{end_field}"] = []
                continue
            
            # 对每个数字进行二次、三次、三次匹配2、四次、五次匹配、六次匹配、版本匹配（如果配置了）
            final_results = []
            secondary_config = pattern_config.get("secondary_match", None)
            third_config = pattern_config.get("third_match", None)
            third_config_2 = pattern_config.get("third_match_2", None)
            fourth_config = pattern_config.get("fourth_match", None)
            fifth_config = pattern_config.get("fifth_match", None)
            sixth_config = pattern_config.get("sixth_match", None)
            match_version_config = pattern_config.get("match_version", None)
            
            for number in numbers:
                # 存储每个匹配项的详细结果
                match_data = {
                    "number": number,
                    "secondary_match": [],
                    "match_version": [],
                    "third_match": [],
                    "third_match_2": [],
                    "fourth_match": [],
                    "fifth_match": [],
                    "sixth_match": []
                }
                
                # 进行二次匹配（保留多个捕获组）
                if secondary_config:
                    secondary_matches = self._match_secondary_pattern_detailed(content, number, secondary_config)
                    if secondary_matches:
                        # secondary_match可能有多个匹配，每个匹配可能有多个捕获组
                        # 取第一个匹配的所有捕获组
                        if secondary_matches and secondary_matches[0]:
                            match_data["secondary_match"] = secondary_matches[0]
                
                # 进行版本匹配
                if match_version_config:
                    version_matches = self._match_secondary_pattern_detailed(content, number, match_version_config)
                    if version_matches:
                        # 取第一个匹配的第一个捕获组
                        if version_matches and version_matches[0]:
                            match_data["match_version"] = version_matches[0]
                
                # 进行三次匹配
                if third_config:
                    third_matches = self._match_secondary_pattern_detailed(content, number, third_config)
                    if third_matches:
                        if third_matches and third_matches[0]:
                            match_data["third_match"] = third_matches[0]
                
                # 进行三次匹配2
                if third_config_2:
                    third_matches_2 = self._match_secondary_pattern_detailed(content, number, third_config_2)
                    if third_matches_2:
                        if third_matches_2 and third_matches_2[0]:
                            match_data["third_match_2"] = third_matches_2[0]
                
                # 进行四次匹配
                if fourth_config:
                    fourth_matches = self._match_secondary_pattern_detailed(content, number, fourth_config)
                    if fourth_matches:
                        # 如果match_all为True，保留所有匹配，否则只取第一个
                        if fourth_config.get("match_all", False):
                            match_data["fourth_match"] = [" | ".join(" ".join(str(m) for m in match) for match in fourth_matches)]
                        else:
                            if fourth_matches and fourth_matches[0]:
                                match_data["fourth_match"] = fourth_matches[0]
                
                # 进行五次匹配
                if fifth_config:
                    fifth_matches = self._match_secondary_pattern_detailed(content, number, fifth_config)
                    if fifth_matches:
                        # 如果match_all为True，保留所有匹配，否则只取第一个
                        if fifth_config.get("match_all", False):
                            match_data["fifth_match"] = [" | ".join(" ".join(str(m) for m in match) for match in fifth_matches)]
                        else:
                            if fifth_matches and fifth_matches[0]:
                                match_data["fifth_match"] = fifth_matches[0]
                
                # 进行六次匹配（温度匹配）
                if sixth_config:
                    sixth_matches = self._match_secondary_pattern_detailed(content, number, sixth_config)
                    if sixth_matches:
                        # 如果match_all为True，保留所有匹配，否则只取第一个
                        if sixth_config.get("match_all", False):
                            match_data["sixth_match"] = [" | ".join(" ".join(str(m) for m in match) for match in sixth_matches)]
                        else:
                            if sixth_matches and sixth_matches[0]:
                                match_data["sixth_match"] = sixth_matches[0]
                
                final_results.append(match_data)
            
            result[f"{start_field}_{end_field}"] = final_results
        
        return result
    
    def extract_zip_recursive(self, zip_path: Path, extract_to: Path):
        """
        递归解压zip文件（逐层解压，不需要额外创建新文件夹）
        
        Args:
            zip_path: zip文件路径
            extract_to: 解压目标路径（直接解压到此目录）
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            
            # 删除已解压的zip文件
            zip_path.unlink()
            
            # 收集解压后目录中的所有zip文件（避免在遍历时修改目录结构）
            zip_files = []
            for item in extract_to.rglob('*.zip'):
                if item.is_file():
                    zip_files.append(item)
            
            # 递归解压所有找到的zip文件
            for zip_file in zip_files:
                # 逐层解压：直接解压到zip文件所在目录，不创建新文件夹
                self.extract_zip_recursive(zip_file, zip_file.parent)
        except (zipfile.BadZipFile, PermissionError, OSError) as e:
            # 跳过损坏的zip文件或权限错误
            pass
    
    def process_zip_files(self, folder_path: str):
        """
        处理文件夹中的zip文件，进行解压
        
        Args:
            folder_path: 要处理的文件夹路径
        """
        folder = Path(folder_path)
        
        # 收集所有zip文件（避免在遍历时修改目录结构）
        zip_files = []
        for item in folder.rglob('*.zip'):
            if item.is_file():
                zip_files.append(item)
        
        # 解压每个zip文件
        for zip_file in zip_files:
            try:
                # 第一层解压：创建与压缩包同名的文件夹
                zip_name_without_ext = zip_file.stem
                extract_folder = zip_file.parent / zip_name_without_ext
                
                # 如果文件夹已存在，添加序号
                counter = 1
                original_extract_folder = extract_folder
                while extract_folder.exists():
                    extract_folder = original_extract_folder.parent / f"{zip_name_without_ext}_{counter}"
                    counter += 1
                
                extract_folder.mkdir(parents=True, exist_ok=True)
                
                # 第一层解压到新创建的文件夹
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    zip_ref.extractall(extract_folder)
                
                # 删除原始zip文件
                zip_file.unlink()
                
                # 检查解压后的文件夹中是否有zip文件，如果有则递归解压
                nested_zip_files = []
                for item in extract_folder.rglob('*.zip'):
                    if item.is_file():
                        nested_zip_files.append(item)
                
                # 递归解压所有嵌套的zip文件（逐层解压，不创建新文件夹）
                for nested_zip in nested_zip_files:
                    self.extract_zip_recursive(nested_zip, nested_zip.parent)
            except (PermissionError, OSError, zipfile.BadZipFile) as e:
                # 跳过无法处理的zip文件
                continue
    
    def analyze_folder(self, folder_path: str, extract_zip: bool = False, delete_unmatched: bool = None) -> pd.DataFrame:
        """
        分析文件夹内容
        
        Args:
            folder_path: 要分析的文件夹路径
            extract_zip: 是否解压zip文件
            delete_unmatched: 是否删除未匹配的文件，如果为None则从配置文件读取
            
        Returns:
            包含分析结果的DataFrame
        """
        # 清空缓存，开始新的分析
        self._file_cache.clear()
        
        # 如果需要解压zip文件，先处理zip文件
        if extract_zip:
            self.process_zip_files(folder_path)
        
        data = []
        folder = Path(folder_path)
        
        for item in folder.rglob('*'):
            try:
                # 获取相对路径用于关键词匹配
                relative_path = str(item.relative_to(folder))
                
                # 如果文件路径没匹配到keyword，且UI勾选了删除选项，则删除该文件
                # delete_unmatched参数由UI传入，如果为None则默认为False（不删除）
                delete_if_no_match = delete_unmatched if delete_unmatched is not None else False
                if item.is_file() and delete_if_no_match:
                    if not self._check_path_keywords_match(relative_path):
                        try:
                            item.unlink()
                            print(f"删除未匹配文件: {relative_path}")
                            continue
                        except (PermissionError, OSError) as e:
                            print(f"无法删除文件 {relative_path}: {e}")
                            continue
                
                # 检查是否应该分析此文件（传入Path对象以便检查文件内容）
                if not self.should_analyze(relative_path, item):
                    print(f"跳过文件: {relative_path}")
                    continue
                else:
                    print(f"分析文件: {relative_path}")
                
                if item.is_file():
                    stat = item.stat()
                    try:
                        file_content = item.read_text(encoding='utf-8', errors='ignore')
                    except OSError:
                        file_content = ''
                    display_clock_date = self._parse_first_display_clock_date(file_content) or ''
                    # 提取匹配模式的内容
                    extracted_data = self.extract_pattern_from_file(item)
                    
                    # 构建文件基本信息
                    province, city = self._parse_location_from_path(relative_path, item.name)
                    # #region agent log
                    try:
                        import json as _json
                        with open(AGENT_DEBUG_LOG_PATH, "a", encoding="utf-8") as _df:
                            _df.write(_json.dumps({"sessionId": "a5fec5", "hypothesisId": "L1", "location": "data_processor.py:analyze_folder", "message": "location from folder path", "data": {"relative_path": relative_path, "filename": item.name, "province": province, "city": city, "source": "folder" if "工程师报告" in relative_path else "filename"}, "timestamp": int(__import__("time").time() * 1000)}, ensure_ascii=False) + "\n")
                    except OSError:
                        pass
                    # #endregion
                    base_file_data = {
                        '文件路径': relative_path,
                        '文件名': item.name,
                        '省份': province,
                        '城市': city,
                        '采集日期': display_clock_date,
                        '文件类型': item.suffix or '无扩展名',
                        '文件大小(字节)': stat.st_size,
                        '文件大小(MB)': round(stat.st_size / (1024 * 1024), 2),
                        '修改时间': pd.Timestamp.fromtimestamp(stat.st_mtime),
                        '是否文件': '是',
                        '是否目录': '否'
                    }
                    
                    # 如果没有任何匹配项，仍然添加一行（不包含匹配数据）
                    if not extracted_data:
                        data.append(base_file_data.copy())
                    else:
                        # 处理每个匹配模式的结果
                        has_match_data = False
                        for pattern_name, match_data_list in extracted_data.items():
                            if not match_data_list:  # 如果没有匹配到的数据
                                continue
                            
                            has_match_data = True
                            # 为每个匹配数据创建一行
                            for match_data in match_data_list:
                                row_data = base_file_data.copy()
                                row_data['匹配项'] = pattern_name
                                row_data['匹配值'] = match_data.get("number", "")
                                
                                # 处理secondary_match，分成三列：条码1、条码2、条码3
                                secondary_match = match_data.get("secondary_match", [])
                                row_data['条码1'] = secondary_match[0] if len(secondary_match) > 0 else ""
                                row_data['条码2'] = secondary_match[1] if len(secondary_match) > 1 else ""
                                row_data['条码3'] = secondary_match[2] if len(secondary_match) > 2 else ""
                                
                                # 处理match_version，列名叫版本号
                                match_version = match_data.get("match_version", [])
                                version_str = match_version[0] if len(match_version) > 0 else ""
                                row_data['版本号'] = version_str
                                
                                # 根据版本号决定时间列
                                if version_str == "R024":
                                    # 如果版本号是R024：
                                    # third_match_2的列名叫做时间
                                    third_match_2 = match_data.get("third_match_2", [])
                                    row_data['时间'] = " ".join(third_match_2) if third_match_2 else ""
                                    # 忽略third_match
                                else:
                                    # 如果版本号不为R024：
                                    # third_match的列名叫做时间
                                    third_match = match_data.get("third_match", [])
                                    row_data['时间'] = " ".join(third_match) if third_match else ""
                                
                                # 处理sixth_match（温度），单独列一列
                                sixth_match = match_data.get("sixth_match", [])
                                row_data['温度'] = " ".join(sixth_match) if sixth_match else ""
                                
                                # 根据版本号决定code值（先计算，不添加到字典）
                                if version_str == "R024":
                                    # fifth_match作为code
                                    fifth_match = match_data.get("fifth_match", [])
                                    code_value = " ".join(fifth_match) if fifth_match else ""
                                else:
                                    # fourth_match作为code，需要格式化
                                    fourth_match = match_data.get("fourth_match", [])
                                    code_value = self._format_fourth_match(fourth_match) if fourth_match else ""
                                
                                # 检查 code 中是否包含 0x1 到 0x16 之间的值（先添加code_hex_check）
                                row_data['code_hex_check'] = self._check_code_contains_hex_range(code_value)
                                # 然后添加code列
                                row_data['code'] = code_value
                                
                                data.append(row_data)
                        
                        # 如果没有任何匹配数据，添加一行基本信息
                        if not has_match_data:
                            data.append(base_file_data.copy())
                elif item.is_dir():
                    data.append({
                        '文件路径': relative_path,
                        '文件名': item.name,
                        '文件类型': '目录',
                        '文件大小(字节)': 0,
                        '文件大小(MB)': 0,
                        '修改时间': pd.Timestamp.fromtimestamp(item.stat().st_mtime),
                        '是否文件': '否',
                        '是否目录': '是'
                    })
            except (PermissionError, OSError):
                # 跳过无法访问的文件
                continue
        
        df = pd.DataFrame(data)
        
        # 根据code列动态添加 macro X lane Y 列
        df = self._add_dynamic_macro_lane_columns(df)
        
        return df
    
    def _convert_hex_to_decimal(self, value: str) -> int:
        """
        将十六进制字符串转换为十进制整数
        
        Args:
            value: 十六进制字符串（如 "0x11"）
            
        Returns:
            十进制整数，如果转换失败返回None
        """
        if not value or not isinstance(value, str):
            return None
        
        value = value.strip()
        # 检查是否是十六进制格式（0x开头）
        if value.startswith('0x') or value.startswith('0X'):
            try:
                return int(value, 16)
            except (ValueError, TypeError):
                return None
        return None
    
    def _process_macro_lane_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        处理macro x lane y列：
        1. 将十六进制值转换为十进制
        2. 将macro x lane y列的数据拆分成多行，每行包含macro、lane和code值
        
        Args:
            df: 原始DataFrame
            
        Returns:
            处理后的DataFrame
        """
        if df.empty:
            return df
        
        # 找到所有macro x lane y列（列名格式：macro X lane Y）
        macro_lane_pattern = re.compile(r'^macro\s+\d+\s+lane\s+\d+$')
        macro_lane_columns = [col for col in df.columns if macro_lane_pattern.match(str(col))]
        
        if not macro_lane_columns:
            return df
        
        # 收集所有非macro x lane y列（同时排除原来的code列，因为会被新的code列替代）
        non_macro_lane_columns = [col for col in df.columns if col not in macro_lane_columns and col != 'code']
        
        # 存储新的行数据
        new_rows = []
        
        # 遍历每一行
        for idx, row in df.iterrows():
            # 获取该行的所有macro x lane y数据
            macro_lane_data = []
            
            for col_name in macro_lane_columns:
                value = row[col_name]
                if value and str(value).strip():
                    # 解析macro和lane数字
                    macro_match = re.search(r'macro\s*(\d+)', col_name)
                    lane_match = re.search(r'lane\s*(\d+)', col_name)
                    
                    if macro_match and lane_match:
                        macro_num = int(macro_match.group(1))
                        lane_num = int(lane_match.group(1))
                        
                        # 将十六进制值转换为十进制，如果已经是数字则直接使用
                        decimal_val = self._convert_hex_to_decimal(str(value))
                        if decimal_val is None:
                            # 如果不是十六进制格式，尝试直接转换为数字
                            try:
                                if pd.notna(value):
                                    decimal_val = int(float(str(value)))
                            except (ValueError, TypeError):
                                # 如果转换失败，跳过这个值
                                continue
                        
                        if decimal_val is not None:
                            macro_lane_data.append({
                                'macro': macro_num,
                                'lane': lane_num,
                                'code': decimal_val
                            })
            
            # 如果有macro x lane y数据，为每个macro-lane组合创建一行
            if macro_lane_data:
                for ml_data in macro_lane_data:
                    new_row = {}
                    # 复制所有非macro x lane y列的数据
                    for col in non_macro_lane_columns:
                        new_row[col] = row[col]
                    # 添加macro、lane和code列
                    new_row['macro'] = ml_data['macro']
                    new_row['lane'] = ml_data['lane']
                    new_row['code'] = ml_data['code']
                    new_rows.append(new_row)
            else:
                # 如果没有macro x lane y数据，保留原行（不包含macro、lane、code列）
                new_row = {}
                for col in non_macro_lane_columns:
                    new_row[col] = row[col]
                new_rows.append(new_row)
        
        # 创建新的DataFrame
        new_df = pd.DataFrame(new_rows)
        
        # 重新排列列顺序：将macro、lane、code列放在一起
        all_columns = list(new_df.columns)
        
        # 找到原来的code列的位置（如果存在，这是旧的code列，现在可能已经不需要了）
        # 但我们主要关注新的macro、lane、code列的位置
        new_column_order = []
        
        # 先添加所有非macro/lane/code列
        for col in all_columns:
            if col not in ['macro', 'lane', 'code']:
                new_column_order.append(col)
        
        # 添加macro、lane、code列（如果存在）
        if 'macro' in all_columns:
            new_column_order.append('macro')
        if 'lane' in all_columns:
            new_column_order.append('lane')
        if 'code' in all_columns:
            new_column_order.append('code')
        
        new_df = new_df[new_column_order]
        return new_df
    
    def save_to_excel(self, df: pd.DataFrame, output_path: str) -> None:
        """
        将DataFrame保存为Excel文件
        
        Args:
            df: 要保存的DataFrame
            output_path: 输出文件路径
        """
        if df.empty:
            raise ValueError("数据为空，无法保存")
        
        # 在保存前处理macro x lane y列
        df = self._process_macro_lane_columns(df)
        
        # 去重：如果文件名和文件大小相同，只保留一条记录
        if '文件名' in df.columns and '文件大小(字节)' in df.columns:
            # 记录去重前的行数
            before_count = len(df)
            # 基于文件名和文件大小去重，保留第一条记录
            df = df.drop_duplicates(subset=['文件名', '文件大小(字节)','macro','lane'], keep='first')
            after_count = len(df)
            if before_count != after_count:
                print(f"去重完成：从 {before_count} 条记录减少到 {after_count} 条记录")
        
        df.to_excel(output_path, index=False, engine='openpyxl')

    FAULT_CODE_THRESHOLD = 22  # code < 0x16

    def _parse_codes_decimal(self, code: str) -> List[int]:
        """从 code 字符串解析所有十进制 code 值"""
        if not code or not str(code).strip():
            return []
        parsed = self._parse_code_macro_lane(str(code))
        values = []
        for hex_val in parsed.values():
            decimal_val = self._convert_hex_to_decimal(str(hex_val))
            if decimal_val is not None:
                values.append(decimal_val)
        return values

    def _parse_first_display_clock_date(self, content: str) -> Optional[str]:
        """从文件内容提取第一个 display clock 日期，返回 YYYY-MM-DD"""
        if not content:
            return None
        block_match = re.search(
            r'display clock \| no-more\s*\r?\n(.*?)\r?\n</Message>',
            content,
            re.DOTALL | re.IGNORECASE,
        )
        if not block_match:
            return None
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', block_match.group(1))
        return date_match.group(1) if date_match else None

    def _parse_folder_collection_date(self, path_str: str) -> Optional[str]:
        """从路径文件夹名提取采集日期 YYYYMMDD，优先取离文件最近的文件夹。"""
        if not path_str or not str(path_str).strip():
            return None
        parts = Path(str(path_str)).parts
        if not parts:
            return None
        folder_parts = parts[:-1] if '.' in parts[-1] else parts
        for part in reversed(folder_parts):
            for match in re.finditer(r'(\d{8})', part):
                raw = match.group(1)
                try:
                    year = int(raw[0:4])
                    month = int(raw[4:6])
                    day = int(raw[6:8])
                    if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                        return f"{year:04d}-{month:02d}-{day:02d}"
                except (ValueError, TypeError):
                    continue
        return None

    def _resolve_year_month_from_clock(
        self,
        clock_date: str,
        relative_path: str,
        analyze_root: Optional[str] = None,
    ) -> Tuple[Optional[int], Optional[int]]:
        """年份、月份：路径文件夹 YYYYMMDD 优先，否则 display clock；再无则年份回退路径首段"""
        folder_date = self._parse_folder_collection_date(relative_path)
        if not folder_date and analyze_root:
            folder_date = self._parse_folder_collection_date(analyze_root)
        if folder_date:
            year = int(folder_date[:4])
            month = int(folder_date[5:7])
            # #region agent log
            try:
                import json as _json
                with open(AGENT_DEBUG_LOG_PATH, "a", encoding="utf-8") as _df:
                    _df.write(_json.dumps({"sessionId": "1d1172", "runId": "pre-fix", "hypothesisId": "H3-H4", "location": "data_processor.py:_resolve_year_month_from_clock", "message": "year month from folder", "data": {"relative_path": relative_path, "analyze_root": analyze_root, "folder_date": folder_date, "clock_date": clock_date, "year": year, "month": month}, "timestamp": int(__import__("time").time() * 1000)}, ensure_ascii=False) + "\n")
            except OSError:
                pass
            # #endregion
            return year, month
        date_str = self._parse_record_date(clock_date)
        if date_str:
            return self._parse_record_year(date_str), self._parse_record_month(date_str)
        return self._parse_record_year_from_path(relative_path), None

    def _parse_record_date(self, time_str: str) -> Optional[str]:
        """从时间字段解析日期，返回 YYYY-MM-DD"""
        if not time_str or not str(time_str).strip():
            return None
        text = str(time_str).strip()
        match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
        return match.group(1) if match else None

    def _parse_record_year(self, time_str: str) -> Optional[int]:
        date_str = self._parse_record_date(time_str)
        if date_str:
            try:
                return int(date_str[:4])
            except (ValueError, TypeError):
                return None
        return None

    def _parse_record_month(self, time_str: str) -> Optional[int]:
        date_str = self._parse_record_date(time_str)
        if date_str:
            try:
                return int(date_str[5:7])
            except (ValueError, TypeError):
                return None
        return None

    def _resolve_record_month(self, time_str: str) -> Optional[int]:
        return self._parse_record_month(time_str)

    def _normalize_optional_int(self, value: Any) -> Optional[int]:
        if value is None:
            return None
        try:
            if pd.isna(value):
                return None
        except (TypeError, ValueError):
            pass
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _parse_record_year_from_path(self, relative_path: str) -> Optional[int]:
        """从文件相对路径的首段目录解析年份，如 2025年春节巡检"""
        if not relative_path:
            return None
        first_part = Path(str(relative_path)).parts[0] if Path(str(relative_path)).parts else ""
        match = re.match(r'(\d{4})', first_part)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, TypeError):
                return None
        return None

    def _resolve_record_year(self, relative_path: str, time_str: str) -> Optional[int]:
        year = self._parse_record_year_from_path(relative_path)
        if year is not None:
            return year
        return self._parse_record_year(time_str)

    def _merge_board_records_by_sn(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """同一单板sn在同一省市、同一年月只计一块单板，合并多槽位及同月内重复扫描"""
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for r in records:
            sn = str(r.get('条码2', '') or '').strip()
            year = r.get('年份')
            month = r.get('月份')
            if sn:
                key = f"{sn}|{r.get('省份', '')}|{r.get('城市', '')}|{year}|{month}"
            else:
                key = f"{r.get('文件路径', '')}|{r.get('匹配值', '')}"
            groups.setdefault(key, []).append(r)

        merged: List[Dict[str, Any]] = []
        for items in groups.values():
            base = dict(items[0])
            codes: List[int] = []
            seen_codes: set = set()
            for it in items:
                for code_val in it.get('codes', []):
                    if code_val not in seen_codes:
                        seen_codes.add(code_val)
                        codes.append(code_val)
            fault_codes = [c for c in codes if c < self.FAULT_CODE_THRESHOLD]
            base['codes'] = codes
            base['fault_codes'] = fault_codes
            base['is_fault'] = len(fault_codes) > 0
            base['code_sum'] = sum(codes)
            merged.append(base)
        return merged

    def build_board_records(
        self,
        df: pd.DataFrame,
        chip_barcode2: Optional[str] = None,
        analyze_root: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """将 DataFrame 转为单板级记录列表（每个单板sn在同一省市、同一年月计一块单板）"""
        if df.empty or '匹配值' not in df.columns:
            return []

        work = df.copy()
        work = work[work['匹配值'].astype(str).str.strip() != '']
        if chip_barcode2:
            work = work[work['条码2'].astype(str) == chip_barcode2]

        file_clock: Dict[str, str] = {}
        for _, row in work.iterrows():
            file_path = str(row.get('文件路径', '') or '')
            clock_date = str(row.get('采集日期', '') or '').strip()
            if file_path and clock_date and file_path not in file_clock:
                file_clock[file_path] = clock_date

        def _row_year_month(row) -> Tuple[Optional[int], Optional[int]]:
            file_path = str(row.get('文件路径', '') or '')
            clock_date = file_clock.get(file_path, str(row.get('采集日期', '') or '').strip())
            return self._resolve_year_month_from_clock(clock_date, file_path, analyze_root)

        work[['_年份', '_月份']] = work.apply(
            lambda row: pd.Series(_row_year_month(row)),
            axis=1,
        )
        work = work.drop_duplicates(
            subset=['_年份', '_月份', '省份', '城市', '文件名', '匹配值'],
            keep='first',
        )

        records = []
        for _, row in work.iterrows():
            codes = self._parse_codes_decimal(row.get('code', ''))
            fault_codes = [c for c in codes if c < self.FAULT_CODE_THRESHOLD]
            time_str = str(row.get('时间', '') or '')
            file_path = str(row.get('文件路径', '') or '')
            clock_date = file_clock.get(file_path, str(row.get('采集日期', '') or '').strip())
            year = self._normalize_optional_int(row.get('_年份'))
            month = self._normalize_optional_int(row.get('_月份'))
            fname = str(row.get('文件名', ''))
            site_name = fname[:-4] if fname.lower().endswith('.txt') else fname
            folder_date = self._parse_folder_collection_date(file_path) or self._parse_folder_collection_date(analyze_root or "")
            records.append({
                '文件名': fname,
                '网元名称': site_name,
                '文件路径': file_path,
                '匹配值': str(row.get('匹配值', '')),
                '省份': str(row.get('省份', '') or ''),
                '城市': str(row.get('城市', '') or ''),
                '条码1': str(row.get('条码1', '') or ''),
                '条码2': str(row.get('条码2', '') or ''),
                '时间': time_str,
                '采集日期': clock_date,
                '日期': folder_date or self._parse_record_date(clock_date) or self._parse_record_date(time_str),
                '年份': year,
                '月份': month,
                'codes': codes,
                'fault_codes': fault_codes,
                'is_fault': len(fault_codes) > 0,
            })
        merged = self._merge_board_records_by_sn(records)
        # #region agent log
        try:
            import json as _json
            from collections import Counter as _Counter
            with open(AGENT_DEBUG_LOG_PATH, "a", encoding="utf-8") as _df:
                _df.write(_json.dumps({"sessionId": "a5fec5", "hypothesisId": "M1", "location": "data_processor.py:build_board_records", "message": "board merge by year-month", "data": {"slot_records": len(records), "merged_records": len(merged), "by_year_month": {f"{y}-{m}": c for (y, m), c in _Counter((r.get("年份"), r.get("月份")) for r in merged).items()}}, "timestamp": int(__import__("time").time() * 1000)}, ensure_ascii=False) + "\n")
        except OSError:
            pass
        # #endregion
        return merged

    def get_filter_options(self, board_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """返回芯片、省、市、年份等筛选选项"""
        chips = sorted({r['条码2'] for r in board_records if r.get('条码2')})
        provinces = sorted({r['省份'] for r in board_records if r.get('省份')})
        city_map: Dict[str, List[str]] = {}
        standalone_cities: List[str] = []
        for r in board_records:
            p, c = r.get('省份', ''), r.get('城市', '')
            if not c:
                continue
            if p:
                city_map.setdefault(p, [])
                if c not in city_map[p]:
                    city_map[p].append(c)
            else:
                if c not in standalone_cities:
                    standalone_cities.append(c)
        for p in city_map:
            city_map[p] = sorted(city_map[p])
        standalone_cities = sorted(standalone_cities)
        # #region agent log
        try:
            all_cities = sorted({c for cities in city_map.values() for c in cities} | set(standalone_cities))
            with open(AGENT_DEBUG_LOG_PATH, "a", encoding="utf-8") as _df:
                _df.write(json.dumps({
                    "sessionId": "1d1172",
                    "runId": "geo-cities",
                    "hypothesisId": "H2-H3",
                    "location": "data_processor.py:get_filter_options",
                    "message": "filter city geojson coverage",
                    "data": {
                        "provinces": provinces,
                        "all_cities": all_cities,
                        "geojson_hits": [c for c in all_cities if c in GEOJSON_CITY_NAMES],
                        "non_geojson": [c for c in all_cities if c not in GEOJSON_CITY_NAMES],
                    },
                    "timestamp": int(__import__("time").time() * 1000),
                }, ensure_ascii=False) + "\n")
        except OSError:
            pass
        # #endregion
        years = sorted({r['年份'] for r in board_records if r.get('年份') is not None})
        year_month_map: Dict[int, List[int]] = {}
        for r in board_records:
            y = self._normalize_optional_int(r.get('年份'))
            m = self._normalize_optional_int(r.get('月份'))
            if y is not None and m is not None:
                year_month_map.setdefault(y, set()).add(m)
        year_month_map = {y: sorted(months) for y, months in sorted(year_month_map.items())}
        latest_year = years[-1] if years else None
        latest_month = year_month_map.get(latest_year, [])[-1] if latest_year else None
        site_names = sorted({r.get('网元名称', '') for r in board_records if r.get('网元名称')})
        result = {
            'chips': chips,
            'provinces': provinces,
            'city_map': city_map,
            'standalone_cities': standalone_cities,
            'years': years,
            'year_month_map': year_month_map,
            'site_names': site_names,
            'latest_year': latest_year,
            'latest_month': latest_month,
        }
        return result

    def _filter_board_records(
        self,
        board_records: List[Dict[str, Any]],
        provinces: Optional[List[str]] = None,
        cities: Optional[List[str]] = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
        years: Optional[List[int]] = None,
        months: Optional[List[int]] = None,
        chips: Optional[List[str]] = None,
        site_names: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        result = board_records
        if chips:
            chip_set = set(chips)
            result = [r for r in result if r.get('条码2') in chip_set]
        if provinces:
            prov_set = set(provinces)
            result = [r for r in result if r.get('省份') in prov_set]
        if cities:
            city_set = set(cities)
            result = [r for r in result if r.get('城市') in city_set]
        if site_names:
            site_set = set(site_names)
            result = [r for r in result if r.get('网元名称') in site_set]
        if year is not None:
            result = [r for r in result if self._normalize_optional_int(r.get('年份')) == year]
        if month is not None:
            result = [r for r in result if self._normalize_optional_int(r.get('月份')) == month]
        if years:
            year_set = set(years)
            result = [r for r in result if self._normalize_optional_int(r.get('年份')) in year_set]
        if months:
            month_set = set(months)
            result = [r for r in result if self._normalize_optional_int(r.get('月份')) in month_set]
        return result

    def _calc_region_stats(self, records: List[Dict[str, Any]]) -> Dict[str, int]:
        total = len(records)
        fault = sum(1 for r in records if r.get('is_fault'))
        return {'total': total, 'fault': fault}

    def get_vulcanization_map_stats(
        self,
        board_records: List[Dict[str, Any]],
        provinces: Optional[List[str]] = None,
        cities: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """返回省或市维度的故障比例数据，支持多省/多市筛选"""
        filtered = self._filter_board_records(board_records, provinces=provinces, cities=cities)

        if cities:
            regions: Dict[str, Dict[str, int]] = {}
            for r in filtered:
                name = r.get('城市', '')
                if not name:
                    continue
                regions.setdefault(name, {'total': 0, 'fault': 0})
                regions[name]['total'] += 1
                if r.get('is_fault'):
                    regions[name]['fault'] += 1
            level = 'city_focus'
            map_provinces = sorted({r.get('省份', '') for r in filtered if r.get('省份')})
        elif provinces:
            regions = {}
            for r in filtered:
                name = r.get('城市', '')
                if not name:
                    continue
                regions.setdefault(name, {'total': 0, 'fault': 0})
                regions[name]['total'] += 1
                if r.get('is_fault'):
                    regions[name]['fault'] += 1
            level = 'city'
            map_provinces = list(provinces)
        else:
            regions = {}
            for r in filtered:
                name = r.get('省份', '')
                if not name:
                    continue
                regions.setdefault(name, {'total': 0, 'fault': 0})
                regions[name]['total'] += 1
                if r.get('is_fault'):
                    regions[name]['fault'] += 1
            level = 'province'
            map_provinces = []

        items = []
        for name, counts in sorted(regions.items()):
            total = counts['total']
            fault = counts['fault']
            ratio = round(fault / total * 100, 2) if total else 0.0
            items.append({
                'name': name,
                'ratio': ratio,
                'fault_count': fault,
                'total_count': total,
            })

        overall = self._calc_region_stats(filtered)
        overall_ratio = round(overall['fault'] / overall['total'] * 100, 2) if overall['total'] else 0.0

        result = {
            'level': level,
            'items': items,
            'map_provinces': map_provinces,
            'overall': {
                'ratio': overall_ratio,
                'fault_count': overall['fault'],
                'total_count': overall['total'],
            },
        }
        return result

    def lookup_fault_rates(
        self,
        board_records: List[Dict[str, Any]],
        barcode1: Optional[str] = None,
        barcode2: Optional[str] = None,
    ) -> Dict[str, Any]:
        """按条码1或条码2查询各省/市故障率"""
        if not barcode1 and not barcode2:
            return {'provinces': [], 'cities': []}

        matched = board_records
        if barcode1:
            matched = [r for r in matched if r.get('条码1') == barcode1]
        if barcode2:
            matched = [r for r in matched if r.get('条码2') == barcode2]

        province_stats: Dict[str, Dict[str, int]] = {}
        city_stats: Dict[str, Dict[str, int]] = {}

        for r in matched:
            p, c = r.get('省份', ''), r.get('城市', '')
            if p:
                province_stats.setdefault(p, {'total': 0, 'fault': 0})
                province_stats[p]['total'] += 1
                if r.get('is_fault'):
                    province_stats[p]['fault'] += 1
            if p and c:
                key = f"{p}|{c}"
                city_stats.setdefault(key, {'total': 0, 'fault': 0, 'province': p, 'city': c})
                city_stats[key]['total'] += 1
                if r.get('is_fault'):
                    city_stats[key]['fault'] += 1

        def to_rate_list(stats: Dict[str, Any], name_key: str) -> List[Dict[str, Any]]:
            rows = []
            for key, counts in sorted(stats.items()):
                total = counts['total']
                fault = counts['fault']
                rows.append({
                    name_key: key if name_key == 'province' else counts.get('city', key.split('|')[-1]),
                    'province': counts.get('province', key) if name_key == 'city' else key,
                    'city': counts.get('city', '') if name_key == 'city' else '',
                    'fault_count': fault,
                    'total_count': total,
                    'ratio': round(fault / total * 100, 2) if total else 0.0,
                })
            return rows

        return {
            'provinces': to_rate_list(province_stats, 'province'),
            'cities': to_rate_list(city_stats, 'city'),
            'matched_count': len(matched),
        }

    def get_alerts(
        self,
        board_records: List[Dict[str, Any]],
        threshold: float = 0.05,
    ) -> List[Dict[str, Any]]:
        """硫化比例（code < 0x16）超过阈值时，按市生成预警"""
        city_groups: Dict[str, List[Dict[str, Any]]] = {}
        for r in board_records:
            p, c = r.get('省份', ''), r.get('城市', '')
            if not p or not c:
                continue
            city_groups.setdefault(f"{p}|{c}", []).append(r)

        alerts = []
        for key, recs in city_groups.items():
            p, c = key.split('|', 1)
            total = len(recs)
            if total == 0:
                continue
            fault = sum(1 for r in recs if r.get('is_fault'))
            ratio = fault / total
            if ratio > threshold:
                alerts.append({
                    'province': p,
                    'city': c,
                    'fault_count': fault,
                    'total_count': total,
                    'ratio': round(ratio * 100, 2),
                })

        alerts.sort(key=lambda x: (-x['ratio'], x['province'], x['city']))
        return alerts

    def get_code_distribution(
        self,
        board_records: List[Dict[str, Any]],
        provinces: Optional[List[str]] = None,
        cities: Optional[List[str]] = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
        chips: Optional[List[str]] = None,
        site_names: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """柱状图：各 code 值对应的单板数量"""
        filtered = self._filter_board_records(
            board_records,
            provinces=provinces,
            cities=cities,
            year=year,
            month=month,
            chips=chips,
            site_names=site_names,
        )
        code_counts: Dict[int, int] = {}
        for r in filtered:
            codes = r.get('codes', [])
            if not codes:
                continue
            min_code = min(codes)
            code_counts[min_code] = code_counts.get(min_code, 0) + 1
        result = [
            {'code_value': k, 'code_hex': f'0x{k:02X}', 'board_count': v}
            for k, v in sorted(code_counts.items())
        ]
        # #region agent log
        try:
            with open(AGENT_DEBUG_LOG_PATH, "a", encoding="utf-8") as _df:
                _df.write(json.dumps({
                    "sessionId": "1d1172",
                    "runId": "pre-fix",
                    "hypothesisId": "H5",
                    "location": "data_processor.py:get_code_distribution",
                    "message": "dynamic code bar axis",
                    "data": {
                        "filtered_boards": len(filtered),
                        "code_values": [x['code_value'] for x in result],
                        "counts": result,
                    },
                    "timestamp": int(__import__("time").time() * 1000),
                }, ensure_ascii=False) + "\n")
        except OSError:
            pass
        # #endregion
        return result

    def get_fault_trend(
        self,
        board_records: List[Dict[str, Any]],
        provinces: Optional[List[str]] = None,
        cities: Optional[List[str]] = None,
        chips: Optional[List[str]] = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """折线图：按看网采集时间点统计硫化比例"""
        filtered = self._filter_board_records(
            board_records, provinces=provinces, cities=cities, chips=chips, year=year, month=month,
        )
        time_groups: Dict[str, List[Dict[str, Any]]] = {}
        for r in filtered:
            time_str = str(r.get('时间', '') or '').strip()
            if not time_str:
                continue
            time_groups.setdefault(time_str, []).append(r)

        items = []
        for time_str, recs in time_groups.items():
            total = len(recs)
            fault = sum(1 for r in recs if r.get('is_fault'))
            ratio = round(fault / total * 100, 2) if total else 0.0
            sort_key = self._parse_record_date(time_str) or time_str
            items.append({
                'time': time_str,
                'sort_key': sort_key,
                'ratio': ratio,
                'fault_count': fault,
                'total_count': total,
            })

        items.sort(key=lambda x: x['sort_key'])
        result = [
            {
                'time': x['time'],
                'ratio': x['ratio'],
                'fault_count': x['fault_count'],
                'total_count': x['total_count'],
            }
            for x in items
        ]
        # #region agent log
        try:
            import json as _json
            with open(AGENT_DEBUG_LOG_PATH, "a", encoding="utf-8") as _df:
                _df.write(_json.dumps({"sessionId": "a5fec5", "hypothesisId": "T1", "location": "data_processor.py:get_fault_trend", "message": "fault trend ratio", "data": {"year": year, "point_count": len(result), "sample": result[:3]}, "timestamp": int(__import__("time").time() * 1000)}, ensure_ascii=False) + "\n")
        except OSError:
            pass
        # #endregion
        return result

    def get_code_sum_trend(
        self,
        board_records: List[Dict[str, Any]],
        chips: List[str],
        provinces: Optional[List[str]] = None,
        cities: Optional[List[str]] = None,
        site_names: Optional[List[str]] = None,
        years: Optional[List[int]] = None,
        months: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """折线图：按年月统计各 SN 的 code 合数"""
        if not chips:
            return []

        filtered = self._filter_board_records(
            board_records,
            provinces=provinces,
            cities=cities,
            chips=chips[:10],
            site_names=site_names,
            years=years if years else None,
            months=months if months else None,
        )

        series_list: List[Dict[str, Any]] = []
        for chip in chips[:10]:
            chip_recs = [r for r in filtered if r.get('条码2') == chip]
            if not chip_recs:
                continue

            time_groups: Dict[Tuple[int, int], List[Dict[str, Any]]] = {}
            for r in chip_recs:
                y = self._normalize_optional_int(r.get('年份'))
                m = self._normalize_optional_int(r.get('月份'))
                if y is None or m is None:
                    continue
                time_groups.setdefault((y, m), []).append(r)

            sites = sorted({str(r.get('网元名称', '') or '') for r in chip_recs if r.get('网元名称')})
            site_label = '、'.join(sites) if sites else '未知网元'
            label = f"{chip} · {site_label}"

            points = []
            for (y, m) in sorted(time_groups.keys()):
                recs = time_groups[(y, m)]
                code_sum = sum(int(r.get('code_sum') or 0) for r in recs)
                point_sites = sorted({str(r.get('网元名称', '') or '') for r in recs if r.get('网元名称')})
                points.append({
                    'time_label': f'{y}年{m}月',
                    'year': y,
                    'month': m,
                    'code_sum': code_sum,
                    'site_name': '、'.join(point_sites) if point_sites else site_label,
                })

            if points:
                series_list.append({
                    'chip': chip,
                    'site_name': site_label,
                    'label': label,
                    'points': points,
                })

        return series_list


def main():
    """主函数：直接运行此文件时自动分析指定目录"""
    # 要分析的目录路径
    folder_path = "/Users/xianbo/vulcanization/vulcanization/logs/test"
    
    # 输出Excel文件路径（与分析目录同目录）
    output_path = os.path.join(folder_path, "分析结果.xlsx")
    
    print(f"开始分析目录: {folder_path}")
    
    try:
        # 创建数据处理器
        processor = DataProcessor()
        
        # 分析文件夹（不自动解压zip，如需解压可设置 extract_zip=True）
        df = processor.analyze_folder(folder_path, extract_zip=False)
        
        if df.empty:
            print("警告: 没有找到符合条件的文件！")
            print("请检查配置文件中的关键词设置。")
            return
        
        # 保存到Excel
        processor.save_to_excel(df, output_path)
        
        print(f"分析完成！共分析 {len(df)} 个项目")
        print(f"Excel文件已保存到: {output_path}")
        
    except Exception as e:
        print(f"分析过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

