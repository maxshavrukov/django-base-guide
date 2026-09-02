document.addEventListener("DOMContentLoaded", () => {
  const catalogDropdown = document.querySelector(".catalog-dropdown");
  const catalogBtn = document.querySelector(".catalog-btn");
  const catalogMenu = document.querySelector(".catalog-menu");
  const sortDropdown = document.querySelector(".sort-dropdown");
  const sortBtn = document.querySelector(".sort-btn");
  const sortMenu = document.querySelector(".sort-menu");
  const headerCart = document.querySelector(".header-cart");
  const cartBtn = document.getElementById("cartBtn");
  const miniCart = document.getElementById("miniCart");

  const isMobile = () => window.matchMedia("(max-width: 860px)").matches;

  const setMenuOpen = (menu, button, isOpen) => {
    if (!menu) return;
    menu.classList.toggle("is-open", isOpen);
    if (menu === miniCart) {
      menu.hidden = !isOpen;
    }
    button?.setAttribute("aria-expanded", String(isOpen));
  };

  const toggleMenu = (menu, button, otherMenu, otherButton) => {
    if (!menu || !button) return;
    const willOpen = !menu.classList.contains("is-open");
    setMenuOpen(otherMenu, otherButton, false);
    setMenuOpen(menu, button, willOpen);
  };

  const closeAll = () => {
    setMenuOpen(catalogMenu, catalogBtn, false);
    setMenuOpen(sortMenu, sortBtn, false);
    setMenuOpen(miniCart, cartBtn, false);
  };

  catalogBtn?.addEventListener("click", (event) => {
    event.stopPropagation();
    toggleMenu(catalogMenu, catalogBtn, sortMenu, sortBtn);
    setMenuOpen(miniCart, cartBtn, false);
  });

  sortBtn?.addEventListener("click", (event) => {
    event.stopPropagation();
    toggleMenu(sortMenu, sortBtn, catalogMenu, catalogBtn);
    setMenuOpen(miniCart, cartBtn, false);
  });

  cartBtn?.addEventListener("click", (event) => {
    event.stopPropagation();
    const willOpen = !miniCart?.classList.contains("is-open");
    setMenuOpen(catalogMenu, catalogBtn, false);
    setMenuOpen(sortMenu, sortBtn, false);
    setMenuOpen(miniCart, cartBtn, willOpen);
  });

  const activateCatalogPanel = (slug) => {
    document.querySelectorAll("[data-catalog-panel]").forEach((panel) => {
      panel.classList.toggle("is-active", panel.dataset.catalogPanel === slug);
    });
    document.querySelectorAll("[data-catalog-category]").forEach((item) => {
      item.classList.toggle("is-active", item.dataset.catalogCategory === slug);
    });
    document.querySelectorAll("[data-catalog-switch]").forEach((button) => {
      const active = button.dataset.catalogSwitch === slug;
      button.setAttribute("aria-expanded", String(active));
    });
  };

  const firstCategory = document.querySelector("[data-catalog-category]");
  if (firstCategory) activateCatalogPanel(firstCategory.dataset.catalogCategory);

  document.querySelectorAll("[data-catalog-switch]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      activateCatalogPanel(button.dataset.catalogSwitch);
    });
  });

  document.querySelectorAll("[data-catalog-category]").forEach((item) => {
    item.addEventListener("mouseenter", () => {
      if (!isMobile()) activateCatalogPanel(item.dataset.catalogCategory);
    });
  });

  document.addEventListener("click", (event) => {
    if (catalogDropdown && !catalogDropdown.contains(event.target)) {
      setMenuOpen(catalogMenu, catalogBtn, false);
    }
    if (sortDropdown && !sortDropdown.contains(event.target)) {
      setMenuOpen(sortMenu, sortBtn, false);
    }
    if (headerCart && !headerCart.contains(event.target)) {
      setMenuOpen(miniCart, cartBtn, false);
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeAll();
  });
});
