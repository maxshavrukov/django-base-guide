from django.db.models import QuerySet

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
            'label': 'Диагональ экрана (дюймы)',
            'type': 'checkbox',
        },
        {
            'param': 'display_refresh_rate',
            'field': 'display_refresh_rate',
            'label': 'Частота обновления (Гц)',
            'type': 'checkbox',
        },
        {
            'param': 'processor',
            'field': 'processor',
            'label': 'Процессор',
            'type': 'checkbox',
        },
        {
            'param': 'ram',
            'field': 'ram',
            'label': 'Оперативная память (ГБ)',
            'type': 'checkbox',
        },
        {
            'param': 'storage',
            'field': 'storage',
            'label': 'Встроенная память (ГБ)',
            'type': 'checkbox',
        },
        {
            'param': 'nfc_support',
            'field': 'nfc_support',
            'label': 'Поддержка NFC',
            'type': 'boolean',
        },
        {
            'param': 'has_esim',
            'field': 'has_esim',
            'label': 'Поддержка eSIM',
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
            'param': 'headphone_type',
            'field': 'headphone_type',
            'label': 'Тип наушников',
            'type': 'checkbox',
        },
        {
            'param': 'connection_type',
            'field': 'connection_type',
            'label': 'Тип подключения',
            'type': 'checkbox',
        },
        {
            'param': 'has_anc',
            'field': 'has_anc',
            'label': 'Шумоподавление (ANC)',
            'type': 'boolean',
        },
        {
            'param': 'has_microphone',
            'field': 'has_microphone',
            'label': 'Микрофон',
            'type': 'boolean',
        },
    ],
    'chargers': [
        {
            'param': 'brand',
            'field': 'brand__name',
            'label': 'Бренд',
            'type': 'checkbox',
        },
        {
            'param': 'charger_type',
            'field': 'charger_type',
            'label': 'Тип зарядного',
            'type': 'checkbox',
        },
        {
            'param': 'is_gan',
            'field': 'is_gan',
            'label': 'Технология GaN',
            'type': 'boolean',
        },
    ],
    'cables': [
        {
            'param': 'brand',
            'field': 'brand__name',
            'label': 'Бренд',
            'type': 'checkbox',
        },
    ],
    'powerbanks': [
        {
            'param': 'brand',
            'field': 'brand__name',
            'label': 'Бренд',
            'type': 'checkbox',
        },
        {
            'param': 'has_wireless_charging',
            'field': 'has_wireless_charging',
            'label': 'Беспроводная зарядка',
            'type': 'boolean',
        },
        {
            'param': 'has_magsafe',
            'field': 'has_magsafe',
            'label': 'Поддержка MagSafe',
            'type': 'boolean',
        },
    ],
}


def get_category_filter_options(category_slug: str, base_queryset: QuerySet, request_get=None) -> list[dict]:
    """Возвращает список доступных фильтров с их возможными значениями из БД."""
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
            values = (
                base_queryset
                .values_list(field_lookup, flat=True)
                .exclude(**{f"{field_lookup}__isnull": True})
                .distinct()
                .order_by(field_lookup)
            )

            selected_values = request_get.getlist(param_name) if hasattr(request_get, 'getlist') else []

            # Автоматически считываем человекочитаемые названия из Choices (если они есть)
            choices_dict = {}
            if '__' not in field_lookup and hasattr(base_queryset.model, '_meta'):
                try:
                    model_field = base_queryset.model._meta.get_field(field_lookup)
                    if model_field.choices:
                        choices_dict = dict(model_field.choices)
                except Exception:
                    pass

            options = []
            for val in values:
                if val is None or str(val).strip() == '':
                    continue
                
                # Использование понятного пользователю текста вместо сырых ключей БД
                display_label = choices_dict.get(val, str(val))
                if param_name in ('storage_gb', 'ram_gb'):
                    display_label = f"{val} ГБ"

                options.append({
                    'value': str(val),
                    'label': str(display_label),
                    'selected': str(val) in selected_values
                })

            if options:
                filters_data.append({
                    'param': param_name,
                    'label': config['label'],
                    'type': 'checkbox',
                    'options': options,
                })

    return filters_data


def apply_category_filters(queryset: QuerySet, category_slug: str, request_get) -> QuerySet:
    """Применяет специфичные фильтры категории к переданному QuerySet."""
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
            values = [v for v in request_get.getlist(param) if v != '']
            if values:
                queryset = queryset.filter(**{f"{field_lookup}__in": values})

    return queryset