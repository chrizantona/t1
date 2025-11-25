/**
 * Evaluation result display component
 */
import React from "react";
import { QuestionAnswerEval, Question } from "../../types/questions";

interface Props {
  result: QuestionAnswerEval;
  question: Question;
  onNext?: () => void;
}

export const EvaluationResult: React.FC<Props> = ({ result, question, onNext }) => {
  const getScoreColor = (score: number) => {
    if (score >= 80) return "#4caf50"; // green
    if (score >= 50) return "#ff9800"; // orange
    return "#f44336"; // red
  };

  const getStatusText = (passed: boolean) => {
    return passed ? "✓ Решение принято" : "✗ Требуется доработка";
  };

  return (
    <div className="evaluation-result">
      <div className="result-header">
        <h2>{getStatusText(result.passed)}</h2>
        <div
          className="score-badge"
          style={{ backgroundColor: getScoreColor(result.score) }}
        >
          {result.score} / 100
        </div>
      </div>

      <div className="result-content">
        <div className="feedback-section">
          <h3>Обратная связь</h3>
          <p className="feedback-text">{result.short_feedback}</p>
        </div>

        {result.mistakes.length > 0 && (
          <div className="mistakes-section">
            <h3>Замечания</h3>
            <ul className="mistakes-list">
              {result.mistakes.map((mistake, index) => (
                <li key={index}>{mistake}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="question-info">
          <p>
            <strong>Категория:</strong> {question.category}
          </p>
          <p>
            <strong>Сложность:</strong> {question.difficulty}
          </p>
        </div>
      </div>

      {onNext && (
        <div className="result-actions">
          <button onClick={onNext} className="next-btn">
            Следующий вопрос
          </button>
        </div>
      )}
    </div>
  );
};
