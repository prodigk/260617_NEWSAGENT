const refreshForms = document.querySelectorAll('form[action="/refresh"]');

refreshForms.forEach((form) => {
  form.addEventListener("submit", () => {
    const button = form.querySelector("button");
    if (button) {
      button.disabled = true;
      button.textContent = "불러오는 중...";
    }
  });
});

document.querySelectorAll(".pagination a").forEach((link) => {
  link.addEventListener("click", () => {
    const grid = document.querySelector("#editorial-grid");
    if (grid) {
      grid.setAttribute("aria-busy", "true");
    }
  });
});

const menuButton = document.querySelector(".menu-button");
const mainNav = document.querySelector("#main-nav");

if (menuButton && mainNav) {
  menuButton.addEventListener("click", () => {
    const isOpen = mainNav.classList.toggle("is-open");
    menuButton.setAttribute("aria-expanded", String(isOpen));
    menuButton.setAttribute("aria-label", isOpen ? "메뉴 닫기" : "메뉴 열기");
  });
}
