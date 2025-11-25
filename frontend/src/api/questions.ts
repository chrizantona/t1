/**
 * API client for tech questions
 */
import { Question, QuestionAnswerEval, SubmitAnswerRequest } from "../types/questions";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function getNextQuestion(
  category: string,
  difficulty: string
): Promise<Question> {
  const response = await fetch(
    `${API_BASE}/api/questions/next?category=${category}&difficulty=${difficulty}`
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch question: ${response.statusText}`);
  }

  return response.json();
}

export async function submitQuestionAnswer(
  questionId: number,
  answerCode?: string,
  answerText?: string
): Promise<QuestionAnswerEval> {
  const payload: SubmitAnswerRequest = {
    question_id: questionId,
    answer_code: answerCode || null,
    answer_text: answerText || null,
  };

  const response = await fetch(`${API_BASE}/api/questions/${questionId}/answer`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Failed to submit answer: ${response.statusText}`);
  }

  return response.json();
}
