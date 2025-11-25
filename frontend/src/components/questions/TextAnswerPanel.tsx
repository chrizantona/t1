/**
 * Text answer panel for theory questions
 */
import React, { useState } from "react";
import { Question } from "../../types/questions";

interface Props {
  question: Question;
  onSubmit: (text: string) => void;
  isSubmitting: boolean;
}

export const TextAnswerPanel: React.FC<Props> = ({ question, onSubmit, isSubmitting }) => {
  const [text, setText] = useState("");

  const handleSubmit = () => {
    if (text.trim()) {
      onSubmit(text);
    }
  };

  return (
    <div className="text-answer-panel">
      <div className="question-header">
        <h3>Теоретический вопрос</h3>
        <span className="difficulty-badge">{question.difficulty}</span>
      </div>

      <div className="question-text">
        <p>{question.question_text}</p>
      </div>

      <div className="text-editor">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Напишите ваш ответ здесь..."
          className="text-textarea"
          rows={10}
        />
      </div>

      <div className="panel-actions">
        <button
          onClick={handleSubmit}
          disabled={!text.trim() || isSubmitting}
          className="submit-btn"
        >
          {isSubmitting ? "Проверка..." : "Отправить ответ"}
        </button>
      </div>
    </div>
  );
};
