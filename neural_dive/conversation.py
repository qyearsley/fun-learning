"""
Conversation utilities for Neural Dive.
"""

import random
import copy
from typing import Optional
from neural_dive.models import Conversation, Question, Answer
from neural_dive.enums import NPCType
from neural_dive.config import (
    CORRECT_ANSWER_COHERENCE_GAIN,
    WRONG_ANSWER_COHERENCE_PENALTY,
)


def randomize_answers(question: Question, seed: Optional[int] = None) -> Question:
    """
    Create a copy of a question with randomized answer order.

    Args:
        question: The question to randomize
        seed: Optional random seed for reproducibility

    Returns:
        New Question object with shuffled answers
    """
    if seed is not None:
        random.seed(seed)

    # Deep copy the question
    new_question = copy.deepcopy(question)

    # Shuffle answers
    random.shuffle(new_question.answers)

    return new_question


def randomize_questions(
    questions: list[Question], seed: Optional[int] = None
) -> list[Question]:
    """
    Create a copy of questions list with randomized order.

    Args:
        questions: List of questions to randomize
        seed: Optional random seed for reproducibility

    Returns:
        New list with shuffled questions
    """
    if seed is not None:
        random.seed(seed)

    # Deep copy and shuffle
    new_questions = copy.deepcopy(questions)
    random.shuffle(new_questions)

    return new_questions


def create_randomized_conversation(
    conversation: Conversation,
    randomize_question_order: bool = True,
    randomize_answer_order: bool = True,
    seed: Optional[int] = None,
    num_questions: int = 3,
) -> Conversation:
    """
    Create a copy of a conversation with randomized questions and answers.

    Args:
        conversation: The conversation to randomize
        randomize_question_order: Whether to shuffle questions
        randomize_answer_order: Whether to shuffle answers within questions
        seed: Optional random seed for reproducibility
        num_questions: Number of questions to select from available pool (default: 3)

    Returns:
        New Conversation object with randomized content
    """
    if seed is not None:
        random.seed(seed)

    new_conv = copy.deepcopy(conversation)

    # Select a random subset of questions if we have more than num_questions
    if len(new_conv.questions) > num_questions:
        new_conv.questions = random.sample(new_conv.questions, num_questions)

    # Randomize question order if requested
    if randomize_question_order and len(new_conv.questions) > 1:
        random.shuffle(new_conv.questions)

    # Randomize answer order for each question if requested
    if randomize_answer_order:
        for i, question in enumerate(new_conv.questions):
            # Use different seed for each question
            q_seed = seed + i if seed is not None else None
            new_conv.questions[i] = randomize_answers(question, q_seed)

    return new_conv


def wrap_text(text: str, width: int) -> list[str]:
    """
    Wrap text to fit within width.

    Args:
        text: Text to wrap
        width: Maximum line width

    Returns:
        List of wrapped lines
    """
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        # Calculate what the line length would be if we add this word
        test_line = current_line + [word]
        # n words need n-1 spaces between them
        test_length = sum(len(w) for w in test_line) + len(test_line) - 1

        if test_length > width and current_line:
            # Line would be too long, save current line and start new one
            lines.append(" ".join(current_line))
            current_line = [word]
        else:
            # Word fits, add it
            current_line.append(word)

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def format_conversation_response(
    npc_name: str,
    response: str,
    is_correct: bool,
    coherence_change: int,
    reward_knowledge: Optional[str] = None,
    is_complete: bool = False,
    is_enemy: bool = False,
) -> str:
    """
    Format a response message with stats and completion info.

    Args:
        npc_name: Name of the NPC
        response: The response text
        is_correct: Whether the answer was correct
        coherence_change: Amount coherence changed (positive or negative)
        reward_knowledge: Knowledge module gained, if any
        is_complete: Whether this completes the conversation
        is_enemy: Whether this is an enemy NPC

    Returns:
        Formatted response string
    """
    result = response

    # Add stat changes
    if is_correct:
        result += f"\n\n[+{coherence_change} Coherence]"
        if reward_knowledge:
            result += f" [Gained: {reward_knowledge}]"
    else:
        if is_enemy:
            result += f"\n\n[CRITICAL ERROR! -{abs(coherence_change)} Coherence]"
        else:
            result += f"\n\n[-{abs(coherence_change)} Coherence]"

    # Add completion banner if conversation is complete
    if is_complete:
        separator = "═" * 40
        if is_enemy:
            completion_message = f"{npc_name}: You have passed my security check. You may proceed."
        else:
            completion_message = f"{npc_name}: You have proven your worth. I grant you passage."

        # Wrap the completion message to fit within a reasonable width
        wrapped_lines = wrap_text(completion_message, 70)
        wrapped_message = "\n".join(wrapped_lines)

        result += f"\n\n{separator}\n✓ CONVERSATION COMPLETE ✓\n{separator}\n\n{wrapped_message}"

    return result
