basket_readme.txt — приложение basket
=========================================

Роль приложения
----------------
`basket` отвечает за корзину товаров.

Главная особенность: есть ДВА режима хранения корзины.

Гость:
    корзина хранится в session под ключом BASKET_SESSION_ID (по умолчанию `basket`).

Авторизованный пользователь:
    корзина хранится в БД в модели BasketItem.

Остальная часть приложения старается давать одинаковый интерфейс поверх обоих вариантов.
Главный объект для работы с корзиной — `basket.services.basket.Basket`.

------------------------------------------------------------
1. ФАЙЛЫ
------------------------------------------------------------

basket/apps.py
--------------
`BasketConfig` — стандартная конфигурация Django-приложения.

basket/__init__.py
------------------
Пустой package-файл.

basket/models.py
----------------

`BasketItem`
    Одна строка корзины авторизованного пользователя.

Поля:
    user       -> пользователь
    product    -> товар
    quantity   -> количество
    created_at -> дата добавления

`Meta.unique_together = ('user', 'product')`
    Один пользователь не может иметь две отдельные строки одного товара.

`__str__()`
    Возвращает удобное представление вроде `username - product (2)`.

basket/forms.py
---------------

`BasketAddProductForm`
    Форма для добавления товара.

Поля:
    quantity -> от 1 до 20, по умолчанию 1
    override -> скрытый boolean; если True, количество заменяется вместо прибавления

basket/context_processors.py
----------------------------

`basket(request)`
    Делает объект `Basket(request)` доступным во всех шаблонах через переменную `basket`.
    Поэтому base.html может показывать количество товаров, не получая basket вручную из каждого view.

basket/urls.py
--------------

    /basket/                         -> basket_detail
    /basket/add/<product_id>/       -> basket_add
    /basket/remove/<product_id>/    -> basket_remove
    /basket/update/<product_id>/<action>/ -> basket_update

------------------------------------------------------------
2. VIEWS
------------------------------------------------------------

basket/views.py
---------------

`basket_add(request, product_id)`
    Только POST.
    1) создаёт Basket;
    2) получает Product;
    3) проверяет BasketAddProductForm;
    4) вызывает basket.add();
    5) если запрос AJAX — возвращает JSON;
    6) иначе возвращает пользователя на предыдущую страницу или в корзину.

`basket_remove(request, product_id)`
    Только POST.
    Удаляет товар и возвращает AJAX JSON или redirect в корзину.

`basket_detail(request)`
    Рендерит `basket/basket_detail.html` и передаёт `basket_details`.

`basket_update(request, product_id, action)`
    Только POST.
    Для action `plus` увеличивает количество на 1,
    для `minus` уменьшает на 1.

------------------------------------------------------------
3. ГЛАВНАЯ ЛОГИКА — services/basket.py
------------------------------------------------------------

`Basket.MAX_QUANTITY = 20`
    Жёсткий верхний лимит товара в корзине.

`Basket.__init__(request)`
    Запоминает session, request и пользователя.
    Для гостя при необходимости создаёт session-словарь корзины.

`add(product, quantity=1, override_quantity=False)`
    Для авторизованного:
        работает с BasketItem в БД.
    Для гостя:
        работает со словарём session.
    Если override=False — прибавляет количество.
    Если override=True — заменяет.
    Значение ограничивается диапазоном 0..20.
    Если получается 0 — товар удаляется.

`change_quantity(product, delta)`
    Унифицированный +/- для гостя и пользователя.

`save()`
    Для session-корзины ставит `session.modified = True`.

`remove(product)`
    Удаляет товар из БД или session.

`_product_price(product)`
    Возвращает текущую цену товара после product-level скидок.
    Это НЕ cart promotion.

`__iter__()`
    Делает Basket итерируемым.
    На каждой строке возвращается словарь:
        product
        quantity
        price
        original_price
        product_discount_percent
        product_discount_amount
        total_price

    Благодаря этому template может делать:
        {% for item in basket %}

`__len__()`
    Возвращает общее количество единиц товаров, а не число разных позиций.

