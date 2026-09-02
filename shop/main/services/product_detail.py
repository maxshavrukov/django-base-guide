from main.constants import CATEGORY_BY_SLUG


def update_recently_viewed(request, product_id: int) -> None:
    """Обновляет список просмотренных товаров в сессии пользователя."""
    recently_viewed = request.session.get('recently_viewed', [])
    recently_viewed = [p_id for p_id in recently_viewed if p_id != product_id]
    recently_viewed.insert(0, product_id)
    request.session['recently_viewed'] = recently_viewed[:4]
    request.session.modified = True


def get_product_gallery(product) -> list[dict]:
    """Собирает список изображений товара для слайдера."""
    gallery = []
    if product.image:
        gallery.append({'url': product.image.url, 'alt': product.name, 'is_primary': True})

    for image in product.images.all():
        if image.image:
            gallery.append({'url': image.image.url, 'alt': product.name, 'is_primary': False})

    return gallery


def get_product_variants(product, category_slug: str) -> tuple[list, list]:
    """Формирует списки доступных вариантов объёма памяти и цвета."""
    if not product.group_id:
        return [], []

    concrete_model = None
    current_storage = None

    if category_slug and category_slug in CATEGORY_BY_SLUG:
        concrete_model = CATEGORY_BY_SLUG[category_slug][1]
        relation_name = concrete_model._meta.model_name
        concrete_instance = getattr(product, relation_name, product)
        current_storage = getattr(concrete_instance, 'storage', None)

    if concrete_model:
        group_products = list(
            concrete_model.objects
            .filter(group=product.group, available=True)
            .select_related('brand', 'group')
        )
    else:
        group_products = list(
            product.group.products
            .filter(available=True)
            .select_related('brand', 'group')
        )

    current_color = getattr(product, 'color', None)

    # 1. Варианты встроенной памяти
    storages_seen = []
    for item in group_products:
        st = getattr(item, 'storage', None)
        if st and st not in storages_seen:
            storages_seen.append(st)

    storage_variants = []
    for st in storages_seen:
        target = next((i for i in group_products if getattr(i, 'color', None) == current_color and getattr(i, 'storage', None) == st), None) \
              or next((i for i in group_products if getattr(i, 'storage', None) == st), None)
        if target:
            storage_variants.append({
                'value': st,
                'product': target,
                'is_active': (st == current_storage),
            })

    # 2. Варианты цвета
    colors_seen = []
    for item in group_products:
        c = getattr(item, 'color', None)
        if c and c not in colors_seen:
            colors_seen.append(c)

    color_variants = []
    for c in colors_seen:
        target = next((i for i in group_products if getattr(i, 'storage', None) == current_storage and getattr(i, 'color', None) == c), None) \
              or next((i for i in group_products if getattr(i, 'color', None) == c), None)
        if target:
            color_variants.append({
                'value': c,
                'product': target,
                'is_active': (c == current_color),
            })

    return storage_variants, color_variants


def get_related_products(product, category_slug: str) -> list:
    """Возвращает список похожих товаров из той же категории."""
    if not category_slug or category_slug not in CATEGORY_BY_SLUG:
        return []

    concrete_model = CATEGORY_BY_SLUG[category_slug][1]
    return list(
        concrete_model.objects
        .filter(available=True)
        .exclude(pk=product.pk)
        .select_related('brand', 'group')
        .order_by('-id')[:4]
    )