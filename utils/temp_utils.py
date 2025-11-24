

ROAST_STAGES = ["City", "City+", "Full City", "Full City+", "Vienna"]
ROAST_TEMPS = [422, 432, 441, 450, 463]  # °F

ROAST_EVENTS = ["1st Crack Start", "2nd Crack Start"]


def c_to_f(temp: float) -> float:
    """Convert celsius to fahrenheit"""
    return temp * 9/5 + 32

def f_to_c(temp: float) -> float:
    """Convert fahrenheit to celsius"""
    return (temp - 32) * 5/9
