document.querySelectorAll("[data-quiz]").forEach((quiz) => {
  const button = quiz.querySelector("button");
  const feedback = quiz.querySelector(".feedback");

  button.addEventListener("click", () => {
    const answer = quiz.querySelector("input[type='radio']:checked");

    if (!answer) {
      feedback.textContent = "Choose one answer first.";
      feedback.dataset.state = "incorrect";
      return;
    }

    const correct = answer.dataset.correct === "true";
    feedback.textContent = correct
      ? "Correct — send the token in the Authorization header."
      : "Try again — query-string keys were removed in v3.0.";
    feedback.dataset.state = correct ? "correct" : "incorrect";
  });
});
