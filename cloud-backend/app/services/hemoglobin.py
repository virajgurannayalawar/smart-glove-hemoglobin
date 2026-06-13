# app/services/hemoglobin.py
from typing import Any

def is_anemic(hb_level: float, age: int, gender: str, is_pregnant: bool = False) -> bool:
    gender_lower = (gender or "").lower()
    if is_pregnant:
        return hb_level < 11.0
    if age < 5:
        return hb_level < 11.0
    if age < 12:
        return hb_level < 11.5
    if age < 15:
        return hb_level < 12.0
    if gender_lower in ("male", "m"):
        return hb_level < 13.0
    return hb_level < 12.0