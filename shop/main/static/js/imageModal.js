document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("imageModal");
  const openBtn = document.getElementById("openImageModal");
  const closeBtn = document.getElementById("closeImageModal");
  const mainImg = document.getElementById("mainProductImg");
  const modalImg = document.getElementById("modalImg");
  const thumbnails = document.querySelectorAll(".gallery-thumbnail");
  const modalPrev = document.getElementById("modalImagePrev");
  const modalNext = document.getElementById("modalImageNext");
  const galleryPrev = document.querySelector(".product-main-image .gallery-nav--prev");
  const galleryNext = document.querySelector(".product-main-image .gallery-nav--next");

  if (!modal || !openBtn || !closeBtn) return;

  let currentIndex = 0;
  const images = Array.from(thumbnails).map(thumb => ({
    url: thumb.getAttribute("data-image-url"),
    alt: thumb.getAttribute("data-image-alt") || ""
  }));

  if (images.length === 0 && mainImg) {
    images.push({ url: mainImg.src, alt: mainImg.alt });
  }

  function updateGallery(index) {
    if (images.length === 0) return;
    currentIndex = (index + images.length) % images.length;
    
    const current = images[currentIndex];
    
    if (mainImg) {
      mainImg.src = current.url;
      mainImg.alt = current.alt;
    }
    if (modalImg) {
      modalImg.src = current.url;
      modalImg.alt = current.alt;
    }

    thumbnails.forEach((thumb, i) => {
      if (i === currentIndex) {
        thumb.classList.add("is-active");
        thumb.setAttribute("aria-current", "true");
      } else {
        thumb.classList.remove("is-active");
        thumb.setAttribute("aria-current", "false");
      }
    });

    const hasMultiple = images.length > 1;
    if (galleryPrev) galleryPrev.hidden = !hasMultiple;
    if (galleryNext) galleryNext.hidden = !hasMultiple;
    if (modalPrev) modalPrev.hidden = !hasMultiple;
    if (modalNext) modalNext.hidden = !hasMultiple;
  }

  if (galleryPrev) galleryPrev.addEventListener("click", (e) => { e.stopPropagation(); updateGallery(currentIndex - 1); });
  if (galleryNext) galleryNext.addEventListener("click", (e) => { e.stopPropagation(); updateGallery(currentIndex + 1); });

  thumbnails.forEach((thumb, index) => {
    thumb.addEventListener("click", () => updateGallery(index));
  });

  if (modalPrev) {
    modalPrev.addEventListener("click", (e) => {
      e.stopPropagation();
      updateGallery(currentIndex - 1);
    });
  }

  if (modalNext) {
    modalNext.addEventListener("click", (e) => {
      e.stopPropagation();
      updateGallery(currentIndex + 1);
    });
  }

  const close = () => {
    modal.style.display = "none";
    modal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("modal-open");
  };

  const open = () => {
    modal.style.display = "flex";
    modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("modal-open");
    updateGallery(currentIndex);
  };

  openBtn.addEventListener("click", (event) => {
    if (!event.target.closest(".gallery-nav")) open();
  });

  openBtn.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      open();
    }
  });

  closeBtn.addEventListener("click", close);

  modal.addEventListener("click", (event) => {
    if (event.target === modal) close();
  });

  document.addEventListener("keydown", (event) => {
    if (modal.style.display !== "none") {
      if (event.key === "Escape") close();
      if (event.key === "ArrowLeft") updateGallery(currentIndex - 1);
      if (event.key === "ArrowRight") updateGallery(currentIndex + 1);
    }
  });

  if (images.length > 0) {
    updateGallery(0);
  }
});