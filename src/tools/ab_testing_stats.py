"""
Statistical Analysis for A/B Testing

통계적 유의성 검증을 위한 도구들을 제공합니다.
"""

from typing import List, Dict, Any
import math


def calculate_mean(values: List[float]) -> float:
    """평균 계산"""
    if not values:
        return 0.0
    return sum(values) / len(values)


def calculate_variance(values: List[float]) -> float:
    """분산 계산"""
    if len(values) < 2:
        return 0.0
    
    mean = calculate_mean(values)
    return sum((x - mean) ** 2 for x in values) / (len(values) - 1)


def calculate_std_dev(values: List[float]) -> float:
    """표준편차 계산"""
    return math.sqrt(calculate_variance(values))


def t_test(group_a: List[float], group_b: List[float]) -> Dict[str, float]:
    """
    독립 표본 t-검정
    
    Args:
        group_a: 그룹 A의 값들
        group_b: 그룹 B의 값들
    
    Returns:
        t-통계량, p-value (근사값)
    """
    if len(group_a) < 2 or len(group_b) < 2:
        return {'t_statistic': 0.0, 'p_value': 1.0, 'significant': False}
    
    mean_a = calculate_mean(group_a)
    mean_b = calculate_mean(group_b)
    
    var_a = calculate_variance(group_a)
    var_b = calculate_variance(group_b)
    
    n_a = len(group_a)
    n_b = len(group_b)
    
    # Pooled standard error
    pooled_se = math.sqrt(var_a / n_a + var_b / n_b)
    
    if pooled_se == 0:
        return {'t_statistic': 0.0, 'p_value': 1.0, 'significant': False}
    
    # t-통계량
    t_statistic = (mean_a - mean_b) / pooled_se
    
    # 자유도
    df = n_a + n_b - 2
    
    # p-value 근사 (간단한 구현)
    # 실제로는 scipy.stats.t.cdf를 사용해야 하지만, 의존성을 줄이기 위해 근사값 사용
    p_value = approximate_p_value(abs(t_statistic), df)
    
    return {
        't_statistic': t_statistic,
        'p_value': p_value,
        'significant': p_value < 0.05,
        'mean_difference': mean_a - mean_b,
        'effect_size': (mean_a - mean_b) / math.sqrt((var_a + var_b) / 2) if (var_a + var_b) > 0 else 0
    }


def approximate_p_value(t: float, df: int) -> float:
    """
    t-통계량에 대한 p-value 근사
    
    간단한 근사 공식 사용 (정확하지 않음, scipy 사용 권장)
    """
    # 매우 간단한 근사: t > 2면 유의, t > 3이면 매우 유의
    if abs(t) < 1.96:
        return 0.1  # 유의하지 않음
    elif abs(t) < 2.58:
        return 0.05  # 경계선
    elif abs(t) < 3.29:
        return 0.01  # 유의
    else:
        return 0.001  # 매우 유의


def chi_square_test(observed: List[int], expected: List[int]) -> Dict[str, float]:
    """
    카이제곱 검정
    
    Args:
        observed: 관측 빈도
        expected: 기대 빈도
    
    Returns:
        카이제곱 통계량, p-value (근사값)
    """
    if len(observed) != len(expected):
        raise ValueError("Observed and expected must have same length")
    
    chi_square = 0.0
    for obs, exp in zip(observed, expected):
        if exp > 0:
            chi_square += ((obs - exp) ** 2) / exp
    
    # 자유도
    df = len(observed) - 1
    
    # p-value 근사
    p_value = approximate_chi_square_p_value(chi_square, df)
    
    return {
        'chi_square': chi_square,
        'p_value': p_value,
        'significant': p_value < 0.05
    }


def approximate_chi_square_p_value(chi_square: float, df: int) -> float:
    """카이제곱 p-value 근사"""
    # 매우 간단한 근사
    critical_values = {
        1: 3.841,
        2: 5.991,
        3: 7.815,
        4: 9.488
    }
    
    critical = critical_values.get(df, 9.488)
    
    if chi_square < critical:
        return 0.1
    elif chi_square < critical * 1.5:
        return 0.05
    else:
        return 0.01


def calculate_confidence_interval(
    values: List[float],
    confidence_level: float = 0.95
) -> Dict[str, float]:
    """
    신뢰구간 계산
    
    Args:
        values: 값들
        confidence_level: 신뢰수준 (기본 95%)
    
    Returns:
        평균, 하한, 상한
    """
    if len(values) < 2:
        mean = calculate_mean(values)
        return {'mean': mean, 'lower': mean, 'upper': mean}
    
    mean = calculate_mean(values)
    std_dev = calculate_std_dev(values)
    n = len(values)
    
    # t-분포 임계값 (근사)
    t_critical = 1.96 if confidence_level == 0.95 else 2.58
    
    margin_of_error = t_critical * (std_dev / math.sqrt(n))
    
    return {
        'mean': mean,
        'lower': mean - margin_of_error,
        'upper': mean + margin_of_error,
        'margin_of_error': margin_of_error
    }
