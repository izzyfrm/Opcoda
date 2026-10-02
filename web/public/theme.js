// Apply the saved theme before first paint (external file so the CSP can forbid inline scripts).
try {
  const theme = localStorage.getItem("opcoda-theme");
  if (theme === "light" || theme === "dark") document.documentElement.dataset.theme = theme;
} catch {
  // storage unavailable: follow the system theme
}
