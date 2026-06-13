def evaluate_bin(fill):

    if fill >= 80:
        return "OVERFLOW"

    elif fill >= 50:
        return "MODERATE"

    else:
        return "NORMAL"
