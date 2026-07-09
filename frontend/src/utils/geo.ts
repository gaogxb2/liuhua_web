/** 省级行政区划 adcode，用于加载 DataV 省地图 */
export const PROVINCE_ADCODE: Record<string, string> = {
  北京市: '110000',
  天津市: '120000',
  河北省: '130000',
  山西省: '140000',
  内蒙古自治区: '150000',
  辽宁省: '210000',
  吉林省: '220000',
  黑龙江省: '230000',
  上海市: '310000',
  江苏省: '320000',
  浙江省: '330000',
  安徽省: '340000',
  福建省: '350000',
  江西省: '360000',
  山东省: '370000',
  河南省: '410000',
  湖北省: '420000',
  湖南省: '430000',
  广东省: '440000',
  广西壮族自治区: '450000',
  海南省: '460000',
  重庆市: '500000',
  四川省: '510000',
  贵州省: '520000',
  云南省: '530000',
  西藏自治区: '540000',
  陕西省: '610000',
  甘肃省: '620000',
  青海省: '630000',
  宁夏回族自治区: '640000',
  新疆维吾尔自治区: '650000',
  台湾省: '710000',
  香港特别行政区: '810000',
  澳门特别行政区: '820000',
}

export function toGeoRegionName(name: string): string {
  if (!name) return ''
  if (name.endsWith('省')) return name.slice(0, -1)
  if (name.endsWith('市') && !['北京市', '上海市', '天津市', '重庆市'].includes(name)) {
    return name.replace(/市$/, '')
  }
  if (name.endsWith('自治区')) {
    if (name.startsWith('内蒙古')) return '内蒙古'
    if (name.startsWith('广西')) return '广西'
    if (name.startsWith('西藏')) return '西藏'
    if (name.startsWith('宁夏')) return '宁夏'
    if (name.startsWith('新疆')) return '新疆'
  }
  if (name.endsWith('特别行政区')) return name.replace('特别行政区', '')
  return name
}

/** 将数据中的省名匹配到 GeoJSON / PROVINCE_ADCODE 中的标准名称 */
export function matchProvinceGeoName(dataProvince: string, geoNames?: string[]): string {
  if (!dataProvince) return ''
  const candidates = geoNames?.length ? geoNames : Object.keys(PROVINCE_ADCODE)
  if (candidates.includes(dataProvince)) return dataProvince
  const dataShort = toGeoRegionName(dataProvince)
  const hit = candidates.find((g) => toGeoRegionName(g) === dataShort)
  return hit || dataProvince
}

/** GeoJSON 地级标准名称与别名（自动生成，与后端 geo_city_data.py 一致） */
import { CITY_GEO_ALIASES, GEOJSON_CITY_NAMES } from './geoCityData'

/** 将数据中的市名匹配到 GeoJSON 中的名称 */
export function matchCityGeoName(dataCity: string, geoNames: string[]): string {
  if (!dataCity) return ''
  if (geoNames.includes(dataCity)) return dataCity
  if (GEOJSON_CITY_NAMES.has(dataCity)) return dataCity

  const resolved =
    CITY_GEO_ALIASES[dataCity] || CITY_GEO_ALIASES[dataCity.replace(/市$/, '')]

  if (resolved && (!geoNames.length || geoNames.includes(resolved))) return resolved

  const shortName = dataCity.replace(/市$/, '')
  const hit = geoNames.find((g) => g === shortName || g.replace(/市$/, '') === shortName)
  if (hit) return hit

  return resolved || dataCity
}
