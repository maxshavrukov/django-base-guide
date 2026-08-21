document.addEventListener("DOMContentLoaded", () => {

    const quantityBoxes = document.querySelectorAll(".quantity_box");

    quantityBoxes.forEach(box => {

        const minusBtn = box.querySelector(".minus");
        const plusBtn = box.querySelector(".plus");
        const input = box.querySelector(".quantity_input");

        minusBtn.addEventListener("click", () => {
            let value = parseInt(input.value);

            if (value > 1) {
                input.value = value - 1;
            }
        });

        plusBtn.addEventListener("click", () => {
            let value = parseInt(input.value);

            if (value < 20) {
                input.value = value + 1;
            }
        });

    });

});