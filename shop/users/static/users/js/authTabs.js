document.addEventListener("DOMContentLoaded", function () {
  const tabLogin = document.getElementById("tab-login");
  const tabRegister = document.getElementById("tab-register");
  const formLogin = document.getElementById("form-login");
  const formRegister = document.getElementById("form-register");

  if (!tabLogin || !tabRegister) return;

  function activateTab(tab) {
    if (tab === "register") {
      // Показываем регистрацию
      formLogin.classList.remove("active");
      formRegister.classList.add("active");

      tabLogin.classList.remove("active");
      tabRegister.classList.add("active");
    } else {
      // Показываем вход
      formRegister.classList.remove("active");
      formLogin.classList.add("active");

      tabRegister.classList.remove("active");
      tabLogin.classList.add("active");
    }
  }

  // Клики по вкладкам
  tabLogin.addEventListener("click", () => activateTab("login"));
  tabRegister.addEventListener("click", () => activateTab("register"));

  // Проверяем параметр ?tab=register в URL (для клика с баннера)
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get("tab") === "register") {
    activateTab("register");
  }
});