# exercise.py
# Программа для новичков: проверяет число и выводит базовую информацию

def analyze_number(n):
    """Возвращает словарь с простой информацией о числе."""
    if n > 0:
        sign = "positive"
    else:
        sign = "non-positive"
    return {"value": n, "sign": sign}

if __name__ == "__main__":
    sample = 5
    info = analyze_number(sample)
    print("Input:", sample)
    print("Info:", info)