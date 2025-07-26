# schemas/__init__.py

from .test_generation import (
    QuestionConfig,
    GenerateTestConfig,
    SingleChoiceAnswer,
    MultipleChoiceAnswer,
    FillInTheBlankAnswer,
    EssayAnswer,
    QuestionModel,
    GenerateTestResponse,
)
from .test_grading import (
    UserAnswer,
    GradeQuestionsRequest,
    ObjectiveGradeResult,
    EssayGradeResult,
    GradeQuestionsResponse,
)
from .feedback import (
    GenerateOverallFeedbackRequest,
    GenerateOverallFeedbackResponse,
    GenerateSingleQuestionFeedbackRequest,
    GenerateSingleQuestionFeedbackResponse,
)
from .essay_evaluation import (
    QuestionInfo,
    EvaluateShortAnswerRequest,
    EvaluateShortAnswerResponse,
)
from .history import (
    TestPaper,
    TestPaperResult,
)

__all__ = [
    # Test Generation
    "QuestionConfig",
    "GenerateTestConfig",
    "SingleChoiceAnswer",
    "MultipleChoiceAnswer",
    "FillInTheBlankAnswer",
    "EssayAnswer",
    "QuestionModel",
    "GenerateTestResponse",
    # Test Grading
    "UserAnswer",
    "GradeQuestionsRequest",
    "ObjectiveGradeResult",
    "EssayGradeResult",
    "GradeQuestionsResponse",
    # Feedback
    "GenerateOverallFeedbackRequest",
    "GenerateOverallFeedbackResponse",
    "GenerateSingleQuestionFeedbackRequest",
    "GenerateSingleQuestionFeedbackResponse",
    # Essay Evaluation
    "QuestionInfo",
    "EvaluateShortAnswerRequest",
    "EvaluateShortAnswerResponse",
    # History
    "TestPaper",
    "TestPaperResult",
]