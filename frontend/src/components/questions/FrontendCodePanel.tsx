/**
 * Frontend code panel for React/TypeScript questions
 */
import React, { useState } from "react";
import { Question } from "../../types/questions";

interface Props {
  question: Question;
  onSubmit: (code: string) => void;
  isSubmitting: boolean;
}

export const FrontendCodePanel: React.FC<Props> = ({ question, onSubmit, isSubmitting }) => {
  const [code, setCode] = useState("");

  const handleSubmit = () => {
    if (code.trim()) {
      onSubmit(code);
    }
  };

  return (
    <div className="frontend-code-panel">
      <div className="question-header">
        <h3>Задание (React/TypeScript)</h3>
        <span className="difficulty-badge">{question.difficulty}</span>
      </div>

      <div className="question-text">
        <p>{question.question_text}</p>
      </div>

      <div className="code-editor">
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="// Напишите ваше решение здесь..."
          className="code-textarea"
          spellCheck={false}
        />
      </div>

      <div className="panel-actions">
        <button
          onClick={handleSubmit}
          disabled={!code.trim() || isSubmitting}
          className="submit-btn"
        >
          {isSubmitting ? "Проверка..." : "Отправить решение"}
        </button>
      </div>
    </div>
  );
};

// пидормот
