const toggles = [...document.querySelectorAll(".node-toggle")];
const progressBar = document.querySelector(".reading-progress span");

function setNodeState(toggle, expanded) {
  const detailId = toggle.getAttribute("aria-controls");
  const detail = document.getElementById(detailId);

  if (!detail) return;

  toggle.setAttribute("aria-expanded", String(expanded));
  detail.hidden = !expanded;
}

toggles.forEach((toggle) => {
  toggle.addEventListener("click", () => {
    const isExpanded = toggle.getAttribute("aria-expanded") === "true";
    setNodeState(toggle, !isExpanded);
  });
});

document.querySelector('[data-action="expand-all"]').addEventListener("click", () => {
  toggles.forEach((toggle) => setNodeState(toggle, true));
});

document.querySelector('[data-action="collapse-all"]').addEventListener("click", () => {
  toggles.forEach((toggle) => setNodeState(toggle, false));
  document.getElementById("nodes").scrollIntoView({ block: "start", behavior: "smooth" });
});

function updateReadingProgress() {
  const scrollable = document.documentElement.scrollHeight - window.innerHeight;
  const progress = scrollable > 0 ? Math.min(window.scrollY / scrollable, 1) : 0;
  progressBar.style.width = `${progress * 100}%`;
}

window.addEventListener("scroll", updateReadingProgress, { passive: true });
window.addEventListener("resize", updateReadingProgress);
updateReadingProgress();
