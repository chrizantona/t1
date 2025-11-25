/**
 * Test page for questions system
 */
import React, { useState } from "react";
import { Question, QuestionAnswerEval } from "../types/questions";
import { getNextQuestion } from "../api/questions";
import { QuestionWorkspace } from "../components/questions/QuestionWorkspace";

export const QuestionsTestPage: React.FC = () => {
  const [question, setQuestion] = useState<Question | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [category, setCategory] = useState("algorithms");
  const [difficulty, setDifficulty] = useState("easy");

  const loadQuestion = async () => {
    setLoading(true);
    setError(null);

    try {
      const q = await getNextQuestion(category, difficulty);
      setQuestion(q);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка загрузки вопроса");
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = (result: QuestionAnswerEval) => {
    console.log("Question completed:", result);
  };

  const handleNext = () => {
    setQuestion(null);
    loadQuestion();
  };

  return (
    <div className="questions-test-page">
      <div className="page-header">
        <h1>Тестирование системы вопросов</h1>
      </div>

      {!question && (
        <div className="question-selector">
          <h2>Выберите параметры вопроса</h2>

          <div className="selector-group">
            <label>Категория:</label>
            <select value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="algorithms">Algorithms</option>
              <option value="frontend">Frontend</option>
              <option value="backend">Backend</option>
              <option value="data-science">Data Science</option>
            </select>
          </div>

          <div className="selector-group">
            <label>Сложность:</label>
            <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>

          <button onClick={loadQuestion} disabled={loading} className="load-btn">
            {loading ? "Загрузка..." : "Загрузить вопрос"}
          </button>

          {error && <div className="error-message">{error}</div>}
        </div>
      )}

      {question && (
        <div className="question-container">
          <QuestionWorkspace question={question} onComplete={handleComplete} />
          <button onClick={handleNext} className="change-question-btn">
            Сменить вопрос
          </button>
        </div>
      )}
    </div>
  );
};
