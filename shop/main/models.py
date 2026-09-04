from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Бренд")
    slug = models.SlugField(max_length=100, unique=True)
    logo = models.FileField(
        upload_to="brands/", 
        blank=True, 
        null=True, 
        verbose_name="Логотип (SVG/PNG)"
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Бренд'
        verbose_name_plural = 'Бренды'

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse("main:product_list_by_brand", args=[self.slug])

class Category(models.Model):
    class ProductType(models.TextChoices):
        SMARTPHONE = 'smartphone', 'Смартфоны'
        HEADPHONE = 'headphone', 'Наушники'
        CHARGER = 'charger', 'Зарядные устройства'
        CABLE = 'cable', 'Кабели'
        POWERBANK = 'powerbank', 'Повербанки'

    name = models.CharField(max_length=120, unique=True, verbose_name='Название категории')
    slug = models.SlugField(max_length=120, unique=True, verbose_name='Slug (URL)')
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children',
        verbose_name='Родительская категория',
    )
    product_type = models.CharField(
        max_length=20,
        choices=ProductType.choices,
        blank=True,
        verbose_name='Тип товара',
        help_text='Для верхнего уровня обязателен. У подкатегорий можно оставить пустым — тип будет унаследован.',
    )
    sort_order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    is_active = models.BooleanField(default=True, verbose_name='Активна')

    class Meta:
        ordering = ('sort_order', 'name')
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        constraints = [
            models.UniqueConstraint(
                fields=('product_type',),
                condition=Q(parent__isnull=True),
                name='unique_root_category_product_type',
            ),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        if self.parent_id is None and not self.product_type:
            raise ValidationError({'product_type': 'Для верхней категории необходимо указать тип товара.'})

        if self.parent_id and self.product_type:
            inherited_type = self.parent.get_effective_product_type()
            if inherited_type and self.product_type != inherited_type:
                raise ValidationError({'product_type': 'Тип товара подкатегории должен совпадать с типом родительской категории.'})

        if self.parent_id and self.parent_id == self.pk:
            raise ValidationError({'parent': 'Категория не может быть родителем самой себя.'})

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or 'category'
            candidate = base_slug
            counter = 2
            while Category.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f'{base_slug}-{counter}'
                counter += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    def get_root(self):
        category = self
        seen = set()
        while category.parent_id and category.id not in seen:
            seen.add(category.id)
            category = category.parent
        return category

    def get_effective_product_type(self):
        category = self
        seen = set()
        while category and category.id not in seen:
            seen.add(category.id)
            if category.product_type:
                return category.product_type
            category = category.parent
        return None

    def get_absolute_url(self):
        return reverse('main:product_list_by_category', args=[self.slug])


class ProductGroup(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название серии / линейки")
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True, verbose_name="Slug (URL)")
    categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name='product_groups',
        verbose_name='Подкатегории',
        help_text='Выберите одну или несколько подкатегорий. Верхние категории определяются типом товара.',
    )

    class Meta:
        verbose_name = "Группа товаров"
        verbose_name_plural = "Группы товаров"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("main:product_list_by_group", args=[self.slug])

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "group"
            candidate = base_slug
            counter = 2
            while ProductGroup.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base_slug}-{counter}"
                counter += 1
            self.slug = candidate
        super().save(*args, **kwargs)

