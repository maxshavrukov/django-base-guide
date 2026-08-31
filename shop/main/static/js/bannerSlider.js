document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".hero-slider").forEach((container) => {
    const slides = [...container.querySelectorAll(".banner-slide")];
    const dotsContainer = container.querySelector(".banner-dots");

    if (slides.length <= 1) {
      if (dotsContainer) dotsContainer.hidden = true;
      return;
    }

    let currentIndex = 0;
    let timer;

    const dots = slides.map((_, index) => {
      const dot = document.createElement("button");
      dot.type = "button";
      dot.className = "banner-dot";
      dot.setAttribute("aria-label", `Показать слайд ${index + 1}`);
      dot.addEventListener("click", (event) => {
        event.preventDefault();
        showSlide(index);
        restart();
      });
      dotsContainer?.appendChild(dot);
      return dot;
    });

    function showSlide(index) {
      currentIndex = (index + slides.length) % slides.length;
      slides.forEach((slide, i) => slide.classList.toggle("active", i === currentIndex));
      dots.forEach((dot, i) => dot.classList.toggle("active", i === currentIndex));
    }

    function start() {
      timer = window.setInterval(() => showSlide(currentIndex + 1), 5000);
    }

    function restart() {
      window.clearInterval(timer);
      start();
    }

    container.addEventListener("mouseenter", () => window.clearInterval(timer));
    container.addEventListener("mouseleave", start);

    showSlide(0);
    start();
  });
});
