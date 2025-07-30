# services/__init__.py

# --- 從 ai.py 匯出 ---
from .ai import (
    generate_test_from_ai,
    get_overall_feedback_from_ai,
    get_single_question_feedback_from_ai,
    evaluate_essay_with_ai,
    generate_test_stream_from_ai
)

# --- 從 database.py 匯出 ---
from .database import (
    get_test_paper_by_id,
    create_test_paper,
    get_question_by_id,
    get_test_result_by_id,
    get_all_test_results,
    get_test_result,
    delete_test_result
)

# --- 從 grading.py 匯出 ---
# GRADING_STRATEGIES 也可能被外部使用，所以匯出
from .grading import (
    GRADING_STRATEGIES,
    grade_objective_question,
    get_formatted_user_answer
)

# --- 從 orchestration.py 匯出 ---
from .orchestration import (
    grade_and_save_test,
    generate_and_save_overall_feedback,
    generate_and_save_single_question_feedback
)

# 使用 __all__ 來定義公開的 API 介面
__all__ = [
    # AI Services
    'generate_test_from_ai',
    'get_overall_feedback_from_ai',
    'get_single_question_feedback_from_ai',
    'evaluate_essay_with_ai',
    'generate_test_stream_from_ai',

    # Database Services
    'get_test_paper_by_id',
    'create_test_paper',
    'get_question_by_id',
    'get_test_result_by_id',
    'get_all_test_results',
    'get_test_result',
    'delete_test_result',

    # Grading Logic
    'GRADING_STRATEGIES',
    'grade_objective_question',
    'get_formatted_user_answer',
    
    # Orchestration Services
    'grade_and_save_test',
    'generate_and_save_overall_feedback',
    'generate_and_save_single_question_feedback'
]