"""
agents_app/orchestrator.py - Deterministic Pipeline Runner
"""

from typing import Dict, Any, List
from agents_app.evaluator_agent import generate_quiz_with_evaluator, QuizSet
from agents_app.controller_agent import process_quiz_submission
from core.calculator import sanitize_and_evaluate_answer
from core.state import load_state


def get_current_system_state() -> Dict[str, Any]:
    """
    Fetch current device state (applies 9 AM rollover if needed).
    """
    return load_state()


def generate_new_quiz(level: int = None, is_practice: bool = False) -> Dict[str, Any]:
    """
    Generate 10-question quiz for the requested level (or current state level).
    """
    state = load_state()
    if level is None:
        level = state.get("current_level", 1)

    quiz_set: QuizSet = generate_quiz_with_evaluator(level, is_practice=is_practice)
    return quiz_set.model_dump()


def grade_and_process_submission(student_answers: Dict[int, str], quiz_dict: Dict[str, Any], is_practice: bool = False) -> Dict[str, Any]:
    """
    Grade student answers, run Controller decision logic, and update state.
    
    :param student_answers: Dict mapping question ID (1..10) to raw input string
    :param quiz_dict: Quiz dict containing 'level' and 'questions' list
    :param is_practice: Whether this was a practice session quiz
    :return: Processed result dict
    """
    current_level = quiz_dict.get("level", 1)
    questions: List[Dict[str, Any]] = quiz_dict.get("questions", [])

    score = 0
    total = len(questions)
    question_results = []

    for q in questions:
        q_id = q.get("id")
        expected_ans = float(q.get("answer", 0.0))
        user_input = str(student_answers.get(q_id, "")).strip()

        is_correct, parsed_val = sanitize_and_evaluate_answer(user_input, expected_ans)
        if is_correct:
            score += 1

        question_results.append({
            "id": q_id,
            "question": q.get("question"),
            "expected": expected_ans,
            "user_input": user_input,
            "parsed_value": parsed_val,
            "is_correct": is_correct,
            "topic": q.get("topic")
        })

    # Run Controller decision logic (evaluates level-up, computes scoring, mutates state)
    controller_result = process_quiz_submission(
        score=score,
        total=total,
        current_level=current_level,
        is_practice=is_practice
    )

    controller_result["question_results"] = question_results
    return controller_result
