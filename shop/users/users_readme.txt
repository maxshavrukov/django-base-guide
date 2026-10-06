users_readme.txt — приложение users
========================================

Роль приложения
----------------
`users` содержит всё, что связано с пользователем после регистрации:
авторизацию, профиль, историю заказов, недавно просмотренные товары и бонусную программу.

Главный файл бизнес-логики бонусов:
    users/services/bonuses.py

Главная идея бонусной системы:
    BonusTransaction = история операций
    BonusConsumption = связь списания с конкретным начислением
    BonusService = правила и расчёты

------------------------------------------------------------
1. ФАЙЛЫ
------------------------------------------------------------

users/apps.py
-------------
`UsersConfig` — конфигурация приложения.

`ready()`
    Импортирует `users.signals`, чтобы активировать создание профиля и бонусного счёта.

users/__init__.py
-----------------
Пустой package-файл.

users/urls.py
-------------

    /users/auth/             -> auth_view
    /users/login/            -> user_login
    /users/register/         -> register
    /users/logout/           -> user_logout
    /users/profile/          -> profile_view
    /users/personal-data/    -> personal_data_view
    /users/bonuses/          -> bonus_history_view
    /users/recently-viewed/  -> recently_viewed_view
    /users/users/            -> order_list

Примечание:
    маршрут списка заказов исторически называется `/users/users/`.
    Имя URL при этом — `users:order_list`.

------------------------------------------------------------
2. MODELS
------------------------------------------------------------

users/models.py
---------------

UserProfile
-----------
Расширяет стандартного Django User.

Поля:
    user
    first_name
    last_name
    phone
    birth_date
    city
    address
    postal_code
    created_at
    updated_at

`__str__()`
    «Профиль: username».

`display_name`
    Если заполнены имя/фамилия — возвращает их.
    Иначе возвращает username.

BonusAccount
------------
Одно бонусное хранилище на пользователя.

`get_available_balance(at=None)`
    Делегирует расчёт BonusService.
    Саму формулу баланса здесь не дублирует.

BonusTransaction
----------------
Леджер бонусных операций.

Типы:
    PURCHASE   -> бонусы за покупку
    BIRTHDAY   -> подарок ко дню рождения
    SPEND      -> списание
    REFUND     -> возврат/сторно
    ADJUSTMENT -> ручная корректировка

Поля:
    account
    amount
    transaction_type
    order
    description
    reference_year
    created_at
    expires_at

`__str__()`
    Показывает знак и тип операции.

Ограничения:
    amount не может быть 0;
    birthday с reference_year защищён от дубля за один год.

BonusConsumption
----------------
Связывает отрицательную операцию SPEND с конкретным положительным источником.

Поля:
    spend_transaction
    source_transaction
    amount

Это позволяет точно знать, какие начисления были «съедены» при списании.

RecentlyViewedProduct
---------------------
История просмотренных товаров для авторизованного пользователя.

Уникальная пара:
    user + product

------------------------------------------------------------
3. FORMS
------------------------------------------------------------

users/forms.py
--------------

`UserLoginForm`
    Расширяет AuthenticationForm.
    Поле username подписано как «Имя пользователя или Email».

`UserRegistrationForm`
    Расширяет UserCreationForm.
    Поля: username, email.

`__init__()`
    Меняет человекочитаемые подписи полей.

`clean_email()`
    Запрещает регистрировать email, который уже существует (без учёта регистра).

`UserProfileForm`
    Редактирование UserProfile.

`clean_birth_date()`
    После первого сохранения запрещает пользователю менять дату рождения.
    Сделано для защиты бонусной логики от изменения birthday data.

------------------------------------------------------------
4. VIEWS
------------------------------------------------------------

users/views.py
--------------

`auth_view(request)`
    Если пользователь уже вошёл — отправляет в каталог.
    Иначе показывает страницу с login и register формами.

`user_login(request)`
    При POST валидирует UserLoginForm.
    При успехе использует `authenticate_and_login()` и ведёт в каталог.

`register(request)`
    При POST валидирует UserRegistrationForm.
    При успехе вызывает `register_and_login()` и сразу авторизует пользователя.

`user_logout(request)`
    Завершает сессию через `logout_user()`.

`profile_view(request)`
    Требует login.
    Показывает профиль, баланс бонусов, последние операции и публичные правила бонусной программы.

`personal_data_view(request)`
    Требует login.
    Показывает и сохраняет UserProfileForm.

`bonus_history_view(request)`
    Требует login.
    Показывает все BonusTransaction и текущий баланс.

`recently_viewed_view(request)`
    Требует login.
    Показывает историю последних просмотренных товаров.

