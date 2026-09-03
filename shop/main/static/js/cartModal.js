document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("cartModal");

  function showToast() {
    if (!modal) return;
    modal.style.display = "flex";
    modal.style.opacity = "1";
    modal.style.transform = "translateX(0)";
    window.setTimeout(() => {
      modal.style.opacity = "0";
      modal.style.transform = "translateX(-20px)";
      window.setTimeout(() => { modal.style.display = "none"; }, 300);
    }, 2200);
  }

  async function requestJson(url, options) {
    const response = await fetch(url, options);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  const preserveMiniCartOpen = () => {
    const miniCart = document.getElementById("miniCart");
    const cartBtn = document.getElementById("cartBtn");
    if (miniCart && cartBtn && miniCart.classList.contains("is-open")) {
      miniCart.hidden = false;
      cartBtn.setAttribute("aria-expanded", "true");
    }
  };

  document.addEventListener("submit", async (event) => {
    const form = event.target;
    if (!form.matches(".product-form") && !form.action.includes("/basket/add/")) return;

    event.preventDefault();
    try {
      const data = await requestJson(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": getCookie("csrftoken"),
        },
      });
      if (data.status === "ok") {
        showToast();
        updateMiniCartUI(data);
      }
    } catch (error) {
      console.error("Ошибка добавления в корзину:", error);
    }
  });

  document.addEventListener("click", async (event) => {
    const removeBtn = event.target.closest(".mini-cart-remove-btn");
    if (!removeBtn) return;

    event.preventDefault();
    event.stopPropagation();

    const productId = removeBtn.dataset.product_id;
    if (!productId) return;

    try {
      const data = await requestJson(`/basket/remove/${productId}/`, {
        method: "POST",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": getCookie("csrftoken"),
        },
      });
      if (data.status === "ok") {
        updateMiniCartUI(data);
        preserveMiniCartOpen();
      }
    } catch (error) {
      console.error("Ошибка удаления из корзины:", error);
    }
  });

 function updateMiniCartUI(data) {
    const headerCart = document.querySelector(".header-cart");
    if (headerCart) headerCart.classList.toggle("has-items", data.basket_len > 0);
    // Берем количество из ответа сервера (data.basket_len)
    const totalQty = data.basket_len || 0;
    const countElement = document.getElementById("cart-count");
    if (countElement) {
      countElement.textContent = totalQty > 0 ? totalQty : "";
    }

    const totalElement = document.getElementById("cart-total-price");
    if (totalElement) totalElement.textContent = Number(data.total_price) > 0 ? `${data.total_price} грн` : "";

    const miniCartSum = document.getElementById("mini-cart-sum");
    const miniCartSubtotal = document.getElementById("mini-cart-subtotal");
    const miniCartProductDiscount = document.getElementById("mini-cart-product-discount");
    const miniCartPromoDiscount = document.getElementById("mini-cart-promo-discount");
    const miniCartProductDiscountRow = document.getElementById("mini-cart-product-discount-row");
    const miniCartPromoRow = document.getElementById("mini-cart-promo-row");

    if (miniCartSum) miniCartSum.textContent = data.total_price || "0.00";
    if (miniCartSubtotal) miniCartSubtotal.textContent = data.subtotal || "0.00";
    if (miniCartProductDiscount) miniCartProductDiscount.textContent = data.product_discount_amount || "0.00";
    if (miniCartPromoDiscount) miniCartPromoDiscount.textContent = data.promo_discount_amount || "0.00";
    if (miniCartProductDiscountRow) miniCartProductDiscountRow.hidden = Number(data.product_discount_amount || 0) <= 0;
    if (miniCartPromoRow) miniCartPromoRow.hidden = Number(data.promo_discount_amount || 0) <= 0;

    const itemsList = document.getElementById("mini-cart-items");
    const footer = document.getElementById('mini-cart-footer');
    if (!itemsList) return;

    if (data.items && data.items.length) {
      if (footer) footer.style.display = "";

      itemsList.innerHTML = data.items.map((item) => `
        <div class="mini-cart-item">
          ${item.image_url ? `<img src="${item.image_url}" alt="${escapeHtml(item.name)}" class="mini-cart-img">` : `<div class="mini-cart-img"></div>`}
          <div class="mini-cart-info">
            <div class="mini-cart-title" title="${escapeHtml(item.name)}">${escapeHtml(item.name)}</div>
            <div class="mini-cart-details">
              <span>${item.quantity} шт. × ${item.price} грн</span>
              ${Number(item.product_discount_percent) > 0 ? `<span class="mini-cart-discount">−${item.product_discount_percent}% · было ${item.original_price} грн</span>` : ""}
            </div>
          </div>
          <button type="button" class="mini-cart-remove-btn" data-product_id="${item.product_id}" title="Удалить товар" aria-label="Удалить товар">
            <svg aria-hidden="true" viewBox="0 0 24 24" fill="none"><path d="M6 6l12 12M18 6 6 18" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
          </button>
        </div>`).join("");
    } else {
      if (footer) footer.style.display = "none";

      itemsList.innerHTML = `
        <div class="mini-cart-empty">
          <span class="mini-cart-empty__icon"><svg aria-hidden="true" viewBox="0 0 24 24" fill="none"><path d="M4 5h2l1.2 9.1a2 2 0 0 0 2 1.9h7.6a2 2 0 0 0 2-1.7L20 8H7" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg></span>
          <strong>Корзина пуста</strong><span>Добавьте что-нибудь из каталога</span>
        </div>`;
    }
  }

  function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = value ?? "";
    return div.innerHTML;
  }
});
