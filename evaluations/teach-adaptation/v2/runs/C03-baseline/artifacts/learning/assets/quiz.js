function initializeQuiz(quiz) {
  const options = [...quiz.querySelectorAll("[data-answer]")];
  const feedback = quiz.querySelector("[data-feedback]");
  const reset = quiz.querySelector("[data-reset]");

  const clear = () => {
    for (const option of options) {
      option.disabled = false;
      delete option.dataset.result;
    }
    feedback.textContent = "Choose one answer, then get immediate feedback.";
    delete feedback.dataset.kind;
    reset.hidden = true;
  };

  for (const option of options) {
    option.addEventListener("click", () => {
      const isCorrect = option.dataset.answer === "correct";

      for (const candidate of options) {
        candidate.disabled = true;
      }

      option.dataset.result = isCorrect ? "correct" : "incorrect";
      feedback.dataset.kind = isCorrect ? "correct" : "incorrect";
      feedback.textContent = isCorrect
        ? quiz.dataset.correctFeedback
        : quiz.dataset.incorrectFeedback;
      reset.hidden = false;
    });
  }

  reset.addEventListener("click", clear);
  clear();
}

for (const quiz of document.querySelectorAll("[data-quiz]")) {
  initializeQuiz(quiz);
}
