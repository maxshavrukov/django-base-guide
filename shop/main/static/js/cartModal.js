document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("cartModal");

    function showToast() {
        if (!modal) return;

        modal.style.display = "block";
        modal.style.transition = "none";
        modal.style.opacity = "1";
        modal.style.transform = "translateX(0)";

        setTimeout(() => {
            modal.style.transition = "opacity 0.3s ease, transform 0.3s ease";
            modal.style.opacity = "0";
            modal.style.transform = "translateX(-20px)";

            setTimeout(() => {
                modal.style.display = "none";
            }, 300);
        }, 2500);
    }

    // 1. Добавление в корзину через AJAX
    document.addEventListener("submit", function (e) {
        const form = e.target;

        if (form.classList.contains("product_form") || form.action.includes("basket/add")) {
            e.preventDefault();

            const formData = new FormData(form);

            fetch(form.action, {
                method: "POST",
                body: formData,
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": getCookie('csrftoken')
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.status === "ok") {
                        showToast();
                        updateMiniCartUI(data);
                    }
                })
                .catch(error => console.error("Ошибка добавления в корзину:", error));
        }
    });

    // 2. Удаление из мини-корзины через AJAX (с использованием closest для надежности)
document.addEventListener("click", function (e) {
        const removeBtn = e.target.closest(".mini-cart-remove-btn");

        if (removeBtn) {
            e.preventDefault();
            e.stopPropagation();

            const productId = removeBtn.getAttribute("data-product_id");
            
            // БЕРЕМ ТОКЕН ЧЕРЕЗ НАШУ УТИЛИТУ ИЗ КУК
            const csrfToken = getCookie('csrftoken');

            fetch(`/basket/remove/${productId}/`, {
                method: "POST",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": csrfToken
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.status === "ok") {
                        updateMiniCartUI(data);
                    }
                })
                .catch(error => console.error("Ошибка удаления из корзины:", error));
        }
    });

// Функция обновления интерфейса шапки и мини-корзины
    function updateMiniCartUI(data) {
        // УПРАВЛЯЕМ КЛАССОМ ДЛЯ ХОВЕРА МИНИ-КОРЗИНЫ
        const headerCart = document.querySelector(".header_cart");
        if (headerCart) {
            if (data.basket_len > 0) {
                headerCart.classList.add("has-items");
            } else {
                headerCart.classList.remove("has-items");
                // Принудительно скрываем выпадашку, если удалили последний товар
                const dropdown = headerCart.querySelector(".mini-cart-dropdown");
                if (dropdown) dropdown.style.display = "none";
            }
        }

        const countElement = document.getElementById("cart-count");
        if (countElement) {
            countElement.textContent = data.basket_len > 0 ? data.basket_len : "";
        }

        const totalElement = document.getElementById("cart-total-price");
        if (totalElement && data.total_price !== undefined) {
            const numericPrice = parseFloat(data.total_price);
            totalElement.textContent = numericPrice > 0 ? numericPrice + " грн" : "";
        }

        const miniCartSum = document.getElementById("mini-cart-sum");
        if (miniCartSum && data.total_price !== undefined) {
            miniCartSum.textContent = data.total_price;
        }

        const itemsList = document.getElementById("mini-cart-items");
        const footer = document.getElementById("mini-cart-footer");

        if (itemsList) {
            if (data.items && data.items.length > 0) {
                if (footer) footer.style.display = "block";

                let itemsHtml = "";
                data.items.forEach(item => {
                    itemsHtml += `
                        <div class="mini-cart-item">
                            ${item.image_url ? `<img src="${item.image_url}" alt="${item.name}" class="mini-cart-img">` : `<div class="mini-cart-img" style="background: #eee;"></div>`}
                            <div class="mini-cart-info">
                                <div class="mini-cart-title" title="${item.name}">${item.name}</div>
                                <div class="mini-cart-details">${item.quantity} шт. × ${item.price} грн</div>
                            </div>
                            <button type="button" class="mini-cart-remove-btn" data-product_id="${item.product_id}" title="Удалить товар">&times;</button>
                        </div>
                    `;
                });
                itemsList.innerHTML = itemsHtml;
            } else {
                if (footer) footer.style.display = "none";
                itemsList.innerHTML = '';
            }
        }
    }
});