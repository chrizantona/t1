/**
 * Types for tech questions and LLM evaluation
 */

export type PanelType =
  | "code_python"
  | "code_frontend"
  | "code_backend"
  | "code_ds"
  | "text_only";

export type QuestionCategory = "algorithms" | "frontend" | "backend" | "data-science";
export type QuestionDifficulty = "easy" | "medium" | "hard";

export interface Question {
  id: number;
  category: string;
  difficulty: string;
  question_text: string;
  panel_type: PanelType;
  language_hint?: string | null;
}

export interface QuestionAnswerEval {
  score: number; // 0-100
  passed: boolean;
  short_feedback: string;
  mistakes: string[];
}

export interface SubmitAnswerRequest {
  question_id: number;
  answer_code?: string | null;
  answer_text?: string | null;
}

// пидормот
