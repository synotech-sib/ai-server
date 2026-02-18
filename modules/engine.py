# modules/engine.py
from config.physics_cfg import DEFAULT_NP_RATIO, NOMINAL_VOLTAGE

def calculate_battery_specs(loading, capacity, area, np_ratio=DEFAULT_NP_RATIO):
    # 기존 계산
    areal_capacity = (loading * capacity) / 1000
    total_capacity = areal_capacity * area
    required_anode = areal_capacity * np_ratio
    
    # [Step 7] 에너지 밀도 계산 (단순화 모델: 양극 소재 기준 Specific Energy)
    # Wh/kg = (mAh/g * V) / 1000
    specific_energy = (capacity * NOMINAL_VOLTAGE)
    
    return {
        "areal_capacity": round(areal_capacity, 3),
        "total_capacity": round(total_capacity, 2),
        "required_anode": round(required_anode, 3),
        "specific_energy": round(specific_energy, 1)
    }