# Базовый класс для ВСЕХ товаров (общие поля)
class Product(models.Model):
    brand = models.ForeignKey(Brand, related_name='products', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Бренд")
    name = models.CharField(max_length=150, db_index=True, verbose_name="Название товара")
    slug = models.SlugField(max_length=150, unique=True)
    image = models.ImageField(upload_to='products/%Y/%m/%d', blank=True, verbose_name="Изображение")
    description = CKEditor5Field('Описание', config_name='extends', blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True, verbose_name="Цвет")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    discount = models.IntegerField(
        default=0,
        blank=True,
        null=True,
        verbose_name="Скидка (%)",
        help_text="Скидка от 0 до 100 процентов.",
    )
    stock = models.PositiveIntegerField(default=0, verbose_name="Количество на складе")
    available = models.BooleanField(default=True, verbose_name="Доступно")

    group = models.ForeignKey(
        ProductGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name="Группа товаров",
        help_text="Выберите серию, к которой относится данный товар"
    )
    color_code = models.CharField(
        max_length=7,
        blank=True,
        verbose_name="HEX-код цвета",
        help_text="Например: #000000 для черного, #FFFFFF для белого"
    )

    def __str__(self):
        return self.name

    @property
    def discount_percent(self):
        return max(0, min(int(self.discount or 0), 100))

    def get_discounted_price(self):
        if not self.price:
            return Decimal("0.00")
        percent = Decimal(self.discount_percent)
        value = self.price * (Decimal("100") - percent) / Decimal("100")
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def get_discount_amount(self):
        return (self.price - self.get_discounted_price()).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    @property
    def category_name(self):
        mapping = {
            "smartphone": "Смартфоны",
            "headphone": "Наушники",
            "charger": "Зарядные устройства",
            "cable": "Кабели",
            "powerbank": "Повербанки",
        }
        model_name = self.__class__.__name__.lower()
        if model_name in mapping:
            return mapping[model_name]

        for relation_name, label in mapping.items():
            try:
                getattr(self, relation_name)
                return label
            except ObjectDoesNotExist:
                continue
        return "Товары"

    def get_variants(self):
        "Возвращает все активные товары из текущей группы"
        if self.group:
            return self.group.products.filter(available=True)
        return Product.objects.none()

    def get_absolute_url(self):
        return reverse('main:product_detail', args=[self.id, self.slug])


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE, verbose_name="Товар")
    image = models.ImageField(upload_to='products/gallery/%Y/%m/%d', verbose_name="Фотография")

    class Meta:
        verbose_name = 'Фотография товара'
        verbose_name_plural = 'Фотографии товара'

    def __str__(self):
        return f"Фото для {self.product.name}"

    
    # ==========================================
    # 1. СМАРТФОНЫ
    # ==========================================