`get_subtotal_price()`
    Полная сумма по каталожным ценам, до всех скидок.

`get_product_discount_amount()`
    Сумма скидок, пришедших именно от product-level скидок.

`get_bonus_requested_amount()`
    Читает `bonus_spend` из POST текущего checkout-запроса.
    Значение не сохраняется в session.

`get_max_bonus_redemption()`
    Считает, сколько бонусов максимум можно использовать в текущей корзине.
    Важное правило: если уже есть cart promotion, бонусная оплата здесь отключается.

`get_bonus_available_balance()`
    Возвращает текущий доступный баланс BonusService.

`get_bonus_discount_amount()`
    Превращает допустимое количество бонусов в сумму скидки.
    Использует min(requested, max_redemption, available_balance).

`_get_discount_data()`
    Находит лучшую CartPromotion и возвращает:
        процент,
        названия применённых скидок,
        сумму скидки.

`get_discount_percentage()`
    Возвращает процент лучшей акции корзины.

`get_basket_details()`
    Центральный метод расчёта итогов корзины.
    Возвращает словарь с:
        subtotal
        product_discount_amount
        promo_discount_percent
        promo_discount_amount
        bonus_discount_amount
        bonus_spend_requested
        bonus_available_balance
        bonus_max_redemption
        bonus_rules
        discount_percent
        discount_amount
        total_price
        applied_discounts

`get_total_price()`
    Короткий доступ к итоговой цене.

`clear()`
    Очищает корзину БД или session.

`get_basket_ajax_payload(basket)`
    Формирует JSON-friendly словарь для AJAX.
    В него входят общие суммы и данные строк mini-cart.

------------------------------------------------------------
4. КАК РАБОТАЕТ ЦЕНА В КОРЗИНЕ
------------------------------------------------------------

Для одной позиции:

    original_price
        |
        v
    product-level discount
        |
        v
    item['price']

Потом на уровне корзины:

    subtotal по original_price
       - product_discount_amount
       - cart promotion
       - bonus discount
       = total_price

Этот порядок важен, потому что UI отдельно показывает скидку на товар,
дополнительную скидку корзины и оплату бонусами.

------------------------------------------------------------
5. HTML/CSS
------------------------------------------------------------

basket/templates/basket/basket_detail.html
-------------------------------------------
Наследует `main/base.html`.
Показывает:
    - заголовок корзины;
    - empty state;
    - список позиций;
    - +/− количество;
    - удаление;
    - summary с subtotal/скидками/итогом;
    - бонусную оплату;
    - кнопку checkout.

basket/static/basket/css/basket.css
-----------------------------------
Стили страницы корзины.
Основные классы:
    .cart_container
    .cart_item
    .cart_item-image
    .cart_item-info
    .cart_item-qty
    .cart_item-total
    .cart_summary
    .checkout_btn

Responsive:
    max-width 900px -> summary становится выше списка;
    max-width 620px -> карточка корзины становится двухколоночной/компактной.

basket/static/basket/css/bonus.css
----------------------------------
Маленький standalone-блок стилей для ввода оплаты бонусами.

------------------------------------------------------------
6. MIGRATION И TESTS
------------------------------------------------------------

migrations/0001_initial.py
    Создаёт BasketItem.

tests/test_models.py
    Проверяет создание BasketItem и запрет дубля user+product.

tests/test_basket.py
    Проверяет добавление и session, а также взаимодействие с CartPromotion.

tests/test_views.py
    Проверяет detail, AJAX add, discount payload и plus/minus.

------------------------------------------------------------
7. ЧТО ИСКАТЬ В ПЕРВУЮ ОЧЕРЕДЬ
------------------------------------------------------------

Если:
    «товар не добавляется»        -> views.py + services/basket.py
    «не меняется количество»      -> basket_update + change_quantity
    «неверный итог»               -> get_basket_details + CartPromotion + BonusService
    «не обновляется mini-cart»    -> main/static/js/cartModal.js
    «не видно корзину в header»   -> main/base.html + context_processors.py + style.css
    «пропали бонусы»              -> users/services/bonuses.py
