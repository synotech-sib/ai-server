# modules/engine.py
from config.physics_cfg import DEFAULT_NP_RATIO

def calculate_battery_specs(loading, capacity, area, np_ratio=DEFAULT_NP_RATIO):
    areal_capacity = (loading * capacity) / 1000
    total_capacity = areal_capacity * area
    required_anode = areal_capacity * np_ratio
    
    return {
        "areal_capacity": round(areal_capacity, 3),
        "total_capacity": round(total_capacity, 2),
        "required_anode": round(required_anode, 3)
    }
