(function teachQuiz(globalScope) {
  "use strict";

  function shuffle(items, random) {
    const shuffled = Array.from(items);
    const nextRandom = random || Math.random;

    for (let index = shuffled.length - 1; index > 0; index -= 1) {
      const swapIndex = Math.floor(nextRandom() * (index + 1));
      [shuffled[index], shuffled[swapIndex]] = [
        shuffled[swapIndex],
        shuffled[index],
      ];
    }
    return shuffled;
  }

  function randomizeOptions(container, random) {
    const options = container.querySelectorAll(":scope > [data-option-id]");
    shuffle(options, random).forEach((option) => container.appendChild(option));
  }

  function initialize(root) {
    root
      .querySelectorAll("[data-teach-options]")
      .forEach((container) => randomizeOptions(container));
  }

  const api = { initialize, randomizeOptions, shuffle };
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (globalScope) {
    globalScope.TeachQuiz = api;
  }
  if (typeof document !== "undefined") {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", () => initialize(document));
    } else {
      initialize(document);
    }
  }
})(typeof globalThis === "undefined" ? undefined : globalThis);
