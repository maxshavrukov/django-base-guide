document.addEventListener("DOMContentLoaded", function () {
  const container = document.querySelector(".banner_slider_container");
  if (!container) return;

  const slides = container.querySelectorAll(".banner_slide");
  const dotsContainer = container.querySelector(".banner_dots");

  if (slides.length <= 1) {
    if (dotsContainer) dotsContainer.style.display = "none";
    return;
  }

  let currentIndex = 0;
  let autoSlideTimer = null;

  // Очищаем контейнер перед генерацией точек
  dotsContainer.innerHTML = "";

  // Генерируем точки
  slides.forEach((_, index) => {
    const dot = document.createElement("button");
    dot.classList.add("banner_dot");
    if (index === 0) dot.classList.add("active");
    dot.setAttribute("type", "button");

    dot.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      showSlide(index);
      resetAutoSlide();
    });

    dotsContainer.appendChild(dot);
  });

  const dots = dotsContainer.querySelectorAll(".banner_dot");

  function showSlide(index) {
    slides.forEach((slide) => slide.classList.remove("active"));
    dots.forEach((dot) => dot.classList.remove("active"));

    currentIndex = (index + slides.length) % slides.length;
    slides[currentIndex].classList.add("active");
    dots[currentIndex].classList.add("active");
  }

  function startAutoSlide() {
    autoSlideTimer = setInterval(() => showSlide(currentIndex + 1), 5000);
  }

  function resetAutoSlide() {
    clearInterval(autoSlideTimer);
    startAutoSlide();
  }

  startAutoSlide();
});