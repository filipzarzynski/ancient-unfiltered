const filterButtons = document.querySelectorAll(".filter-button");
const examples = document.querySelectorAll(".example");

function setActiveFilter(nextFilter) {
  filterButtons.forEach((button) => {
    const isActive = button.dataset.filter === nextFilter;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-pressed", String(isActive));
  });

  examples.forEach((example) => {
    const shouldShow = nextFilter === "all" || example.dataset.theme === nextFilter;
    example.hidden = !shouldShow;
  });
}

filterButtons.forEach((button) => {
  button.setAttribute("aria-pressed", button.classList.contains("active") ? "true" : "false");
  button.addEventListener("click", () => setActiveFilter(button.dataset.filter));
});
