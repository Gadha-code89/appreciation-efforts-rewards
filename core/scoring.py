"""
core/scoring.py - Scoring, Quiz Generation, and Grading Logic
"""

import os
import json
import random
from typing import Dict, Any, List

from core.calculator import verify_arithmetic, sanitize_and_evaluate_answer
from core.levels import get_level_info

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


def compute_minutes(num_correct: int, num_questions: int, session_number: int, is_practice: bool = False, level: int = 1) -> Dict[str, Any]:
    """
    Compute earned minutes for a completed quiz session.
    Kept for legacy compatibility and testing.
    """
    if num_questions <= 0:
        return {"minutes": 0, "session_number": session_number, "accuracy": 0.0, "rate": 0.0}

    accuracy = num_correct / num_questions
    perfect = (num_correct == num_questions)

    if not perfect:
        return {
            "minutes": 0,
            "session_number": session_number,
            "accuracy": round(accuracy, 2),
            "rate": 0.0,
            "reason": f"Scored {num_correct}/{num_questions}. A strict 10/10 (100%) is required to earn minutes."
        }

    # Perfect score: level 1 = 5, level 2 = 10, level 3 = 15
    minutes = 5 * level
    rate = minutes / num_questions

    return {
        "minutes": minutes,
        "session_number": session_number,
        "accuracy": 1.0,
        "rate": round(rate, 2),
        "reason": f"Perfect score ({num_correct}/{num_questions})! Earned {minutes} minutes."
    }


def generate_new_quiz(level: int) -> Dict[str, Any]:
    """
    Generate 10 unique math questions for the specified level.
    Uses AI if configured, otherwise falls back to deterministic generator.
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key and OpenAI is not None:
        try:
            client = OpenAI(api_key=api_key)
            level_info = get_level_info(level)
            system_prompt = (
                f"You are a math tutor app. "
                f"Generate a 10-question math quiz suitable for {level_info['name']}. "
                f"Description: {level_info['description']}. "
                f"Format questions using standard math symbols (+, -, *, /). "
                f"Every question MUST have an exact verified numeric answer. "
                f"Respond ONLY in JSON format: "
                f'{{"level": {level}, "questions": [{{"id": 1, "question": "5 + 3", "answer": 8.0, "topic": "Addition"}}]}}'
            )
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate the 10 questions."}
                ],
                response_format={"type": "json_object"}
            )
            quiz_data = json.loads(completion.choices[0].message.content)
            
            # Verify and sanitize answers
            verified_questions = []
            for q in quiz_data.get("questions", []):
                raw_expr = q["question"].replace('×', '*').replace('÷', '/')
                try:
                    calc_ans = verify_arithmetic(raw_expr)
                    verified_questions.append({
                        "id": q["id"],
                        "question": q["question"],
                        "answer": float(calc_ans),
                        "topic": q.get("topic", "Arithmetic")
                    })
                except Exception:
                    verified_questions.append({
                        "id": q["id"],
                        "question": q["question"],
                        "answer": float(q["answer"]),
                        "topic": q.get("topic", "Arithmetic")
                    })
            return {"level": level, "questions": verified_questions}
        except Exception:
            pass

    # Fallback generator
    questions = []
    for i in range(1, 11):
        if level == 1:
            a, b = random.randint(5, 25), random.randint(1, 20)
            op = random.choice(['+', '-'])
            if op == '-' and a < b:
                a, b = b, a
            expr = f"{a} {op} {b}"
            topic = "Addition & Subtraction"
        elif level == 2:
            a, b = random.randint(15, 50), random.randint(10, 45)
            op = random.choice(['+', '-'])
            if op == '-' and a < b:
                a, b = b, a
            expr = f"{a} {op} {b}"
            topic = "Carrying & Borrowing"
        elif level == 3:
            a, b = random.randint(2, 12), random.randint(2, 12)
            expr = f"{a} * {b}"
            topic = "Multiplication Tables"
        elif level == 4:
            b = random.randint(2, 10)
            a = b * random.randint(2, 10)
            expr = f"{a} / {b}"
            topic = "Division & Mixed Math"
        else:
            a, b, c = random.randint(2, 10), random.randint(2, 10), random.randint(5, 20)
            expr = f"({a} * {b}) + {c}"
            topic = "Multi-step Arithmetic"

        ans = verify_arithmetic(expr)
        questions.append({
            "id": i,
            "question": expr.replace('*', '×').replace('/', '÷'),
            "answer": float(ans),
            "topic": topic
        })

    return {"level": level, "questions": questions}


def grade_quiz(student_answers: Dict[int, str], quiz_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Grades user answers against the generated math quiz questions.
    """
    questions = quiz_dict.get("questions", [])
    score = 0
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

    return {
        "score": score,
        "total": len(questions),
        "question_results": question_results
    }
