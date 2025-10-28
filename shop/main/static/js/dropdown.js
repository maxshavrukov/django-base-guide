document.addEventListener('DOMContentLoaded', function () {
  // Делегирование и поддержка нескольких dropdown'ов
  // Структура ожидается такая:
  // <div class="dropdown">
  //   <button class="sort-button">Сортировка</button>
  //   <ul class="dropdown-menu">...</ul>
  // </div>

  // Закрыть все открытые dropdown'ы
  function closeAllDropdowns() {
    document.querySelectorAll('.dropdown.open').forEach(d => d.classList.remove('open'));
  }

  // Обработчик кликов по документу (делегирование)
  document.addEventListener('click', function (e) {
    const btn = e.target.closest('.sort-button');       // кнопка (если клик по ней или её потомку)
    const dropdown = e.target.closest('.dropdown');     // ближайший .dropdown от клика

    if (btn) {
      // Если кликнули по кнопке сортировки — переключаем её меню
      const thisDropdown = btn.closest('.dropdown');
      if (!thisDropdown) return; // безопасность

      // Закрываем другие dropdown'ы и открываем/закрываем текущий
      document.querySelectorAll('.dropdown.open').forEach(d => {
        if (d !== thisDropdown) d.classList.remove('open');
      });
      thisDropdown.classList.toggle('open');
      return;
    }

    // Если клик был не по кнопке — закрываем меню, если клик вне открытого dropdown
    if (!dropdown) {
      closeAllDropdowns();
      return;
    }

    // Если клик внутри .dropdown (например, по ссылке) — не делаем ничего,
    // можно закрывать после перехода, но обычно это handled naturally.
  });

  // Закрыть по нажатию Esc
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' || e.key === 'Esc') closeAllDropdowns();
  });
});