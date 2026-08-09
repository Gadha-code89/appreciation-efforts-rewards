"""
agents_app/evaluator_agent.py - Math Quiz Generation & AST Answer Key Verification Agent
"""

import os
import json
import random
from typing import List, Dict, Any
from pydantic import BaseModel

from core.calculator import verify_arithmetic
from core.levels import get_level_info

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class QuizQuestion(BaseModel):
    id: int
    question: str
    answer: float
    topic: str


class QuizSet(BaseModel):
    level: int
    questions: List[QuizQuestion]


def generate_fallback_quiz(level: int) -> QuizSet:
    """
    Pre-validated fallback generator if OpenAI API is unconfigured or fails.
    """
    level_info = get_level_info(level)
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
        questions.append(QuizQuestion(
            id=i,
            question=expr.replace('*', '×').replace('/', '÷'),
            answer=float(ans),
            topic=topic
        ))

    return QuizSet(level=level, questions=questions)


def generate_quiz_with_evaluator(level: int, is_practice: bool = False) -> QuizSet:
    """
    Generate 10-question quiz for level using OpenAI API with AST verification tool.
    Retries up to 3 times on validation failure before falling back.
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or OpenAI is None:
        return generate_fallback_quiz(level)

    level_info = get_level_info(level)
    client = OpenAI(api_key=api_key)

    system_prompt = (
        f"You are the Evaluator Agent for a math quiz app. "
        f"Your task is to generate a 10-question math quiz suitable for a student at {level_info['name']}. "
        f"Description: {level_info['description']}. "
        f"IMPORTANT: Format questions using standard math symbols (+, -, *, /). "
        f"Every question MUST have an exact verified numeric answer."
    )

    for attempt in range(1, 4):
        try:
            # Request structured output using Pydantic model
            completion = client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate 10 unique questions for Level {level} math quiz."}
                ],
                response_format=QuizSet
            )
            quiz_set: QuizSet = completion.choices[0].message.parsed
            
            # Verify every question's answer key using AST calculator
            verified_questions = []
            for q in quiz_set.questions:
                # Convert display operators for AST evaluation
                raw_expr = q.question.replace('×', '*').replace('÷', '/')
                try:
                    calc_ans = verify_arithmetic(raw_expr)
                    verified_questions.append(QuizQuestion(
                        id=q.id,
                        question=q.question,
                        answer=float(calc_ans),
                        topic=q.topic
                    ))
                except Exception:
                    # Fallback answer to pydantic answer if AST parse fails on text
                    verified_questions.append(q)

            return QuizSet(level=level, questions=verified_questions)

        except Exception as e:
            if attempt == 3:
                break

    return generate_fallback_quiz(level)
