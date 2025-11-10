"""
Data loading utilities for Neural Dive.
Loads questions, NPCs, and terminals from JSON files.
"""

import json
import os
from pathlib import Path
from typing import Dict
from neural_dive.models import Question, Answer, Conversation
from neural_dive.enums import NPCType


def get_data_dir() -> Path:
    """Get the data directory path"""
    return Path(__file__).parent / "data"


def load_questions() -> Dict[str, Question]:
    """Load all questions from questions.json"""
    data_file = get_data_dir() / "questions.json"

    with open(data_file, "r") as f:
        data = json.load(f)

    questions = {}
    for question_id, q_data in data.items():
        # Parse answers
        answers = []
        for ans_data in q_data["answers"]:
            answer = Answer(
                text=ans_data["text"],
                correct=ans_data["correct"],
                response=ans_data["response"],
                reward_knowledge=ans_data.get("reward_knowledge"),
                enemy_penalty=ans_data.get("enemy_penalty", 35),  # default from config
            )
            answers.append(answer)

        # Create question
        question = Question(
            question_text=q_data["question_text"],
            answers=answers,
            topic=q_data["topic"],
        )
        questions[question_id] = question

    return questions


def load_npcs(questions: Dict[str, Question]) -> Dict[str, dict]:
    """
    Load all NPCs from npcs.json

    Args:
        questions: Dictionary of Question objects keyed by question_id

    Returns:
        Dictionary of NPC data with Conversation objects
    """
    data_file = get_data_dir() / "npcs.json"

    with open(data_file, "r") as f:
        data = json.load(f)

    npcs = {}
    for npc_name, npc_data in data.items():
        # Parse NPC type
        npc_type = NPCType(npc_data["npc_type"])

        # Get questions for this NPC
        npc_questions = []
        for question_id in npc_data.get("questions", []):
            if question_id in questions:
                npc_questions.append(questions[question_id])

        # Create conversation
        conversation = Conversation(
            npc_name=npc_name,
            greeting=npc_data["greeting"],
            questions=npc_questions,
            npc_type=npc_type,
        )

        # Store NPC data
        npcs[npc_name] = {
            "char": npc_data["char"],
            "color": npc_data["color"],
            "floor": npc_data["floor"],
            "conversation": conversation,
        }

    return npcs


def load_terminals() -> Dict[str, dict]:
    """Load all terminals from terminals.json"""
    data_file = get_data_dir() / "terminals.json"

    with open(data_file, "r") as f:
        data = json.load(f)

    return data


def load_all_game_data():
    """
    Load all game data (questions, NPCs, terminals)

    Returns:
        Tuple of (questions, npcs, terminals)
    """
    questions = load_questions()
    npcs = load_npcs(questions)
    terminals = load_terminals()

    return questions, npcs, terminals