`order_list(request)`
    Требует login.
    Получает заказы пользователя через `get_user_orders()`.

------------------------------------------------------------
5. SERVICES
------------------------------------------------------------

users/services/auth.py
----------------------

`authenticate_and_login(request, form)`
    Берёт пользователя из валидной формы и вызывает Django `login()`.

`register_and_login(request, form)`
    Сохраняет нового пользователя и сразу вызывает `login()`.

`logout_user(request)`
    Вызывает Django `logout()`.

users/services/profile.py
-------------------------

`get_user_profile(user)`
    Создаёт UserProfile, если его нет.
    Заодно создаёт BonusAccount.

`get_user_orders(user)`
    Возвращает QuerySet заказов пользователя с prefetch OrderItem/Product.

`record_recently_viewed(user, product)`
    Создаёт/обновляет DB history.
    Хранит максимум 20 записей для одного пользователя.

`get_recently_viewed(user, limit=20)`
    Возвращает последние просмотренные товары, сортируя по viewed_at.

------------------------------------------------------------
6. BONUS SERVICE — самый важный файл
------------------------------------------------------------

users/services/bonuses.py
-------------------------

`BonusService` — единый источник истины по бонусной программе.

Константы:
    PURCHASE_BONUS_PERCENT = 1
    PURCHASE_BONUS_VALIDITY_MONTHS = 12
    BIRTHDAY_BONUS = 1000
    BIRTHDAY_WINDOW_DAYS = 7
    MAX_PRODUCT_REDEMPTION_PERCENT = 50
    BONUS_VALUE_UAH = 1

`get_rules()`
    Возвращает все эти значения в виде словаря для UI.
    Поэтому шаблоны не должны хардкодить правила, если можно взять их отсюда.

`_today()`
    Возвращает локальную дату Django timezone.

`_add_months(value, months)`
    Добавляет месяцы с корректировкой дня для коротких месяцев.

`purchase_expiry(created_at)`
    Рассчитывает дату истечения бонусов за покупку (+12 месяцев).

`birthday_window(birth_date, year)`
    Возвращает окно: 7 дней до дня рождения и 7 дней после.
    29 февраля специально обрабатывается для не високосных лет.

`birthday_expiry(birth_date, year)`
    Бонус дня рождения истекает в начале следующего дня после окна.

`get_active_birthday_year(birth_date, on_date=None)`
    Определяет, попадает ли текущая дата в birthday window.

`birthday_is_active(birth_date, on_date=None)`
    Удобная boolean-обёртка.

`calculate_purchase_bonus(eligible_purchase_value)`
    Считает 1% от eligible purchase value и округляет до целого бонуса.

`get_or_create_account(user)`
    Возвращает BonusAccount пользователя, создавая его при необходимости.

`_positive_sources(account, at=None)`
    Находит ещё не полностью использованные положительные начисления,
    исключая истёкшие. Сортирует их по сроку истечения.

`get_available_balance(account, at=None)`
    Считает доступный баланс.
    Положительные транзакции уменьшаются на связанные BonusConsumption.
    Дополнительные отрицательные операции типа refund/adjustment уменьшают баланс напрямую.
    SPEND не вычитается второй раз, потому что он уже учтён через consumption.

`grant_purchase_bonus(order, created_at=None)`
    Начисляет бонусы за оплаченный заказ.
    Смотрит OrderItem.bonus_eligible.
    Если флаг None — использует резервное правило полной цены.
    Защищён от повторного начисления через purchase_bonus_granted.

`ensure_birthday_bonus(user, on_date=None)`
    Если сейчас birthday window и бонус за этот расчётный год ещё не выдавался,
    создаёт BonusTransaction типа BIRTHDAY.

`is_product_full_price(product)`
    True, если effective_discount_percent == 0.

`max_redemption_for_line(price, quantity=1)`
    Считает максимум бонусов для строки.
    Ограничение 50% применяется отдельно к каждой единице.
    Каждая единица округляется вниз до целого бонуса, затем результаты суммируются.

`calculate_max_spend(items)`
    Складывает допустимое списание по полным ценам.
    Товары со скидками исключаются.

`spend(user, amount, order=None, description='Оплата бонусами')`
    Списывает бонусы атомарно.
    Сначала блокирует источники и считает доступный баланс.
    Затем создаёт отрицательную SPEND-транзакцию и BonusConsumption.
    Использует начисления с ближайшим сроком истечения первыми.

`_locked_positive_sources(account, at)`
    Версия поиска источников с `select_for_update()` для безопасной транзакции списания.

