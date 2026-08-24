document.addEventListener("DOMContentLoaded", function () {
  const dropdown = document.getElementById("catalogDropdown");
  const btn = document.getElementById("catalogBtn");

  if (!dropdown || !btn) return;

  // Открытие / закрытие по клику на кнопку
  btn.addEventListener("click", function (e) {
    e.stopPropagation();
    dropdown.classList.toggle("active");
  });

  // Закрытие при клике вне меню
  document.addEventListener("click", function (e) {
    if (!dropdown.contains(e.target)) {
      dropdown.classList.remove("active");
    }
  });
});