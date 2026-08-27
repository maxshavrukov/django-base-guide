from django.db import models
from django.urls import reverse

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Бренд")
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Бренд'
        verbose_name_plural = 'Бренды'

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse("main:product_list_by_category", args=[self.slug])

# Базовый класс для ВСЕХ товаров (общие поля)
class Product(models.Model):
    brand = models.ForeignKey(Brand, related_name='products', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Бренд")
    name = models.CharField(max_length=150, db_index=True, verbose_name="Название товара")
    slug = models.SlugField(max_length=150, unique=True)
    image = models.ImageField(upload_to='products/%Y/%m/%d', blank=True, verbose_name="Изображение")
    description = models.TextField(blank=True, verbose_name="Описание")
    color = models.CharField(max_length=50, blank=True, null=True, verbose_name="Цвет")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    
    stock = models.PositiveIntegerField(default=0, verbose_name="Количество на складе")
    available = models.BooleanField(default=True, verbose_name="Доступен для заказа")
    
    created = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        ordering = ('name',)
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return self.name
    
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

class Smartphone(Product):
    # харатрестики смартфонов
    # дисплей
    display_type = models.CharField(max_length=50, blank=True, null=True, verbose_name="Тип дисплея")
    display_refresh_rate = models.CharField(max_length=50, blank=True, null=True, verbose_name="Частота обновления дисплея")
    display_size = models.CharField(max_length=50, blank=True, null=True, verbose_name="Размер дисплея")
    display_resolution = models.CharField(max_length=50, blank=True, null=True, verbose_name="Разрешение дисплея")
    # связь
    communication_standards = models.CharField(max_length=100, blank=True, null=True, verbose_name="Стандарты связи")
    quantity_of_sim_cards = models.PositiveIntegerField(blank=True, null=True, verbose_name="Количество SIM-карт")
    sim_card_type = models.CharField(max_length=50, blank=True, null=True, verbose_name="Тип SIM-карты")
    # память
    ram = models.CharField(max_length=50, blank=True, null=True, verbose_name="Оперативная память (RAM)")
    storage = models.CharField(max_length=50, blank=True, null=True, verbose_name="Встроенная память")
    extra_storage = models.CharField(max_length=50, blank=True, null=True, verbose_name="Расширение памяти")
    # процессор
    processor = models.CharField(max_length=100, blank=True, null=True, verbose_name="Модель процессора")
    core_count = models.PositiveIntegerField(blank=True, null=True, verbose_name="Количество ядер процессора")
    core_speed = models.CharField(max_length=50, blank=True, null=True, verbose_name="Тактовая частота процессора")
    # аккумулятор
    battery_capacity = models.CharField(max_length=50, blank=True, null=True, verbose_name="Емкость батареи")
    charging_type = models.CharField(max_length=50, blank=True, null=True, verbose_name="Тип зарядки")
    # операционная система
    operating_system = models.CharField(max_length=50, blank=True, null=True, verbose_name="Операционная система")
    # камера
    main_camera = models.CharField(max_length=50, blank=True, null=True, verbose_name="Основная камера")
    front_camera = models.CharField(max_length=50, blank=True, null=True, verbose_name="Фронтальная камера")
    # дополнительные характеристики
    wi_fi_standards = models.CharField(max_length=50, blank=True, null=True, verbose_name="Стандарты Wi-Fi")
    bluetooth_version = models.CharField(max_length=50, blank=True, null=True, verbose_name="Версия Bluetooth")
    nfc_support = models.BooleanField(default=False, verbose_name="Поддержка NFC")
    navigational_systems = models.CharField(max_length=100, blank=True, null=True, verbose_name="Навигационные системы")
    interfaces_usb = models.CharField(max_length=50, blank=True, null=True, verbose_name="Интерфейсы USB")
    protection_class = models.CharField(max_length=50, blank=True, null=True, verbose_name="Класс защиты")
    material = models.CharField(max_length=50, blank=True, null=True, verbose_name="Материал корпуса")

    class Meta:
        verbose_name = 'Смартфон'
        verbose_name_plural = 'Смартфоны'

# 2. Наушники (наследует Product + свои поля)
class Headphone(Product):
    type = models.CharField(max_length=50, blank=True, null=True, verbose_name="Тип наушников (вкладыши/накладные/полноразмерные)")
    connection_type = models.CharField(max_length=50, blank=True, null=True, verbose_name="Тип подключения (проводные/беспроводные)")
    noise_cancellation = models.BooleanField(default=False, verbose_name="Активное шумоподавление (ANC)")
    battery_autonomy = models.CharField(max_length=50, blank=True, null=True, verbose_name="Время автономной работы")
    battery_full_case_autonomy = models.CharField(max_length=50, blank=True, null=True, verbose_name="Время автономной работы с кейсом (для беспроводных)")
    bluetooth_version = models.CharField(max_length=50, blank=True, null=True, verbose_name="Версия Bluetooth (для беспроводных)")
    microphone = models.BooleanField(default=False, verbose_name="Наличие микрофона")

    class Meta:
        verbose_name = 'Наушники'
        verbose_name_plural = 'Наушники'

# 3. Зарядные устройства (наследует Product + свои поля)
class Charger(Product):
    power = models.CharField(max_length=50, blank=True, null=True, verbose_name="Мощность (Вт)")
    ports_count = models.PositiveIntegerField(default=1, verbose_name="Количество портов")
    fast_charging = models.BooleanField(default=False, verbose_name="Поддержка быстрой зарядки")

    class Meta:
        verbose_name = 'Зарядное устройство'
        verbose_name_plural = 'Зарядные устройства'

# 4. Кабели питания (наследует Product + свои поля)
class Cable(Product):
    length = models.CharField(max_length=50, blank=True, null=True, verbose_name="Длина кабеля")
    connector_from = models.CharField(max_length=50, blank=True, null=True, verbose_name="Разъем 1 (например, USB-A)")
    connector_to = models.CharField(max_length=50, blank=True, null=True, verbose_name="Разъем 2 (например, Type-C)")

    class Meta:
        verbose_name = 'Кабель питания'
        verbose_name_plural = 'Кабели питания'

# 4. Повербанки (наследует Product + свои поля)
class PowerBank(Product):
    capacity = models.CharField(max_length=50, blank=True, null=True, verbose_name="Емкость (мАч)")
    ports_count = models.PositiveIntegerField(default=1, verbose_name="Количество портов")
    fast_charging = models.BooleanField(default=False, verbose_name="Поддержка быстрой зарядки")
    power_output = models.CharField(max_length=50, blank=True, null=True, verbose_name="Выходная мощность (Вт)")

    class Meta:
        verbose_name = 'Повербанк'
        verbose_name_plural = 'Повербанки'

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