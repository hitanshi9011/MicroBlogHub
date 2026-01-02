// Character counter for post textarea
document.addEventListener("DOMContentLoaded", () => {
  const textarea = document.querySelector("textarea");
  const counter = document.getElementById("charCount");

  if (textarea && counter) {
    textarea.addEventListener("input", () => {
      counter.textContent = `${textarea.value.length} / 280`;
    });
  }
});
