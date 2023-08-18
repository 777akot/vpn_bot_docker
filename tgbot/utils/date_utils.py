def format_duration(input_str):
    num, unit = int(input_str[:-1]), input_str[-1]

    units = {
        'd': ('день', 'дня', 'дней'),
        'w': ('неделя', 'недели', 'недель'),
        'm': ('месяц', 'месяца', 'месяцев')
    }

    unit_str = units.get(unit)
    if unit_str:
        index = 0 if num == 1 else 1 if 2 <= num <= 4 else 2
        return f"{num} {unit_str[index]}"
    else:
        print(f'ERROR: Некорректный формат')
        return None