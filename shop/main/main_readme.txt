main_readme.txt — приложение main
====================================

Роль приложения
----------------
`main` — центральное приложение магазина. Здесь живёт практически всё, что относится
к каталогу и общему пользовательскому интерфейсу: товары, категории, бренды, группы,
скидки, акции, баннеры, каталог, поиск, фильтры, сортировка и общий layout сайта.

Упрощённо:

    shop/urls.py
        -> main/urls.py
            -> main/views.py
                -> main/services/*
                    -> main/models.py
                -> main/templates/main/*

------------------------------------------------------------
1. ФАЙЛЫ PYTHON
------------------------------------------------------------

main/apps.py
------------
`MainConfig` — стандартная конфигурация Django-приложения main.
Функций с бизнес-логикой нет.

main/__init__.py
---------------
Пустой файл. Помечает директорию как Python package.

main/constants.py
-----------------
Центральный реестр конкретных типов товаров.

`PRODUCT_TYPES`:
    кортеж вида (slug, имя для UI, Django-модель).
    Сейчас зарегистрированы:
        smartphones -> Smartphone
        headphones -> Headphone
        chargers -> Charger
        cables -> Cable
        powerbanks -> PowerBank

`PRODUCT_CATEGORIES`:
    алиас на PRODUCT_TYPES.

`PRODUCT_TYPE_BY_SLUG`:
    быстрый доступ по slug.

`CATEGORY_BY_MODEL_NAME`:
    быстрый доступ по имени concrete-модели.

Почему файл важен:
------------------
Если добавляешь новый тип товара, этот реестр — одно из первых мест, которое надо проверить.
Именно от него зависят сервисы, которые перебирают все concrete-модели товаров.

main/context_processors.py
--------------------------

`categories(request)`
    Отдаёт в шаблоны список активных корневых категорий и все бренды.
    На /admin/ специально возвращает пустые данные, чтобы не строить публичное меню в админке.

`catalog_menu(request)`
    Отдаёт `catalog_tree`, который строится через `get_catalog_tree()`.
    Это полноценное дерево для mega-menu: категория -> подкатегории -> бренды -> группы.

main/utils.py
-------------

`transliterate_to_cyrillic(text)`
    Простая замена латинских сочетаний на кириллицу.
    Сначала обрабатывает длинные последовательности (`shch`, `zh`, `ch` и т.п.),
    потом одиночные символы.
    Сейчас это вспомогательная функция; основной поиск в проекте реализован в `services/search.py`.

main/urls.py
------------
Маршруты приложения main:

    /                              -> product_list
    /delivery-and-payment/        -> delivery_and_payment
    /contacts/                    -> contacts
    /new/                         -> new_products
    /search/                      -> search_results
    /brand/<slug>/                -> product_list (режим бренда)
    /group/<slug>/                -> product_list (режим группы)
    /<id>/<slug>/                -> product_detail
    /<category_slug>/             -> product_list (режим категории)

Последний category_slug намеренно стоит в URLconf в самом конце, чтобы не перехватывать
более специфичные маршруты.

main/views.py
-------------

`product_list(request, category_slug=None, group_slug=None, brand_slug=None)`
    Главная точка входа каталога.
    1) получает общий набор товаров через `resolve_catalog_data()`;
    2) применяет базовые фильтры: бренд, цены, наличие;
    3) сортирует по GET-параметру `sort`;
    4) собирает данные для шаблона: баннеры, бренды, фильтры, группы,
       недавно просмотренные товары и т.д.;
    5) рендерит `main/product/list.html`.

`delivery_and_payment(request)`
    Рендерит статическую страницу `delivery_and_payment.html`.

`contacts(request)`
    Рендерит `contacts.html`.

`new_products(request)`
    Берёт доступные товары, сортирует по id от новых к старым и показывает максимум 12.

`search_results(request)`
    Берёт `q` из GET и передаёт его в `search_products()`.
    Рендерит страницу результатов поиска.

`product_detail(request, id, slug)`
    Ищет только доступный Product с заданными id и slug.
    Подтягивает бренд, группу, concrete-тип и галерею.
    Затем:
        - определяет корневую категорию;
        - записывает просмотр;
        - формирует варианты по памяти/цвету;
        - формирует похожие товары;
        - рендерит `product/detail.html`.

------------------------------------------------------------
2. МОДЕЛИ — main/models.py
------------------------------------------------------------

main/models.py — самый большой файл приложения. Он содержит модель данных каталога.

Brand
-----
Поля:
    name, slug, logo

`__str__()`
    Возвращает имя бренда.

`get_absolute_url()`
    Строит URL списка товаров бренда.

Category
--------
Дерево пользовательских категорий.

Поля:
    name, slug, parent, product_type, sort_order, is_active

`ProductType`
    Набор разрешённых concrete-типов товара:
    smartphone, headphone, charger, cable, powerbank.

`clean()`
    Проверяет правила категории:
    - у корневой категории обязательно должен быть product_type;
    - подкатегория не должна конфликтовать с типом родителя;
    - категория не может быть родителем самой себе.

`save()`
    Если slug пустой, генерирует его через slugify.
    При конфликте добавляет `-2`, `-3` и т.д.

`get_root()`
    Поднимается по цепочке parent до корневой категории.
    Использует `seen`, чтобы не зациклиться на ошибочной структуре данных.

`get_effective_product_type()`
    Ищет product_type у текущей категории или выше по родителям.
    Поэтому подкатегория может оставить свой product_type пустым и унаследовать его.

`get_absolute_url()`
    Возвращает URL категории.

MainCategory / SubCategory
--------------------------
Proxy-модели Category. Новой таблицы в БД не создают.
Нужны в основном для разделения корневых категорий и подкатегорий в Django Admin.

ProductGroup
------------
Серия/линейка товара.
Поля:
    name, slug, categories (ManyToMany)

`__str__()`
    Имя группы.

`get_absolute_url()`
    URL каталога по группе.

`save()`
    Автоматическая генерация уникального slug при необходимости.

Product
-------
Базовая модель всех товаров.

Общие поля:
    brand
    name
    slug
    image
    description
    color
    price
    discount
    stock
    available
    group
    color_code

`__str__()`
    Название товара.

`discount_percent`
    Property. Нормализует ручную скидку к диапазону 0..100.

`get_promotion_discount_percent()`
    Ищет лучшую активную ProductPromotion для товара.

`effective_discount_percent`
    Property. Берёт максимум из ручной скидки и промо-скидки.

`get_discounted_price()`
    Считает цену после эффективной скидки и округляет до копейки.

`get_discount_amount()`
    Разница между исходной и текущей ценой.

`category_name`
    Возвращает человекочитаемое имя concrete-типа товара.
    Сначала смотрит имя concrete-класса, затем пытается определить существующую
    связь с дочерним объектом.

`get_variants()`
    Возвращает доступные товары из той же ProductGroup.
    Если группы нет — пустой QuerySet.

`get_absolute_url()`
    URL конкретного товара вида /id/slug/.

ProductImage
------------
Дополнительная фотография товара.
Связана с Product через `images`.

`__str__()`
    Возвращает текст вроде «Фото для iPhone ...».

Concrete-модели товаров
-----------------------

Smartphone
    Унаследован от Product.
    Характеристики: дисплей, процессор, GPU, RAM, storage, слоты,
    камеры, батарея, зарядка, связь, SIM, eSIM, NFC, Wi-Fi, Bluetooth,
    ОС, защита и материал.

    Вложенные TextChoices:
        DisplayType, VideoResolution, SlotConfig, UsbType, OSChoices

Headphone
    Характеристики: тип, подключение, ANC, прозрачность, кодеки,
    автономность, Bluetooth, микрофон, влагозащита.

    `battery_display()`
        Готовит человекочитаемую строку автономности.

Charger
    Характеристики: тип, мощность, число USB-портов, GaN,
    протоколы быстрой зарядки, кабель в комплекте.

    `ports_total`
        Общее число USB-C + USB-A портов.

    `ports_display`
        Формирует строку вида `2x Type-C, 1x USB-A`.

Cable
    Характеристики: два разъёма, длина, мощность, ток, скорость передачи данных,
    материал оплётки.

    `connection_display`
        Формирует строку `USB Type-C → Lightning` и т.п.

PowerBank
    Характеристики: ёмкость, мощность, порты, беспроводная зарядка,
    MagSafe, встроенный кабель, pass-through, индикация.

    `capacity_display`
        Возвращает красивую строку ёмкости: `10 000 мА·ч`.

ProductPromotion
----------------
Промо-скидка, которая может применяться к:
    бренду / категории / группе / конкретному товару.

Основные поля:
    name, target_type, brand, category, group, product,
    discount_percent, starts_at, ends_at, is_active, created_at

`clean()`
    Проверяет, что выбрана ровно одна цель и скидка находится в 0..100%.
    Проверяет корректность дат.

`is_currently_active(now=None)`
    Проверяет флаг активности, процент и временной диапазон.

`applies_to(product)`
    Проверяет, подходит ли акция конкретному товару.
    Особый случай — категория: учитываются корневая категория и descendants.

`get_best_discount_for_product(product)`
    Находит максимальную активную ProductPromotion для товара.

CartPromotion
-------------
Акция на корзину.

Правила:
    CART           -> на всю сумму корзины
    CHEAPEST       -> на самый дешёвый товар
    MOST_EXPENSIVE  -> на самый дорогой товар
    NTH             -> на N-й товар

`clean()`
    Проверяет процент, минимальное количество и nth_position.

`is_currently_active(user=None, now=None)`
    Проверяет время, активность и требование «только для авторизованных».

`calculate_discount(items, user=None)`
    Проверяет, доступна ли акция и достигнут ли minimum quantity,
    затем считает скидку по выбранному правилу.

`get_best_for_basket(items, user=None)`
    Перебирает активные акции и возвращает ту, которая даёт максимальную скидку.

Banner
------
Визуальный баннер каталога.

Поля:
    title, subtitle, image, link, is_active, created_at

Важно: Banner сам по себе не влияет на цену и не создаёт скидку.

------------------------------------------------------------
3. SERVICES
------------------------------------------------------------

main/services/categories.py
---------------------------
Это низкоуровневые функции для категорий и определения concrete-модели.

`PRODUCT_TYPE_TO_MODEL`
    Карта имени concrete-модели -> модель.

`FILTER_KEY_BY_PRODUCT_TYPE`
    Карта concrete-модели -> ключ конфигурации фильтров.

`get_active_root_categories()`
    Возвращает активные корневые категории.

`get_category_descendant_ids(category)`
    Возвращает id самой категории + всех активных дочерних категорий любой глубины.

`get_product_model(product)`
    По базовому Product определяет конкретную модель (Smartphone, Headphone и т.д.).

`get_category_model(category)`
    Определяет concrete-модель товара по effective product type категории.

`get_category_filter_key(category)`
    Возвращает ключ, под которым лежит конфигурация фильтров.

`get_category_product_queryset(category)`
    Возвращает доступные товары выбранной категории.
    Для корневой категории берёт все товары concrete-типа.
    Для подкатегории ищет товары через ProductGroup.categories.

`get_category_group_queryset(category)`
    Возвращает группы товаров, которые видны внутри категории.

`get_product_root_category(product)`
    Находит активную корневую категорию, соответствующую concrete-типу товара.

`get_catalog_tree()`
    Главная функция построения mega-menu.
    Создаёт структуру:
        root category
            -> children
            -> brands
                -> groups
    Эта функция используется context processor `catalog_menu`.

main/services/filters.py
------------------------

`CATEGORY_FILTER_FIELDS`
    Конфигурация полей фильтра для каждой concrete-категории.

Для смартфонов:
    brand, operating_system, display_type, display_size,
    display_refresh_rate, processor, ram, storage, nfc_support, has_esim

Для наушников:
    brand, headphone_type, connection_type, has_anc, has_microphone

Для зарядных:
    brand, charger_type, is_gan

Для кабелей:
    brand

Для повербанков:
    brand, has_wireless_charging, has_magsafe

`get_category_filter_options(category_slug, base_queryset, request_get=None)`
    Собирает варианты фильтра из реальных значений в БД.
    Для boolean полей даёт Да/Нет.
    Для Django choices пытается показать человекочитаемое название.

`apply_category_filters(queryset, category_slug, request_get)`
    Реально применяет выбранные фильтры к QuerySet.

main/services/product_list.py
-----------------------------

`get_all_available_products()`
    Собирает все доступные товары из всех concrete-моделей.

`_decimal_param(value)`
    Безопасно превращает строку цены из GET в Decimal.
    Некорректное значение -> None.

`filter_products(products, request)`
    Применяет базовые фильтры:
        brand
        price_min
        price_max
        in_stock
    Цена сравнивается уже после скидки.

`sort_products(products, sort_key)`
    Сортирует переданный список на месте.
    Поддерживает цену по возрастанию/убыванию и имя А-Я/Я-А.

`build_sort_urls(request)`
    Строит ссылки сортировки, сохраняя текущие GET-параметры.

`get_category_groups(products)`
    Достаёт ProductGroup для переданного списка товаров.

`get_recently_viewed_products(request)`
    Читает id из session `recently_viewed` и восстанавливает товары из concrete-моделей.

`resolve_catalog_data(...)`
    Главный диспетчер данных каталога.
    Может работать в четырёх режимах:
        brand_slug  -> товары бренда
        group_slug  -> конкретная серия/линейка
        category_slug -> категория
        ничего       -> весь каталог
    Параллельно формирует фильтры и группы.

`_get_category_or_none(slug)`
    Активная категория или None.

`_find_product_category(product)`
    Делегирует определение категории в catalog.py.

`_get_filter_key_for_product(product)`
    Определяет ключ конфигурации фильтров по concrete-модели.

`_get_group_concrete_queryset(group, product)`
    Возвращает товары группы только concrete-типа текущего товара.

main/services/product_detail.py
--------------------------------

`update_recently_viewed(request, product_id)`
    Обновляет session-список недавно просмотренных.
    Последний товар помещается в начало, хранится максимум 4.

`record_product_view(request, product)`
    Вызывает session-историю и, если пользователь авторизован,
    сохраняет товар в DB-историю через users.services.profile.

`get_product_gallery(product)`
    Собирает основную картинку + дополнительные ProductImage.

`_get_storage_val(instance)`
    Нормализует отображение памяти товара.

`_get_concrete_model(product)`
    Получает concrete-модель через categories.py.

`get_product_variants(product)`
    Строит варианты товара внутри его группы.
    Сейчас отдельно формируются варианты по storage и color.
    Для каждого варианта выбирается подходящий Product и помечается активный.

`get_related_products(product)`
    Возвращает до 4 последних доступных товаров того же concrete-типа,
    исключая текущий товар.

main/services/catalog.py
------------------------

`category_menu()`
    Возвращает простой список корневых категорий: slug + name.

`product_category_slug(product)`
    Возвращает slug и имя корневой категории товара.
    Если категория не найдена — `(None, 'Товары')`.

main/services/search.py
----------------------

`LAYOUT_MAPPING`
    Таблица замены русской/украинской раскладки в английскую.

`RU_TO_EN_LAYOUT`
    Готовая translation-table.

`CYR_TO_LAT_MAP`
    Фонетическая транслитерация кириллицы в латиницу.

`_transliterate_cyr_to_lat(text)`
    Например `самсунг` -> `samsung`.

`search_products(query)`
    Поиск идёт каскадом:
        1. точный ввод пользователя;
        2. фонетическая латиница;
        3. смена раскладки клавиатуры.
    Ищет по name, description и brand.name.

------------------------------------------------------------
4. ADMIN — main/admin.py
------------------------------------------------------------

Этот файл сильно расширяет стандартную Django Admin.

`CustomDiscountForm`
    Форма с процентом 0..100.

`set_custom_discount(modeladmin, request, queryset)`
    Admin action: применяет одну скидку ко всем выбранным товарам.
    Если action вызван впервые — показывает промежуточную форму.

`duplicate_products(modeladmin, request, queryset)`
    Admin action: создаёт копию товара и копирует его ProductImage.
    Slug копии получает `-copy`, `-copy-1`, ... при конфликте.
    Всё выполняется в transaction.atomic().

`ProductImageInline`
    Inline для фотографий товара.

`CommonProductAdminMixin`
    Общие настройки админки для всех concrete-моделей товаров:
    таблица, фильтры, поиск, slug, inline-фото, actions.

`BrandAdmin`
    Управление брендами.

`RootCategoryForm`
    Форма корневой категории. Родитель фиксирован как None.

`RootCategoryForm.clean_parent()`
    Всегда возвращает None.

`SubCategoryForm`
    Форма подкатегории. Показывает только допустимых родителей-корней.

`SubCategoryForm.__init__()`
    Формирует queryset для поля parent.

`SubCategoryForm.clean_parent()`
    Запрещает выбирать родителем другую подкатегорию.

`MainCategoryAdmin.get_queryset()`
    Показывает только root categories.

`MainCategoryAdmin.save_model()`
    Принудительно сохраняет parent=None.

`SubCategoryAdmin.get_queryset()`
    Показывает только дочерние категории.

`SubCategoryAdmin.save_model()`
    Автоматически записывает product_type через `get_effective_product_type()`.

`SmartphoneAdmin`, `HeadphoneAdmin`, `ChargerAdmin`, `CableAdmin`, `PowerBankAdmin`
    Разделяют характеристики товара на понятные fieldsets.

`ProductPromotionAdmin.current_status()`
    Показывает: Отключена / Запланирована / Завершена / Действует.

`CartPromotionAdmin.current_status()`
    Аналогичный статус для акций корзины.

`BannerAdmin`
    Управляет баннерами и их активностью.

`ProductInline.has_add_permission()`
    Запрещает вручную добавлять Product прямо из ProductGroup inline.
    Товары здесь только для просмотра.

`ProductGroupForm.__init__()`
    Настраивает список выбираемых подкатегорий для ProductGroup.

`ProductGroupAdmin.get_queryset()`
    Добавляет аннотацию `_products_count`.

`ProductGroupAdmin.products_count()`
    Показывает количество товаров в группе.

`get_grouped_app_list()`
    Переопределяет порядок списка моделей Django Admin.
    Виртуально группирует их в:
        1. Структура каталога
        2. Товары
        3. Маркетинг

------------------------------------------------------------
5. MANAGEMENT COMMANDS
------------------------------------------------------------

main/management/commands/dump_catalog.py
-----------------------------------------

`Command.add_arguments(parser)`
    Добавляет аргументы команды.

`Command.handle(*args, **options)`
    Создаёт снапшот каталога в main/fixtures/catalog_dump.json.
    Это способ сохранить каталог в Git и восстановить его позже.

main/management/commands/load_catalog.py
-----------------------------------------

`Command.add_arguments(parser)`
    Настраивает аргументы загрузки fixture.

`Command.handle(*args, **options)`
    Загружает каталог из fixture.
    В логике есть защита от повторного наполнения и обработка старых/legacy связей.

`Command._fixture_path(fixture_name)`
    Строит путь к fixture-файлу.

`Command._remap_root_parents(payload)`
    Исправляет/переназначает связи родительских root-категорий при загрузке.

------------------------------------------------------------
6. ШАБЛОНЫ
------------------------------------------------------------

main/templates/main/base.html
    Главный layout сайта.
    Наследуется большинством публичных страниц.

main/templates/main/product/list.html
    Страница каталога.
    Здесь находится `catalog-heading`, sidebar фильтров, сортировка,
    сетка товаров и дополнительные блоки.

main/templates/main/product/_card.html
    Переиспользуемая карточка товара.
    Подключается через `{% include ... %}`.

main/templates/main/product/detail.html
    Большая страница товара: хлебные крошки, галерея, характеристики,
    цена, варианты, корзина, избранное, связанные товары.

main/templates/main/new_products.html
    Страница новинок.

main/templates/main/search_results.html
    Результаты поиска.

main/templates/main/delivery_and_payment.html
    Статическая информационная страница.

main/templates/main/contacts.html
    Страница контактов.

main/templates/admin/apply_discount_intermediate.html
    Промежуточная admin-страница для action `set_custom_discount`.

------------------------------------------------------------
7. JAVASCRIPT
------------------------------------------------------------

main/static/js/utils.js
-----------------------
`getCookie(name)`
    Читает cookie по имени. Используется для CSRF-токена при AJAX POST.

main/static/js/catalogMenu.js
-----------------------------
Главный клиентский контроллер меню каталога, сортировки и mini-cart.

`isMobile()`
    Проверяет viewport <= 860px.

`setMenuOpen(menu, button, isOpen)`
    Открывает/закрывает меню и синхронизирует aria-expanded.

`toggleMenu(menu, button, otherMenu, otherButton)`
    Переключает одно меню и закрывает другое.

`closeAll()`
    Закрывает каталог, сортировку и mini-cart.

`activateCatalogPanel(slug)`
    Делает активной нужную панель mega-menu и подсвечивает категорию.

Поведение:
    - desktop: при наведении на категорию переключается панель;
    - mobile: панели переключаются нажатием;
    - click outside закрывает меню;
    - Escape закрывает всё.

main/static/js/cartModal.js
---------------------------
Отвечает за AJAX-добавление/удаление товаров и обновление mini-cart.

`showToast()`
    Показывает всплывающее уведомление «товар добавлен».

`requestJson(url, options)`
    Выполняет fetch и возвращает JSON; при HTTP ошибке бросает exception.

`preserveMiniCartOpen()`
    После AJAX-изменения сохраняет mini-cart открытой, если она была открыта.

`updateMiniCartUI(data)`
    Главная UI-функция.
    Обновляет количество, суммы, скидки и список товаров mini-cart.

`escapeHtml(value)`
    Безопасно экранирует текст перед вставкой в innerHTML.

Также есть глобальная обработка submit/click для URL корзины.

main/static/js/product-quantity.js
-----------------------------------
Управляет +/- возле количества товара.

`getBounds()`
    Читает min/max из HTML input.

`normalize()`
    Приводит введённое количество к допустимому диапазону.

main/static/js/bannerSlider.js
------------------------------
Автоматический слайдер баннеров.

`showSlide(index)`
    Активирует нужный слайд и точку.

`start()`
    Запускает автоматическую смену каждые 5 секунд.

`restart()`
    Перезапускает таймер.

При наведении мыши автопереключение временно останавливается.

main/static/js/imageModal.js
----------------------------
Галерея и полноэкранный modal на странице товара.

`updateGallery(index)`
    Меняет основное изображение, активную thumbnail и кнопки навигации.

`close()`
    Закрывает modal и снимает body.modal-open.

`open()`
    Открывает modal и синхронизирует изображение.

Поддерживает мышь, Enter/Space, Escape и стрелки ← →.

------------------------------------------------------------
8. CSS
------------------------------------------------------------

main/static/style.css
---------------------
Глобальный CSS всего магазина.
Основные области:
    - layout и container;
    - header/topbar/navigation;
    - catalog menu;
    - search;
    - cart + mini-cart;
    - кнопки и общие UI-компоненты;
    - hero/banner;
    - catalog page;
    - product cards;
    - product detail;
    - media queries для responsive.

Главные mobile breakpoints проекта находятся вокруг 860px, 900px, 680/620px и меньше.

Особенно важные классы для каталога:
    .catalog-dropdown
    .catalog-menu
    .catalog-menu--mega
    .catalog-heading
    .sort-dropdown
    .sort-menu

Если проблема выглядит как «один блок накрывает другой», сначала проверяй:
    position
    z-index
    overflow
    transform
    stacking context родителя

------------------------------------------------------------
9. MIGRATIONS
------------------------------------------------------------

0001_initial.py
    Создаёт базовые модели каталога, concrete-товары, ProductGroup и Banner.

0002_alter_product_description.py
    Меняет поле описания товара.
    Текущее состояние использует CKEditor5Field.

0003_category_productgroup_categories_and_more.py
    Добавляет/перестраивает связи категорий и групп.

0004_seed_root_categories.py
    Создаёт корневые категории.
    `create_root_categories()` — добавляет исходные root categories.
    `remove_root_categories()` — обратная операция миграции.

0005_productpromotion_cartpromotion.py
    Добавляет модели ProductPromotion и CartPromotion.

0006_category_admin_proxies.py
    Добавляет proxy-модели MainCategory и SubCategory для admin.

------------------------------------------------------------
10. TESTS
------------------------------------------------------------

main/tests/test_models.py
    Проверяет создание Product/Banner, скидки и absolute_url.

main/tests/test_categories.py
    Проверяет правила категорий, наследование product_type,
    descendants, queryset и admin proxy.

main/tests/test_promotions.py
    Проверяет product promotion и cart promotion.

main/tests/test_views.py
    Проверяет страницы каталога, фильтрацию, menu markup,
    detail page и recently viewed.

main/tests/test_catalog_commands.py
    Проверяет загрузку/сохранение снапшота каталога и защиту от дублирования.

------------------------------------------------------------
11. СВЯЗЬ С ОСТАЛЬНЫМИ ПРИЛОЖЕНИЯМИ
------------------------------------------------------------

main -> basket
    detail product page содержит форму add-to-basket.

main -> wishlist
    detail product page содержит ссылку add/remove wishlist.

main -> users
    product_detail при авторизованном пользователе пишет history через users.services.profile.

main -> orders
    catalog сам заказ не создаёт, это делает orders.

main -> base.html
    Это главный frontend-контракт проекта: другие приложения в основном наследуют base.html.
