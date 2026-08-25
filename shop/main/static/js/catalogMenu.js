document.addEventListener("DOMContentLoaded", function () {
  // Элементы каталога
  const catalogDropdown = document.querySelector(".catalog_dropdown");
  const catalogBtn = document.querySelector(".catalog_btn") || document.getElementById("catalogBtn");
  const catalogMenu = document.querySelector(".catalog_menu");

  // Элементы сортировки
  const sortDropdown = document.querySelector(".sort_dropdown");
  const sortBtn = document.querySelector(".sort_btn") || document.getElementById("sortBtn");
  const sortMenu = document.querySelector(".sort_menu");

  // Открытие/закрытие каталога
  if (catalogBtn && catalogMenu) {
    catalogBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      catalogMenu.classList.toggle("is-open");
      if (sortMenu) sortMenu.classList.remove("is-open"); // закрываем соседнее меню
    });
  }

  // Открытие/закрытие сортировки
  if (sortBtn && sortMenu) {
    sortBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      sortMenu.classList.toggle("is-open");
      if (catalogMenu) catalogMenu.classList.remove("is-open"); // закрываем соседнее меню
    });
  }

  // Закрытие обоих меню при клике в любое место вне их
  document.addEventListener("click", function (e) {
    if (catalogDropdown && !catalogDropdown.contains(e.target)) {
      if (catalogMenu) catalogMenu.classList.remove("is-open");
    }
    if (sortDropdown && !sortDropdown.contains(e.target)) {
      if (sortMenu) sortMenu.classList.remove("is-open");
    }
  });
});