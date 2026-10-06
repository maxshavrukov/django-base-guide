wishlist_readme.txt — приложение wishlist
============================================

Роль приложения
----------------
`wishlist` — список желаемых товаров («Избранное»).

Как и basket, он работает в двух режимах:

    гость -> session
    авторизованный -> БД

Главный класс:
    wishlist.services.wishlist.Wishlist

------------------------------------------------------------
1. ФАЙЛЫ
------------------------------------------------------------

wishlist/apps.py
----------------
`WishlistConfig` — обычная конфигурация приложения.

wishlist/__init__.py
--------------------
Пустой package-файл.

wishlist/admin.py
-----------------
Сейчас модели wishlist не зарегистрированы в Django Admin.
Файл содержит только стандартный импорт admin.

wishlist/models.py
------------------

`WishlistItem`
    Строка избранного для авторизованного пользователя.

Поля:
    user
    product
    created_at

`unique_together = ('user', 'product')`
    Один товар нельзя добавить одному пользователю два раза.

`__str__()`
    Возвращает `username - product`.

wishlist/context_processors.py
------------------------------

`wishlist(request)`
    Создаёт `Wishlist(request)` и делает его доступным в шаблонах как `wishlist`.

wishlist/urls.py
----------------

    /wishlist/                    -> wishlist_detail
    /wishlist/add/<product_id>/  -> wishlist_add
    /wishlist/remove/<product_id>/ -> wishlist_remove

------------------------------------------------------------
2. SERVICE — services/wishlist.py
------------------------------------------------------------

`CONCRETE_RELATIONS`
    Имена Django reverse-relations к concrete-моделям.

`_concrete_product(product)`
    Если передан уже concrete-товар — возвращает его.
    Если передан базовый Product — пробует найти Smartphone/Headphone/Charger/Cable/PowerBank.
    Если concrete потомка нет — возвращает исходный Product.

`Wishlist.__init__(request)`
    Сохраняет session, request и authenticated user.
    Для гостя создаёт session-list `wishlist`.

`add(product_id)`
    Авторизованный:
        создаёт WishlistItem через get_or_create.
    Гость:
        добавляет строковый id в session-list, если его там ещё нет.

`remove(product_id)`
    Удаляет товар из БД или session.

`save()`
    Помечает session modified.

`__iter__()`
    Делает Wishlist итерируемым.
    Загружает Product с brand/group/concrete relation и отдаёт concrete-объекты.

`__len__()`
    Количество товаров в избранном.

`clear()`
    Полностью очищает избранное.

------------------------------------------------------------
3. VIEWS
------------------------------------------------------------

wishlist/views.py
-----------------

`wishlist_detail(request)`
    Показывает `wishlist/wishlist_detail.html`.

`wishlist_add(request, product_id)`
    Добавляет товар и возвращает пользователя на HTTP_REFERER,
    а при отсутствии referer — в каталог.

`wishlist_remove(request, product_id)`
    Удаляет товар и возвращает на предыдущую страницу/в каталог.

------------------------------------------------------------
4. TEMPLATE
------------------------------------------------------------

wishlist/templates/wishlist/wishlist_detail.html
-------------------------------------------------
Наследует `users/account_base.html`, поэтому избранное находится внутри личного кабинета.

Показывает:
    - сетку избранных товаров;
    - категорию товара;
    - цену и скидку;
    - ссылку «Подробнее»;
    - кнопку удаления;
    - empty state, если список пуст.

------------------------------------------------------------
5. MIGRATION / TESTS
------------------------------------------------------------

migrations/0001_initial.py
    Создаёт WishlistItem.

tests/test_models.py
    Проверяет создание и unique user+product.

tests/test_views.py
    Проверяет detail, guest add/remove и authenticated add/remove.

tests/test_wishlist.py
    Проверяет сам класс Wishlist для гостя и пользователя,
    включая случай базового Product без concrete child.

------------------------------------------------------------
6. ЧТО ИСКАТЬ
------------------------------------------------------------

«Избранное не обновилось»
    -> Wishlist.add/remove
    -> context_processors.wishlist

«Гость видит одно, авторизованный другое»
    -> проверь режим хранения: session vs WishlistItem.

«В шаблоне доступны не те характеристики товара»
    -> `_concrete_product()` и `__iter__()`.

«Избранное не отображается в header»
    -> main/base.html.
    Сейчас ссылка «Избранное» в primary-nav закомментирована,
    хотя context processor wishlist всё равно подключён.
