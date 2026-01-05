document.addEventListener("DOMContentLoaded", () => {
    const forms = document.querySelectorAll("form");

    forms.forEach(form => {
        const btn = form.querySelector(".buy_button");
        if (!btn) return;

        form.addEventListener("submit", function(e){
            e.preventDefault();

            const url = form.action;
            const formData = new FormData(form);

            fetch(url, {
                method: "POST",
                body: formData,
                headers: { "X-Requested-With": "XMLHttpRequest" }
            })
            .then(() => {
                // создаём модалку один раз
                let modal = document.getElementById("cartModal");
                if (!modal) {
                    modal = document.createElement("div");
                    modal.id = "cartModal";
                    modal.className = "cart-modal";
                    modal.innerHTML = `
                        <div class="cart-modal-content">
                            <p>Товар добавлен в корзину!</p>
                            <p>Желаете продолжить покупки или перейти в корзину?</p>
                            <div class="cart-modal-buttons">
                                <button id="continueShopping" class="modal-btn">Продолжить покупки</button>
                                <button id="goToCart" class="modal-btn">Перейти в корзину</button>
                            </div>
                        </div>
                    `;
                    document.body.appendChild(modal);

                    // кнопки
                    document.getElementById("continueShopping").addEventListener("click", () => hideModal(modal));
                    document.getElementById("goToCart").addEventListener("click", () => window.location.href = "/basket/");

                    // закрытие по клику на overlay
                    modal.addEventListener("click", (e) => {
                        if (e.target === modal) hideModal(modal);
                    });
                }

                showModal(modal);
            })
            .catch(err => console.error(err));
        });
    });

    // функции для показа/скрытия модалки с анимацией
    function showModal(modal) {
        modal.classList.add("show");
        // авто-скрытие через 5 секунд
        setTimeout(() => hideModal(modal), 5000);
    }

    function hideModal(modal) {
        modal.classList.remove("show");
    }
});