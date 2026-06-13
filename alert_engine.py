def evaluate_status(fill_level):
    if fill_level >= 85:
        return "High Alert"
    elif fill_level >= 60:
        return "Medium"
    return "Normal"
