"""
Data models for Neural Dive game.
"""

from dataclasses import dataclass, field
from typing import Optional
from neural_dive.enums import NPCType
from neural_dive.config import ENEMY_WRONG_ANSWER_PENALTY


@dataclass
class Answer:
    """A possible answer to a conversation question"""

    text: str
    correct: bool
    response: str  # NPC's response to this answer
    reward_knowledge: Optional[str] = None  # Knowledge module gained if correct
    enemy_penalty: int = ENEMY_WRONG_ANSWER_PENALTY  # Extra penalty for enemies


@dataclass
class Question:
    """A CS question in a conversation"""

    question_text: str
    answers: list[Answer]
    topic: str  # e.g., "algorithms", "data_structures", "systems"


@dataclass
class Conversation:
    """A conversation with an NPC"""

    npc_name: str
    greeting: str
    questions: list[Question]
    npc_type: NPCType = NPCType.SPECIALIST
    current_question_idx: int = 0
    completed: bool = False

    def get_current_question(self) -> Optional[Question]:
        """Get the current question, or None if conversation is complete"""
        if self.current_question_idx < len(self.questions):
            return self.questions[self.current_question_idx]
        return None

    def advance_question(self):
        """Move to the next question"""
        self.current_question_idx += 1
        if self.current_question_idx >= len(self.questions):
            self.completed = True

    def is_complete(self) -> bool:
        """Check if all questions have been answered"""
        return self.current_question_idx >= len(self.questions)
