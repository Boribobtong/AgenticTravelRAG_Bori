# Region settings for HotelRAGAgent
# Each region defines price keyword groups and optional native name handling.

from dataclasses import dataclass
from typing import Dict, List

@dataclass
class RegionSettings:
    """지역별 설정"""
    price_keywords: Dict[str, List[str]]  # keys: high_name, low_name, high, low
    use_native_name_for_search: bool = False
    native_name_field: str = "kor_name"  # default field name for native hotel name

# 기본(전역) 설정 – 영어권 국가에 적용
DEFAULT = RegionSettings(
    price_keywords={
        "high_name": [
            "luxury", "grand", "plaza", "ritz", "four seasons", "intercontinental",
            "signiel", "shilla", "conrad", "sofitel", "fairmont", "jw marriott",
            "hyatt", "hilton", "sheraton", "westin"
        ],
        "low_name": ["inn", "hostel", "guesthouse", "motel", "residence", "stay", "youth"],
        "high": [
            "luxury", "expensive", "premium", "high-end", "upscale", "fancy",
            "top notch", "world class", "5 star", "five star"
        ],
        "low": [
            "budget", "cheap", "affordable", "hostel", "guesthouse",
            "value for money", "economical", "basic", "simple"
        ],
    },
    use_native_name_for_search=False,
)

# 한국(Seoul) 전용 설정 – 한국어 이름을 검색에 사용
KOREA = RegionSettings(
    price_keywords=DEFAULT.price_keywords,
    use_native_name_for_search=True,
    native_name_field="kor_name",
)

# 일본(예: Tokyo) 전용 설정 – 일본어 이름 사용 예시
JAPAN = RegionSettings(
    price_keywords=DEFAULT.price_keywords,
    use_native_name_for_search=True,
    native_name_field="jpn_name",
)

# 미국(예: New York, Los Angeles) 전용 설정 – 기본 영어 사용
USA = RegionSettings(
    price_keywords=DEFAULT.price_keywords,
    use_native_name_for_search=False,
)

# 매핑: city name -> RegionSettings
REGION_MAP = {
    "Seoul": KOREA,
    "Tokyo": JAPAN,
    "New York": USA,
    "Los Angeles": USA,
    # 필요 시 추가
}
