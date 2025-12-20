/**
 * Question workspace - renders appropriate panel based on question type
 */
import React, { useState } from "react";
import { Question, QuestionAnswerEval } from "../../types/questions";
import { submitQuestionAnswer } from "../../api/questions";
import { PythonCodePanel } from "./PythonCodePanel";
import { FrontendCodePanel } from "./FrontendCodePanel";
import { BackendCodePanel } from "./BackendCodePanel";
import { DataSciencePanel } from "./DataSciencePanel";
import { TextAnswerPanel } from "./TextAnswerPanel";
import { EvaluationResult } from "./EvaluationResult";

interface Props {
  question: Question;
  onComplete?: (result: QuestionAnswerEval) => void;
}

export const QuestionWorkspace: React.FC<Props> = ({ question, onComplete }) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<QuestionAnswerEval | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (code?: string, text?: string) => {
    setIsSubmitting(true);
    setError(null);

    try {
      const evaluation = await submitQuestionAnswer(question.id, code, text);
      setResult(evaluation);
      onComplete?.(evaluation);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка при проверке ответа");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCodeSubmit = (code: string) => {
    handleSubmit(code, undefined);
  };

  const handleTextSubmit = (text: string) => {
    handleSubmit(undefined, text);
  };

  // Show result if available
  if (result) {
    return <EvaluationResult result={result} question={question} />;
  }

  // Show error if any
  if (error) {
    return (
      <div className="error-panel">
        <h3>Ошибка</h3>
        <p>{error}</p>
        <button onClick={() => setError(null)}>Попробовать снова</button>
      </div>
    );
  }

  // Render appropriate panel based on question type
  switch (question.panel_type) {
    case "code_python":
      return (
        <PythonCodePanel
          question={question}
          onSubmit={handleCodeSubmit}
          isSubmitting={isSubmitting}
        />
      );

    case "code_frontend":
      return (
        <FrontendCodePanel
          question={question}
          onSubmit={handleCodeSubmit}
          isSubmitting={isSubmitting}
        />
      );

    case "code_backend":
      return (
        <BackendCodePanel
          question={question}
          onSubmit={handleCodeSubmit}
          isSubmitting={isSubmitting}
        />
      );

    case "code_ds":
      return (
        <DataSciencePanel
          question={question}
          onSubmit={handleCodeSubmit}
          isSubmitting={isSubmitting}
        />
      );

    case "text_only":
    default:
      return (
        <TextAnswerPanel
          question={question}
          onSubmit={handleTextSubmit}
          isSubmitting={isSubmitting}
        />
      );
  }
};

// пидормот