`reverse_purchase_bonus(order, description=None)`
    Создаёт отрицательную REFUND-транзакцию для ранее начисленных бонусов за заказ.
    Защищён от повторного сторно.

`available_balance_after_expiration(user)`
    Удобный метод для пересчёта актуального баланса с учётом expirations.

------------------------------------------------------------
7. SIGNAL
------------------------------------------------------------

users/signals.py
----------------

`ensure_user_accounts(sender, instance, created, **kwargs)`
    После сохранения стандартного Django User гарантирует наличие:
        UserProfile
        BonusAccount

------------------------------------------------------------
8. MANAGEMENT COMMANDS
------------------------------------------------------------

expire_bonuses.py
-----------------
`Command.handle()`
    Сейчас НЕ удаляет истёкшие транзакции.
    Просто проходит по BonusAccount и выводит суммарный доступный баланс.
    Это диагностическая команда.

issue_birthday_bonuses.py
-------------------------
`Command.handle()`
    Берёт активных пользователей с birth_date и вызывает ensure_birthday_bonus().
    Отчитывается, сколько бонусов выдано и сколько пропущено.

recalculate_bonus_balances.py
-----------------------------
`Command.handle()`
    Проходит по активным пользователям и заставляет BonusService пересчитать доступный баланс.
    Историю операций не меняет.

------------------------------------------------------------
9. TEMPLATES
------------------------------------------------------------

users/templates/users/account_base.html
---------------------------------------
Второй важный layout после main/base.html.
Наследует main/base.html и добавляет личный кабинет.
Содержит боковое меню:
    заказы
    избранное
    персональные данные
    бонусы
    недавно просмотренные
    профиль
    logout

Остальные страницы кабинета наследуют account_base.html.

users/templates/users/auth.html
-------------------------------
Вход + регистрация в одной странице. Использует JS tab-switcher.

users/templates/users/profile.html
----------------------------------
Дашборд пользователя и бонусный баланс.

users/templates/users/personal_data.html
----------------------------------------
Форма UserProfileForm.

users/templates/users/bonus_history.html
----------------------------------------
История бонусных операций.

users/templates/users/recently_viewed.html
------------------------------------------
Сетка недавно просмотренных товаров.

users/templates/users/order_list.html
-------------------------------------
Список заказов пользователя.

------------------------------------------------------------
10. JAVASCRIPT/CSS
------------------------------------------------------------

users/static/users/js/authTabs.js
---------------------------------
Переключает tabs «Вход / Регистрация» и соответствующую форму.

users/static/users/css/users.css
--------------------------------
Основной CSS личного кабинета и auth.
Содержит:
    sidebar кабинета;
    ссылки меню;
    карточки профиля;
    wishlist grid;
    order history;
    profile form;
    auth page;
    responsive breakpoints.

users/static/users/css/bonuses.css
----------------------------------
Дополнительный CSS для бонусного dashboard.
Содержит стили:
    account shell/sidebar;
    bonus balance;
    account cards;
    rules grid;
    products grid;
    profile form.

------------------------------------------------------------
11. ADMIN
------------------------------------------------------------

users/admin.py
--------------

`CustomUserAdmin`
    Регистрирует/настраивает стандартного пользователя.

`UserProfileAdmin`
    Админка профилей.

`BonusAccountAdmin.available_balance(obj)`
    Показывает вычисленный доступный бонусный баланс.

`BonusTransactionAdmin`
    Просмотр/поиск бонусных операций.

`BonusConsumptionAdmin`
    Просмотр связи списаний с начислениями.

`RecentlyViewedProductAdmin`
    Просмотр истории просмотров.

------------------------------------------------------------
12. MIGRATION / TESTS
------------------------------------------------------------

migrations/0001_initial.py
    Создаёт UserProfile, BonusAccount, BonusTransaction,
    BonusConsumption, RecentlyViewedProduct и ограничения.

users/tests/test_bonuses.py
    Большой набор тестов для сроков действия, birthday window,
    трат бонусов FIFO по сроку, лимита 50%, начисления за полную цену,
    reverse/refund и единого источника правил.

users/tests/test_forms.py
    Проверяет уникальность email регистрации.

users/tests/test_views.py
    Проверяет auth/profile/bonus/history/order-list.

------------------------------------------------------------
13. КЛЮЧЕВАЯ СВЯЗЬ С ORDERS
------------------------------------------------------------

Создание заказа:
    orders.services.order.create_order()
        -> BonusService.spend()

Оплата заказа:
    Order.paid=True
        -> orders.signals
        -> BonusService.grant_purchase_bonus()

То есть «потратить бонусы» и «заработать бонусы» — это две разные операции.