class Smartphone(Product):
    class DisplayType(models.TextChoices):
        AMOLED = 'amoled', 'AMOLED'
        OLED = 'oled', 'OLED'
        IPS = 'ips', 'IPS'
        LTPO = 'ltpo', 'LTPO OLED'

    class VideoResolution(models.TextChoices):
        RES_8K = '8k', '8K UHD (7680x4320)'
        RES_4K = '4k', '4K UHD (3840x2160)'
        RES_FHD = '1080p', 'Full HD (1920x1080)'
        RES_HD = '720p', 'HD (1280x720)'

    class SlotConfig(models.TextChoices):
        SIM_ONLY = 'sim_only', 'Только SIM (без карты памяти)'
        HYBRID = 'hybrid', 'Комбинированный (SIM или MicroSD)'
        DEDICATED = 'dedicated', 'Отдельный (2x SIM + MicroSD)'
        NO_PHYSICAL = 'no_physical', 'Только eSIM'

    class UsbType(models.TextChoices):
        TYPE_C = 'type_c', 'USB Type-C'
        LIGHTNING = 'lightning', 'Lightning'
        MICRO_USB = 'micro_usb', 'Micro-USB'

    class OSChoices(models.TextChoices):
        ANDROID = 'android', 'Android'
        IOS = 'ios', 'iOS'
        OTHER = 'other', 'Другая'

    # ==========================================
    # БЛОК 1: ДИСПЛЕЙ
    # ==========================================
    display_type = models.CharField(
        max_length=20, choices=DisplayType.choices, default=DisplayType.AMOLED, verbose_name="Тип матрицы"
    )
    display_size = models.DecimalField(
        max_digits=3, decimal_places=1, verbose_name="Диагональ (\")", help_text="Например: 6.7"
    )
    display_resolution = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Разрешение", help_text="Например: 2400x1080"
    )
    display_refresh_rate = models.PositiveIntegerField(
        default=60, verbose_name="Частота обновления (Гц)", help_text="60, 90, 120, 144"
    )

    # ==========================================
    # БЛОК 2: ПРОЦЕССОР И ГРАФИКА
    # ==========================================
    processor = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Модель процессора", help_text="Snapdragon 8 Gen 3"
    )
    gpu = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Графический процессор (GPU)", help_text="Adreno 750, Mali-G720"
    )
    core_count = models.PositiveSmallIntegerField(
        default=8, verbose_name="Количество ядер"
    )
    core_speed = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Тактовая частота", help_text="1x3.3 ГГц + 3x3.2 ГГц"
    )

    # ==========================================
    # БЛОК 3: ПАМЯТЬ И СЛОТЫ
    # ==========================================
    ram = models.PositiveIntegerField(
        verbose_name="ОЗУ (ГБ)", help_text="Например: 8, 12, 16"
    )
    storage = models.PositiveIntegerField(
        verbose_name="Встроенная память (ГБ)", help_text="Например: 128, 256, 512, 1024"
    )
    slot_config = models.CharField(
        max_length=20, choices=SlotConfig.choices, default=SlotConfig.SIM_ONLY, verbose_name="Конфигурация слота"
    )
    max_sd_capacity = models.PositiveIntegerField(
        blank=True, null=True, verbose_name="Макс. карта памяти (ГБ)", help_text="Пусто, если SD не поддерживается"
    )

    # ==========================================
    # БЛОК 4: КАМЕРЫ
    # ==========================================
    main_camera_mp = models.PositiveIntegerField(
        verbose_name="Основная камера (Мп)", help_text="Главный модуль для фильтров (например: 50)"
    )
    main_camera_desc = models.CharField(
        max_length=150, blank=True, null=True, verbose_name="Полный блок камер", help_text="50 Мп + 12 Мп + 10 Мп"
    )
    front_camera_mp = models.PositiveIntegerField(
        blank=True, null=True, verbose_name="Фронтальная камера (Мп)", help_text="Например: 32"
    )
    max_video_resolution = models.CharField(
        max_length=20, choices=VideoResolution.choices, default=VideoResolution.RES_4K, verbose_name="Макс. разрешение видео"
    )
    optical_zoom = models.DecimalField(
        max_digits=3, decimal_places=1, blank=True, null=True, verbose_name="Оптический зум (x)", help_text="Например: 3.0, 5.0, 10.0 (пусто, если нет)"
    )

    # ==========================================
    # БЛОК 5: АККУМУЛЯТОР И ЗАРЯДКА
    # ==========================================
    battery_capacity = models.PositiveIntegerField(
        verbose_name="Емкость аккумулятора (мАч)", help_text="Например: 5000"
    )
    charging_power = models.PositiveIntegerField(
        blank=True, null=True, verbose_name="Мощность проводной зарядки (Вт)", help_text="Например: 67"
    )
    has_wireless_charging = models.BooleanField(
        default=False, verbose_name="Беспроводная зарядка"
    )
    has_reverse_charging = models.BooleanField(
        default=False, verbose_name="Реверсивная зарядка", help_text="Зарядка других устройств (наушников/часов) от телефона"
    )

    # ==========================================
    # БЛОК 6: СВЯЗЬ И ИНТЕРФЕЙСЫ
    # ==========================================
    communication_standards = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Стандарты связи", help_text="2G, 3G, 4G, 5G"
    )
    sim_count = models.PositiveSmallIntegerField(
        default=2, verbose_name="Кол-во активных SIM"
    )
    has_esim = models.BooleanField(
        default=False, verbose_name="Поддержка eSIM"
    )
    usb_type = models.CharField(
        max_length=20, choices=UsbType.choices, default=UsbType.TYPE_C, verbose_name="Разъем зарядки"
    )
    nfc_support = models.BooleanField(
        default=False, verbose_name="Поддержка NFC"
    )
    has_jack_3_5 = models.BooleanField(
        default=False, verbose_name="Разъем 3.5 мм"
    )
    wi_fi_standards = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Wi-Fi", help_text="Wi-Fi 6E, Wi-Fi 7"
    )
    bluetooth_version = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Bluetooth", help_text="5.3, 5.4"
    )

    # ==========================================
    # БЛОК 7: КОРПУС И ОС
    # ==========================================
    operating_system = models.CharField(
        max_length=20, choices=OSChoices.choices, default=OSChoices.ANDROID, verbose_name="ОС"
    )
    os_version = models.CharField(
        max_length=30, blank=True, null=True, verbose_name="Версия ОС", help_text="Android 14, iOS 17"
    )
    protection_class = models.CharField(
        max_length=30, blank=True, null=True, verbose_name="Класс защиты", help_text="IP68, IP54"
    )
    material = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Материалы корпуса", help_text="Стекло / металл"
    )

    class Meta:
        verbose_name = 'Смартфон'
        verbose_name_plural = 'Смартфоны'

