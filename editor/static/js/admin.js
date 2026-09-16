// Customisations of the Django admin: copy buttons for the "Build info" popover.
// Opening and closing the popover is handled by the native <details> element.

const COPIED_CLASS = "build-info__copy--copied";

const root = document.querySelector(".build-info");
const rows = [...root.querySelectorAll(".build-info__row")];

const valueOf = (row) => row.querySelector(".build-info__value").textContent;
const labelOf = (row) => row.querySelector(".build-info__label").textContent;
const allValues = () => rows.map((row) => `${labelOf(row)}: ${valueOf(row)}`).join("\n");

root.addEventListener("click", async ({ target }) => {
  const button = target.closest(".build-info__copy");
  if (!button || !navigator.clipboard) return;

  const row = button.closest(".build-info__row");
  await navigator.clipboard.writeText(row ? valueOf(row) : allValues());
  button.classList.add(COPIED_CLASS);
  setTimeout(() => button.classList.remove(COPIED_CLASS), 1500);
});

// Close the popover when clicking elsewhere or pressing Escape.
document.addEventListener("click", ({ target }) => {
  if (!root.contains(target)) root.open = false;
});
document.addEventListener("keydown", ({ key }) => {
  if (key === "Escape") root.open = false;
});
