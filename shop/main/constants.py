from .models import Cable, Charger, Headphone, PowerBank, Smartphone


# Единственный источник истины для типов товаров в каталоге.
# Формат: (slug, отображаемое имя, concrete-модель Django).
PRODUCT_CATEGORIES = (
    ("smartphones", "Смартфоны", Smartphone),
    ("headphones", "Наушники", Headphone),
    ("chargers", "Зарядные устройства", Charger),
    ("cables", "Кабели", Cable),
    ("powerbanks", "Повербанки", PowerBank),
)

CATEGORY_BY_SLUG = {slug: (name, model) for slug, name, model in PRODUCT_CATEGORIES}
CATEGORY_BY_MODEL_NAME = {
    model._meta.model_name: (slug, name, model)
    for slug, name, model in PRODUCT_CATEGORIES
}