# ==========================================
# 2. НАУШНИКИ
# ==========================================
class Headphone(Product):
    class HeadphoneType(models.TextChoices):
        TWS = 'tws', 'TWS (полностью беспроводные)'
        IN_EAR = 'in_ear', 'Вкладыши'
        VACUUM = 'vacuum', 'Внутриканальные (вакуумные)'
        ON_EAR = 'on_ear', 'Накладные'
        OVER_EAR = 'over_ear', 'Полноразмерные'

    class ConnectionType(models.TextChoices):
        WIRELESS = 'wireless', 'Беспроводные'
        WIRED = 'wired', 'Проводные'
        COMBINED = 'combined', 'Комбинированные (Bluetooth + кабель)'

    headphone_type = models.CharField(
        max_length=20, choices=HeadphoneType.choices, default=HeadphoneType.TWS, verbose_name="Тип наушников"
    )
    connection_type = models.CharField(
        max_length=20, choices=ConnectionType.choices, default=ConnectionType.WIRELESS, verbose_name="Подключение"
    )

    # Звук и шумоподавление
    has_anc = models.BooleanField(default=False, verbose_name="Активное шумоподавление (ANC)")
    has_transparency_mode = models.BooleanField(default=False, verbose_name="Режим прозрачности")
    audio_codecs = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Поддерживаемые кодеки", help_text="SBC, AAC, aptX, LDAC"
    )

    # Автономность и аккумулятор
    battery_life_hours = models.PositiveSmallIntegerField(
        blank=True, null=True, verbose_name="Время работы без кейса (ч)", help_text="Например: 6"
    )
    total_battery_life_hours = models.PositiveSmallIntegerField(
        blank=True, null=True, verbose_name="Время работы с кейсом (ч)", help_text="Например: 30"
    )
    has_wireless_charging_case = models.BooleanField(
        default=False, verbose_name="Беспроводная зарядка кейса"
    )

    # Физические параметры и функционал
    bluetooth_version = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Версия Bluetooth", help_text="5.3, 5.4"
    )
    has_microphone = models.BooleanField(default=True, verbose_name="Наличие микрофона")
    protection_class = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Класс влагозащиты", help_text="IPX4, IPX7"
    )

    class Meta:
        verbose_name = 'Наушники'
        verbose_name_plural = 'Наушники'

    @property
    def battery_display(self):
        if self.total_battery_life_hours:
            return f"до {self.battery_life_hours} ч (до {self.total_battery_life_hours} ч с кейсом)"
        elif self.battery_life_hours:
            return f"до {self.battery_life_hours} ч"
        return "Не указано"

# ==========================================
# 3. ЗАРЯДНЫЕ УСТРОЙСТВА
# ==========================================
class Charger(Product):
    class ChargerType(models.TextChoices):
        WALL = 'wall', 'Сетевое (в розетку)'
        CAR = 'car', 'Автомобильное'
        WIRELESS_PAD = 'wireless', 'Беспроводная станция/док-станция'

    charger_type = models.CharField(
        max_length=20, choices=ChargerType.choices, default=ChargerType.WALL, verbose_name="Тип зарядного"
    )
    max_power_w = models.PositiveIntegerField(
        verbose_name="Максимальная мощность (Вт)", help_text="Например: 20, 33, 65, 120"
    )

    # Разъемы
    usb_c_ports = models.PositiveSmallIntegerField(default=1, verbose_name="Портов USB Type-C")
    usb_a_ports = models.PositiveSmallIntegerField(default=0, verbose_name="Портов USB-A")

    # Технологии
    is_gan = models.BooleanField(
        default=False, verbose_name="GaN-технология", help_text="Компактный размер и меньший нагрев"
    )
    fast_charging_protocols = models.CharField(
        max_length=150, blank=True, null=True, verbose_name="Протоколы быстрой зарядки", help_text="Power Delivery 3.0, Quick Charge 4.0, PPS"
    )
    has_cable_included = models.BooleanField(default=False, verbose_name="Кабель в комплекте")

    class Meta:
        verbose_name = 'Зарядное устройство'
        verbose_name_plural = 'Зарядные устройства'

    @property
    def ports_total(self):
        return self.usb_c_ports + self.usb_a_ports

    @property
    def ports_display(self):
        parts = []
        if self.usb_c_ports:
            parts.append(f"{self.usb_c_ports}x Type-C")
        if self.usb_a_ports:
            parts.append(f"{self.usb_a_ports}x USB-A")
        return ", ".join(parts) if parts else "Без портов"

