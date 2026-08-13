document.querySelectorAll("[data-quiz]").forEach((quiz) => {
  const button = quiz.querySelector("[data-check-answer]");
  const feedback = quiz.querySelector("[data-feedback]");

  button.addEventListener("click", () => {
    const selected = quiz.querySelector("input[type='radio']:checked");

    if (!selected) {
      feedback.hidden = false;
      feedback.className = "feedback incorrect";
      feedback.textContent = "Choose one diagnosis first; guessing is part of the practice.";
      return;
    }

    const correct = selected.value === quiz.dataset.answer;
    feedback.hidden = false;
    feedback.className = `feedback ${correct ? "correct" : "incorrect"}`;
    feedback.textContent = correct
      ? quiz.dataset.correctFeedback
      : quiz.dataset.incorrectFeedback;
  });
});
