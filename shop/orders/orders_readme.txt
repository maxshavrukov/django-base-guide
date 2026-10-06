orders_readme.txt — приложение orders
==========================================

Роль приложения
----------------
`orders` отвечает за оформление заказа и сохранение его в БД.
Источник товаров для заказа — объект Basket из `basket`.

Основная цепочка:

    /orders/create/
        -> orders.views.order_create
        -> OrderCreateForm
        -> orders.services.order.create_order
        -> Order + OrderItem
        -> списание бонусов (если есть)
        -> очистка Basket
        -> orders/templates/orders/created.html

Вторая важная цепочка:

    admin меняет Order.paid=True
        -> post_save signal
        -> BonusService.grant_purchase_bonus(order)

------------------------------------------------------------
1. ФАЙЛЫ
------------------------------------------------------------

orders/apps.py
--------------
`OrdersConfig` — конфигурация приложения.

`ready()`
    Импортирует `orders.signals`, чтобы Django зарегистрировал post_save signal.

orders/__init__.py
------------------
Пустой package-файл.

orders/urls.py
-------------

    /orders/create/ -> order_create

orders/forms.py
---------------

`OrderCreateForm`
    ModelForm для создания Order.
    Поля:
        first_name
        email
        phone
        address
        comment

Важно:
    некоторые дополнительные поля интерфейса checkout (город, доставка и т.п.)
    существуют в HTML, но в текущей ModelForm в список полей не входят.
    Поэтому при возврате к checkout стоит отдельно помнить, какие поля реально сохраняются в Order.

------------------------------------------------------------
2. MODELS
------------------------------------------------------------

orders/models.py
----------------

Order
-----
Главный объект заказа.

Основные поля:
    user
    first_name
    email
    phone
    address
    comment
    created
    updated
    paid

Бонусные/скидочные поля:
    purchase_bonus_granted
    purchase_bonus_amount
    basket_discount_amount
    bonus_spent_amount

`__str__()`
    `Order <id>`.

`get_items_total()`
    Суммирует `price * quantity` по OrderItem.

`get_total_cost()`
    Берёт сумму позиций и вычитает скидку корзины и потраченные бонусы.
    Ниже нуля результат не падает.

OrderItem
---------
Фиксированная строка заказа.

Поля:
    order
    product
    price
    quantity
    bonus_eligible

Особенность:
    цена здесь хранится отдельно от текущей цены товара.
    Это важно, потому что заказ должен помнить цену на момент покупки.

`__str__()`
    Возвращает id строки.

`get_cost()`
    `price * quantity`.

------------------------------------------------------------
3. VIEW
------------------------------------------------------------

orders/views.py
---------------

`order_create(request)`
    1) создаёт Basket;
    2) вычисляет `basket_details`;
    3) если POST — валидирует OrderCreateForm;
    4) при успехе вызывает `create_order()`;
    5) при успехе показывает `created.html`;
    6) при ошибке остаётся на create.html с form errors.

------------------------------------------------------------
4. SERVICE — services/order.py
------------------------------------------------------------

`create_order(user, form, basket)`
    Центральная операция оформления заказа.
    Помечена `transaction.atomic`, поэтому БД либо получает согласованный результат,
    либо изменения откатываются.

Алгоритм:
    1. form.save(commit=False) -> готовим Order.
    2. Если пользователь авторизован — записываем order.user.
    3. Получаем basket_details.
    4. Берём скидку корзины и запрошенные бонусы.
    5. Ограничиваем фактическую сумму бонусов через min().
    6. Сохраняем Order.
    7. Для каждой позиции создаём OrderItem.
    8. Вычисляем `bonus_eligible`.
    9. Если бонусы реально тратятся и есть пользователь — вызываем BonusService.spend().
    10. После успешных операций очищаем basket.

Очень важный смысл `bonus_eligible`:
    бонусы за покупку не должны начисляться на товар,
    если товар уже был со скидкой или была скидка корзины.

