def transliterate_to_cyrillic(text):
    """Простая функция перевода латиницы в кириллицу"""
    translit_map = {
        'shch': 'щ', 'zh': 'ж', 'ch': 'ч', 'sh': 'ш', 'yu': 'ю', 'ya': 'я',
        'a': 'а', 'b': 'б', 'v': 'в', 'g': 'г', 'd': 'д', 'e': 'е', 'z': 'з',
        'i': 'і', 'j': 'й', 'k': 'к', 'l': 'л', 'm': 'м', 'n': 'н', 'o': 'о',
        'p': 'п', 'r': 'р', 's': 'с', 't': 'т', 'u': 'у', 'f': 'ф', 'h': 'х',
        'c': 'ц', 'y': 'ы'
    }
    # Сортируем ключи по длине (сначала длинные вроде shch, ch), чтобы заменялось корректно
    sorted_keys = sorted(translit_map.keys(), key=len, reverse=True)
    res = text.lower()
    for k in sorted_keys:
        res = res.replace(k, translit_map[k])
    return res
