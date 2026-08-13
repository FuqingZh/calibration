const quizzes = document.querySelectorAll("[data-quiz]");

for (const quiz of quizzes) {
  const feedback = quiz.querySelector("[data-quiz-feedback]");
  const status = quiz.querySelector("[data-quiz-status]");
  const explanation = quiz.querySelector("[data-quiz-explanation]");
  const options = [...quiz.querySelectorAll("input[type='radio']")];

  quiz.addEventListener("submit", (event) => {
    event.preventDefault();

    const choice = options.find((option) => option.checked);
    feedback.hidden = false;

    for (const option of options) {
      delete option.closest(".quiz-option").dataset.state;
    }

    if (!choice) {
      feedback.dataset.state = "prompt";
      status.textContent = "Choose one answer first.";
      explanation.hidden = true;
      return;
    }

    const isCorrect = choice.value === quiz.dataset.correct;
    const correctOption = options.find(
      (option) => option.value === quiz.dataset.correct,
    );

    feedback.dataset.state = isCorrect ? "correct" : "incorrect";
    status.textContent = isCorrect
      ? quiz.dataset.correctMessage
      : quiz.dataset.incorrectMessage;
    explanation.hidden = false;
    choice.closest(".quiz-option").dataset.state = isCorrect
      ? "correct"
      : "incorrect";
    correctOption.closest(".quiz-option").dataset.state = "correct";
  });

  quiz.addEventListener("reset", () => {
    feedback.hidden = true;
    explanation.hidden = false;
    delete feedback.dataset.state;

    for (const option of options) {
      delete option.closest(".quiz-option").dataset.state;
    }
  });
}