------------------------------------------------------------
5. SIGNALS
------------------------------------------------------------

orders/signals.py
-----------------

`grant_purchase_bonus_after_payment(sender, instance, created, **kwargs)`
    Слушает post_save Order.
    Если:
        order.user_id существует
        AND order.paid=True
        AND purchase_bonus_granted=False
    то вызывается:
        BonusService.grant_purchase_bonus(order)

Получается, сам факт создания заказа бонусы не начисляет.
Нужен признак оплаченного заказа.

------------------------------------------------------------
6. ADMIN
------------------------------------------------------------

orders/admin.py
---------------

`OrderItemInline`
    Показывает состав заказа прямо внутри Order.

`OrderAdmin.get_items_summary(obj)`
    Собирает строку с товарами и количеством.

`OrderAdmin.get_total_cost(obj)`
    Показывает итог заказа в admin.

В admin Order можно:
    искать по имени, телефону, адресу, email;
    фильтровать по paid/created;
    видеть состав заказа inline.

------------------------------------------------------------
7. ШАБЛОНЫ И JS
------------------------------------------------------------

orders/templates/orders/create.html
-----------------------------------
Checkout-страница.
Наследует `main/base.html`.
Подключает:
    orders/css/orders.css
    orders/css/bonus.css
    orders/js/checkout.js

Содержит:
    контактные данные;
    оплату бонусами;
    доставку;
    выбор города;
    выбор отделения;
    комментарий;
    summary заказа.

orders/templates/orders/created.html
------------------------------------
Страница успеха после создания заказа.
Показывает номер заказа и ссылки обратно в магазин/мои заказы.

orders/static/orders/js/checkout.js
-----------------------------------
Клиентская логика checkout.
В первую очередь отвечает за интерфейс доставки:
    выбор способа доставки;
    ввод города;
    список подсказок города;
    загрузка отделений;
    активация/деактивация поля отделения.

Для подробного поиска поведения здесь удобно начинать с обработчиков `change`/`input`
и элементов `#delivery_service`, `#city_input`, `#city_suggestions`, `#id_address`.

orders/static/orders/css/orders.css
-----------------------------------
Стили формы оформления заказа, summary и success page.
Ключевые блоки:
    .order_container
    .order_form_wrapper
    .order_field
    .order_input / .order_select / .order_textarea
    .order_summary
    .order_item
    .order_total
    .order_success_card

Responsive breakpoints: примерно 900px и 600px.

orders/static/orders/css/bonus.css
----------------------------------
Стили блока бонусной оплаты на checkout.

------------------------------------------------------------
8. MIGRATIONS
------------------------------------------------------------

0001_initial.py
    Создаёт Order и OrderItem.

0002_bonus_fields.py
    Добавляет поля скидок/бонусов в Order и bonus_eligible в OrderItem.

------------------------------------------------------------
9. TESTS
------------------------------------------------------------

test_models.py
    Проверяет расчёт стоимости заказа.

test_forms.py
    Проверяет валидную форму и обязательные поля.

test_views.py
    Проверяет успешное оформление заказа.

------------------------------------------------------------
10. ЧТО ИСКАТЬ
------------------------------------------------------------

«Заказ не создаётся»
    -> views.py -> OrderCreateForm -> create_order()

«Сумма заказа не та»
    -> Order.get_total_cost()
    -> Basket.get_basket_details()

«Бонусы не начисляются после оплаты»
    -> orders/signals.py
    -> order.paid
    -> BonusService.grant_purchase_bonus()

«Бонусы списались, но не должны были»
    -> Basket.get_max_bonus_redemption()
    -> BonusService.calculate_max_spend()
    -> create_order()

«Checkout выглядит неправильно»
    -> create.html -> orders.css

«Не работает выбор города/отделения»
    -> orders/static/orders/js/checkout.js
