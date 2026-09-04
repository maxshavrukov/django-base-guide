
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


def _get_storage_val(instance):
    """Вспомогательный метод для получения текстового отображения объёма памяти."""
    if instance is None:
        return None
    if hasattr(instance, 'storage_display'):
        return instance.storage_display
    if hasattr(instance, 'storage_gb') and instance.storage_gb:
        return f"{instance.storage_gb} ГБ"
    return getattr(instance, 'storage', None)


def _get_concrete_model(product):
    from main.services.categories import get_product_model
    return get_product_model(product)


def get_product_variants(product) -> tuple[list, list]:
    """Формирует варианты только внутри группы и concrete-типа текущего товара."""
    if not product.group_id:
        return [], []

    concrete_model = _get_concrete_model(product)

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

    # Достаем concrete-экземпляр текущего товара из списка group_products по PK
    current_concrete = next((i for i in group_products if i.pk == product.pk), product)

    # Считываем память с concrete-объекта (у него есть storage_gb / storage_display)
    current_storage = _get_storage_val(current_concrete)
    current_color = getattr(current_concrete, 'color', None)

    storages_seen = []
    for item in group_products:
        st = _get_storage_val(item)
        if st and st not in storages_seen:
            storages_seen.append(st)

    storage_variants = []
    for st in storages_seen:
        target = next(
            (i for i in group_products if getattr(i, 'color', None) == current_color and _get_storage_val(i) == st),
            None,
        ) or next(
            (i for i in group_products if _get_storage_val(i) == st),
            None,
        )
        if target:
            storage_variants.append({
                'value': st,
                'product': target,
                'is_active': st == current_storage,
            })

    colors_seen = []
    for item in group_products:
        color = getattr(item, 'color', None)
        if color and color not in colors_seen:
            colors_seen.append(color)

    color_variants = []
    for color in colors_seen:
        target = next(
            (i for i in group_products if _get_storage_val(i) == current_storage and getattr(i, 'color', None) == color),
            None,
        ) or next(
            (i for i in group_products if getattr(i, 'color', None) == color),
            None,
        )
        if target:
            color_variants.append({
                'value': color,
                'product': target,
                'is_active': color == current_color,
            })

    return storage_variants, color_variants

def get_related_products(product) -> list:
    """Возвращает последние активные товары того же concrete-типа."""
    concrete_model = _get_concrete_model(product)
    if not concrete_model:
        return []

    return list(
        concrete_model.objects
        .filter(available=True)
        .exclude(pk=product.pk)
        .select_related('brand', 'group')
        .order_by('-id')[:4]
    )
