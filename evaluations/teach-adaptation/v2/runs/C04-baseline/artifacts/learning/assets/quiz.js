document.querySelectorAll("[data-quiz]").forEach((quiz) => {
  const feedback = quiz.querySelector("[data-feedback]");

  quiz.querySelectorAll("button[data-answer]").forEach((button) => {
    button.addEventListener("click", () => {
      const correct = button.dataset.answer === "correct";
      feedback.className = correct ? "correct" : "incorrect";
      feedback.textContent = correct
        ? quiz.dataset.correctFeedback
        : quiz.dataset.incorrectFeedback;
    });
  });
});
