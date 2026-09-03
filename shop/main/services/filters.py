from django.db.models import QuerySet


# 1. Карта специфичных полей для каждой категории.
CATEGORY_FILTER_FIELDS = {
    'smartphones': [
        {
            'param': 'brand',
            'field': 'brand__name',
            'label': 'Бренд',
            'type': 'checkbox',
        },
        {
            'param': 'operating_system',
            'field': 'operating_system',
            'label': 'Операционная система',
            'type': 'checkbox',
        },
        {
            'param': 'display_type',
            'field': 'display_type',
            'label': 'Тип экрана',
            'type': 'checkbox',
        },
        {   
            'param': 'display_size',
            'field': 'display_size',
            'label': 'Размер экрана',
            'type': 'checkbox',
        },
        {
            'param': 'display_resolution',
            'field': 'display_resolution',
            'label': 'Разрешение экрана',
            'type': 'checkbox',
        },
        {
            'param': 'display_refresh_rate',
            'field': 'display_refresh_rate',
            'label': 'Частота обновления экрана',
            'type': 'checkbox',
        },
        {
            'param': 'processor',
            'field': 'processor',
            'label': 'Процессор',
            'type': 'checkbox',
        },
        {
            'param': 'core_count',
            'field': 'core_count',
            'label': 'Количество ядер',
            'type': 'checkbox',
        },
        {
            'param': 'ram',
            'field': 'ram',
            'label': 'Оперативная память (RAM)',
            'type': 'checkbox',
        },
        {
            'param': 'storage',
            'field': 'storage',
            'label': 'Встроенная память (Storage)',
            'type': 'checkbox',
        },
        {
            'param': 'extra_storage',
            'field': 'extra_storage',
            'label': 'Дополнительная память',
            'type': 'checkbox',
        },
        {
            'param': 'nfc_support',
            'field': 'nfc_support',
            'label': 'Поддержка NFC',
            'type': 'boolean',
        },
    ],
    'headphones': [
        {
            'param': 'brand',
            'field': 'brand__name',
            'label': 'Бренд',
            'type': 'checkbox',
        },
        {
            'param': 'connection_type',
            'field': 'connection_type',
            'label': 'Тип подключения',
            'type': 'checkbox',
        },
        {
            'param': 'noise_cancellation',
            'field': 'noise_cancellation',
            'label': 'Шумоподавление (ANC)',
            'type': 'boolean',
        },
        {
            'param': 'bluetooth_version',
            'field': 'bluetooth_version',
            'label': 'Версия Bluetooth',
            'type': 'checkbox',
        },
    ],
    'chargers': [
        {
            'param': 'fast_charging',
            'field': 'fast_charging',
            'label': 'Быстрая зарядка',
            'type': 'boolean',
        },
    ],
    'cables': [],
    'powerbanks': [
        {
            'param': 'fast_charging',
            'field': 'fast_charging',
            'label': 'Быстрая зарядка',
            'type': 'boolean',
        },
    ],
}


def get_category_filter_options(category_slug: str, base_queryset: QuerySet, request_get=None) -> list[dict]:
    """
    Возвращает список доступных фильтров с их возможными значениями из БД.
    Если передан request_get, отмечается выбранное состояние (selected).
    """
    field_configs = CATEGORY_FILTER_FIELDS.get(category_slug, [])
    filters_data = []
    request_get = request_get or {}

    for config in field_configs:
        field_lookup = config['field']
        param_name = config['param']

        if config['type'] == 'boolean':
            current_val = request_get.get(param_name, '')
            filters_data.append({
                'param': param_name,
                'label': config['label'],
                'type': 'boolean',
                'options': [
                    {'value': '1', 'label': 'Да', 'selected': current_val == '1'},
                    {'value': '0', 'label': 'Нет', 'selected': current_val == '0'},
                ]
            })
        else:
            # Безопасно исключаем NULL из БД без сравнения с пустой строкой ''
            values = (
                base_queryset
                .values_list(field_lookup, flat=True)
                .exclude(**{f"{field_lookup}__isnull": True})
                .distinct()
                .order_by(field_lookup)
            )

            selected_values = request_get.getlist(param_name) if hasattr(request_get, 'getlist') else []

            # Исключаем None и пустые строки на уровне Python
            options = [
                {
                    'value': str(val),
                    'label': str(val),
                    'selected': str(val) in selected_values
                }
                for val in values if val is not None and str(val).strip() != ''
            ]

            if options:
                filters_data.append({
                    'param': param_name,
                    'label': config['label'],
                    'type': 'checkbox',
                    'options': options,
                })

    return filters_data


def apply_category_filters(queryset: QuerySet, category_slug: str, request_get) -> QuerySet:
    """
    Применяет специфичные фильтры категории к переданному QuerySet.
    """
    field_configs = CATEGORY_FILTER_FIELDS.get(category_slug, [])

    for config in field_configs:
        param = config['param']
        field_lookup = config['field']
        filter_type = config.get('type', 'checkbox')

        if filter_type == 'boolean':
            val = request_get.get(param)
            if val == '1':
                queryset = queryset.filter(**{field_lookup: True})
            elif val == '0':
                queryset = queryset.filter(**{field_lookup: False})

        else:
            # Отфильтровываем пустые строки из GET-параметров
            values = [v for v in request_get.getlist(param) if v != '']
            if values:
                queryset = queryset.filter(**{f"{field_lookup}__in": values})

    return queryset