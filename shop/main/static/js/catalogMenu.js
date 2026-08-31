document.addEventListener("DOMContentLoaded", () => {
  const catalogDropdown = document.querySelector(".catalog-dropdown");
  const catalogBtn = document.querySelector(".catalog-btn");
  const catalogMenu = document.querySelector(".catalog-menu");

  const sortDropdown = document.querySelector(".sort-dropdown");
  const sortBtn = document.querySelector(".sort-btn");
  const sortMenu = document.querySelector(".sort-menu");

  const closeMenu = (menu, button) => {
    if (!menu) return;
    menu.classList.remove("is-open");
    if (button) button.setAttribute("aria-expanded", "false");
  };

  const toggleMenu = (menu, button, otherMenu, otherButton) => {
    if (!menu || !button) return;
    const willOpen = !menu.classList.contains("is-open");
    closeMenu(otherMenu, otherButton);
    menu.classList.toggle("is-open", willOpen);
    button.setAttribute("aria-expanded", String(willOpen));
  };

  catalogBtn?.addEventListener("click", (event) => {
    event.stopPropagation();
    toggleMenu(catalogMenu, catalogBtn, sortMenu, sortBtn);
  });

  sortBtn?.addEventListener("click", (event) => {
    event.stopPropagation();
    toggleMenu(sortMenu, sortBtn, catalogMenu, catalogBtn);
  });

  document.addEventListener("click", (event) => {
    if (catalogDropdown && !catalogDropdown.contains(event.target)) {
      closeMenu(catalogMenu, catalogBtn);
    }
    if (sortDropdown && !sortDropdown.contains(event.target)) {
      closeMenu(sortMenu, sortBtn);
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeMenu(catalogMenu, catalogBtn);
      closeMenu(sortMenu, sortBtn);
    }
  });
});
