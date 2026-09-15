export const themes = Object.freeze([
  {
    id: "light",
    labelKey: "header.theme_light",
    icon: "☀️",
    rootClass: null,
    colorScheme: "light",
  },
  {
    id: "dark",
    labelKey: "header.theme_dark",
    icon: "🌙",
    rootClass: "dark",
    colorScheme: "dark",
  },
  {
    id: "dopamine",
    labelKey: "header.theme_dopamine",
    icon: "🌈",
    rootClass: "dopamine",
    colorScheme: "light",
  },
  {
    id: "high-contrast",
    labelKey: "header.theme_high_contrast",
    icon: "◐",
    rootClass: "high-contrast",
    colorScheme: "dark",
  },
]);

const themeIds = new Set(themes.map(({ id }) => id));

export function getInitialTheme() {
  const savedTheme = localStorage.getItem("theme");
  if (themeIds.has(savedTheme)) return savedTheme;

  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function applyTheme(themeId) {
  const theme = themes.find(({ id }) => id === themeId);
  if (!theme) return false;

  const root = document.documentElement;
  for (const { rootClass } of themes) {
    if (rootClass) root.classList.remove(rootClass);
  }
  if (theme.rootClass) root.classList.add(theme.rootClass);
  root.dataset.theme = theme.id;
  root.style.colorScheme = theme.colorScheme;
  return true;
}
