"""
Shared season inference utilities.
Centralized to prevent duplication across predictors.
"""

def infer_season(temperature: float) -> int:
    """
    Infer season from temperature.
    
    Args:
        temperature: Temperature in Celsius
        
    Returns:
        0 for Kharif (summer, >=28°C)
        1 for Rabi (winter, <=22°C)  
        2 for Zaid (spring, 22-28°C)
    """
    if temperature >= 28:
        return 0  # Kharif
    if temperature <= 22:
        return 1  # Rabi
    return 2  # Zaid


def get_season_name(season_code: int) -> str:
    """Get season name from code."""
    season_names = ["Kharif", "Rabi", "Zaid"]
    return season_names[season_code] if 0 <= season_code <= 2 else "Unknown"
