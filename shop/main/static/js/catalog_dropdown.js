document.addEventListener('DOMContentLoaded', function() {
  const catalogDropdown = document.querySelector('.catalog_dropdown');
  const catalogBtn = document.getElementById('catalogBtn');
  const catalogMenu = document.getElementById('catalogMenu');

  if (catalogBtn && catalogMenu) {
    catalogBtn.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      catalogMenu.classList.toggle('is-open');
    });

    document.addEventListener('click', function(e) {
      if (!catalogDropdown.contains(e.target)) {
        catalogMenu.classList.remove('is-open');
      }
    });

    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' || e.key === 'Esc') {
        catalogMenu.classList.remove('is-open');
      }
    });
  }
});