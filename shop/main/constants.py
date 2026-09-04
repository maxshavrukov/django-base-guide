from .models import Cable, Charger, Headphone, PowerBank, Smartphone


# Реестр concrete-типов товаров. Это НЕ список всех пользовательских категорий.
# Формат: (slug, отображаемое имя, concrete-модель Django).
PRODUCT_TYPES = (
    ("smartphones", "Смартфоны", Smartphone),
    ("headphones", "Наушники", Headphone),
    ("chargers", "Зарядные устройства", Charger),
    ("cables", "Кабели", Cable),
    ("powerbanks", "Повербанки", PowerBank),
)

PRODUCT_CATEGORIES = PRODUCT_TYPES
PRODUCT_TYPE_BY_SLUG = {slug: (name, model) for slug, name, model in PRODUCT_TYPES}
CATEGORY_BY_MODEL_NAME = {
    model._meta.model_name: (slug, name, model)
    for slug, name, model in PRODUCT_TYPES
}
