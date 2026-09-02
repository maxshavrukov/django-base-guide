from django.db.models import Q
from main.constants import PRODUCT_CATEGORIES

# Карта раскладки клавиатуры (RU/UA -> EN)
LAYOUT_MAPPING = {
    # Нижний регистр
    'й': 'q', 'ц': 'w', 'у': 'e', 'к': 'r', 'е': 't', 'н': 'y', 'г': 'u', 'ш': 'i', 'щ': 'o', 'з': 'p',
    'х': '[', 'ъ': ']', 'ї': ']', 'ф': 'a', 'ы': 's', 'і': 's', 'в': 'd', 'а': 'f', 'п': 'g', 'р': 'h',
    'о': 'j', 'л': 'k', 'д': 'l', 'ж': ';', 'э': "'", 'є': "'", 'я': 'z', 'ч': 'x', 'с': 'c', 'м': 'v',
    'и': 'b', 'т': 'n', 'ь': 'm', 'б': ',', 'ю': '.', 'ё': '`', 'ґ': '\\',
    # Верхний регистр
    'Й': 'Q', 'Ц': 'W', 'У': 'E', 'К': 'R', 'Е': 'T', 'Н': 'Y', 'Г': 'U', 'Ш': 'I', 'Щ': 'O', 'З': 'P',
    'Х': '{', 'Ъ': '}', 'Ї': '}', 'Ф': 'A', 'Ы': 'S', 'І': 'S', 'В': 'D', 'А': 'F', 'П': 'G', 'Р': 'H',
    'О': 'J', 'Л': 'K', 'Д': 'L', 'Ж': ':', 'Э': '"', 'Є': '"', 'Я': 'Z', 'Ч': 'X', 'С': 'C', 'М': 'V',
    'И': 'B', 'Т': 'N', 'Ь': 'M', 'Б': '<', 'Ю': '>', 'Ё': '~', 'Ґ': '|',
}

RU_TO_EN_LAYOUT = str.maketrans(LAYOUT_MAPPING)

# Фонетическая транслитерация (Кириллица -> Латиница)
CYR_TO_LAT_MAP = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'zh',
    'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
    'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts',
    'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu',
    'я': 'ya', 'і': 'i', 'ї': 'yi', 'є': 'ye', 'ґ': 'g'
}


def _transliterate_cyr_to_lat(text: str) -> str:
    """Преобразует кириллицу в латиницу: 'самсунг' -> 'samsung'."""
    return "".join(CYR_TO_LAT_MAP.get(char, char) for char in text.lower())


def search_products(query: str) -> list:
    """
    Выполняет поиск товаров по прямому запросу, фонетической латинице 
    и смене раскладки клавиатуры.
    """
    query = (query or '').strip()
    if not query:
        return []

    def _execute_search(q_text: str) -> list:
        conditions = (
            Q(name__icontains=q_text)
            | Q(description__icontains=q_text)
            | Q(brand__name__icontains=q_text)
        )
        results = []
        for _, _, model in PRODUCT_CATEGORIES:
            results.extend(
                model.objects.filter(available=True)
                .filter(conditions)
                .select_related('brand', 'group')
            )
        return results

    # 1. Прямой поиск
    products = _execute_search(query)
    if products:
        return products

    # 2. Поиск по фонетической латинице ("самсунг" -> "samsung")
    lat_query = _transliterate_cyr_to_lat(query)
    if lat_query != query:
        products = _execute_search(lat_query)
        if products:
            return products

    # 3. Поиск по смене раскладки клавиатуры ("cfvceyu" -> "самсунг")
    layout_query = query.translate(RU_TO_EN_LAYOUT)
    if layout_query not in (query, lat_query):
        products = _execute_search(layout_query)

    return products