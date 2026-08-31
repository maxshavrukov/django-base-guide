document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".quantity-box").forEach((box) => {
    const minusBtn = box.querySelector(".minus");
    const plusBtn = box.querySelector(".plus");
    const input = box.querySelector(".quantity-input");

    if (!minusBtn || !plusBtn || !input) return;

    const getBounds = () => ({
      min: Number(input.min) || 1,
      max: Number(input.max) || 20,
    });

    const normalize = () => {
      const { min, max } = getBounds();
      let value = Number.parseInt(input.value, 10);
      if (Number.isNaN(value)) value = min;
      input.value = Math.min(Math.max(value, min), max);
    };

    minusBtn.addEventListener("click", () => {
      normalize();
      const { min } = getBounds();
      input.value = Math.max(Number(input.value) - 1, min);
    });

    plusBtn.addEventListener("click", () => {
      normalize();
      const { max } = getBounds();
      input.value = Math.min(Number(input.value) + 1, max);
    });

    input.addEventListener("change", normalize);
  });
});