# ==========================================
# 4. КАБЕЛИ ПИТАНИЯ И ДАННЫХ
# ==========================================
class Cable(Product):
    class ConnectorType(models.TextChoices):
        USB_A = 'usb_a', 'USB-A'
        USB_C = 'usb_c', 'USB Type-C'
        LIGHTNING = 'lightning', 'Lightning'
        MICRO_USB = 'micro_usb', 'Micro-USB'

    connector_from = models.CharField(
        max_length=20, choices=ConnectorType.choices, default=ConnectorType.USB_C, verbose_name="Разъем 1 (откуда)"
    )
    connector_to = models.CharField(
        max_length=20, choices=ConnectorType.choices, default=ConnectorType.USB_C, verbose_name="Разъем 2 (куда)"
    )

    # Технические параметры
    length_m = models.DecimalField(
        max_digits=3, decimal_places=2, verbose_name="Длина кабеля (м)", help_text="Например: 0.25, 1.00, 2.00"
    )
    max_power_w = models.PositiveIntegerField(
        default=60, verbose_name="Макс. пропускаемая мощность (Вт)", help_text="60, 100, 240"
    )
    max_current_a = models.DecimalField(
        max_digits=3, decimal_places=1, blank=True, null=True, verbose_name="Макс. ток (А)", help_text="3.0, 5.0"
    )

    # Физические свойства
    data_transfer_speed = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Скорость передачи данных", help_text="480 Мбит/с, 10 Гбит/с"
    )
    braiding_material = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Материал оплетки", help_text="Нейлоновая оплетка, Силикон, ТЭП"
    )

    class Meta:
        verbose_name = 'Кабель питания'
        verbose_name_plural = 'Кабели питания'

    @property
    def connection_display(self):
        return f"{self.get_connector_from_display()} → {self.get_connector_to_display()}"

# ==========================================
# 5. ПОВЕРБАНКИ (POWERBANKS)
# ==========================================
class PowerBank(Product):
    class DisplayType(models.TextChoices):
        DIGITAL = 'digital', 'Цифровой дисплей (%)'
        LED = 'led', 'Светодиодные индикаторы'
        NONE = 'none', 'Отсутствует'

    capacity_mah = models.PositiveIntegerField(
        verbose_name="Емкость (мА·ч)", help_text="Например: 10000, 20000, 30000"
    )
    max_power_w = models.PositiveIntegerField(
        default=22, verbose_name="Макс. выходная мощность (Вт)", help_text="Например: 22, 45, 65, 100"
    )

    # Разъемы Выхода (Output)
    usb_c_ports = models.PositiveSmallIntegerField(default=1, verbose_name="Выходов USB Type-C")
    usb_a_ports = models.PositiveSmallIntegerField(default=1, verbose_name="Выходов USB-A")

    # Дополнительные функции
    has_wireless_charging = models.BooleanField(default=False, verbose_name="Беспроводная зарядка")
    has_magsafe = models.BooleanField(default=False, verbose_name="Поддержка MagSafe / магнитное крепление")
    has_built_in_cable = models.BooleanField(default=False, verbose_name="Встроенный кабель")
    is_pass_through_supported = models.BooleanField(
        default=False, verbose_name="Сквозная зарядка", help_text="Зарядка повербанка и подключенных устройств одновременно"
    )
    display_type = models.CharField(
        max_length=20, choices=DisplayType.choices, default=DisplayType.LED, verbose_name="Индикация заряда"
    )

    class Meta:
        verbose_name = 'Повербанк'
        verbose_name_plural = 'Повербанки'

    @property
    def capacity_display(self):
        return f"{self.capacity_mah:,}".replace(',', ' ') + " мА·ч"

# 6. Баннеры (наследует Product + свои поля)
class Banner(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок баннера")
    subtitle = models.TextField(verbose_name="Описание / Подзаголовок", blank=True)
    image = models.ImageField(upload_to='promo/', verbose_name="Изображение баннера", blank=True, null=True)
    link = models.CharField(max_length=200, default="#", verbose_name="Ссылка при клике")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Баннер"
        verbose_name_plural = "Баннеры"

    def __str__(self):
        return self.title