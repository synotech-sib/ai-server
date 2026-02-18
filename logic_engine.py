# logic_engine.py
# Lead Architect: Woo-seok Choi (CEO)
# Implementation: Seo-yeon Choi & Gemini

import numpy as np

def calculate_battery_specs(loading, spec_capacity, area, np_ratio_target):
    """
    최우석 대표님의 SIB 물리 엔진: 
    Loading(mg/cm2)과 Spec. Capacity(mAh/g)를 기반으로 
    Design Capacity 및 필요 음극 용량을 계산합니다.
    """
    # 1. 양극 용량 (Capacity per unit area) 계산
    # 공식: Loading * Spec_Capacity / 1000
    areal_capacity = (loading * spec_capacity) / 1000  # mAh/cm2
    
    # 2. 총 용량 (Total Design Capacity)
    total_capacity = areal_capacity * area  # mAh
    
    # 3. N/P Ratio에 따른 음극 필요 용량 설계
    # 공식: 양극 용량 * 목표 N/P Ratio
    required_anode_capacity = areal_capacity * np_ratio_target  # mAh/cm2
    
    return {
        "areal_capacity": round(areal_capacity, 4),
        "total_capacity": round(total_capacity, 2),
        "required_anode": round(required_anode_capacity, 4)
    }

def validate_input(value, min_val, max_val):
    """실측 데이터 유효성 검사 로직"""
    if min_val <= value <= max_val:
        return True
    return False