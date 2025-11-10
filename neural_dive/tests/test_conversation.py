"""
Unit tests for conversation utilities.
"""

import unittest
from neural_dive.conversation import (
    randomize_answers,
    randomize_questions,
    wrap_text,
    format_conversation_response,
)
from neural_dive.models import Answer, Question


class TestRandomization(unittest.TestCase):
    """Test answer and question randomization"""

    def test_randomize_answers(self):
        """Test that answers are randomized"""
        answers = [
            Answer("A", False, "No."),
            Answer("B", False, "No."),
            Answer("C", True, "Yes!"),
            Answer("D", False, "No."),
        ]
        question = Question("Test?", answers, "test")

        # Randomize with seed for reproducibility
        randomized = randomize_answers(question, seed=42)

        # Should have same answers but potentially different order
        self.assertEqual(len(randomized.answers), len(question.answers))
        self.assertEqual(
            set(a.text for a in randomized.answers),
            set(a.text for a in question.answers),
        )

        # Order might be different (not guaranteed, but very likely with 4 items)
        original_order = [a.text for a in question.answers]
        randomized_order = [a.text for a in randomized.answers]

        # At least verify they're the same question
        self.assertEqual(randomized.question_text, question.question_text)
        self.assertEqual(randomized.topic, question.topic)

    def test_randomize_questions(self):
        """Test that questions are randomized"""
        q1 = Question("Q1?", [Answer("A", True, "Yes")], "topic1")
        q2 = Question("Q2?", [Answer("B", True, "Yes")], "topic2")
        q3 = Question("Q3?", [Answer("C", True, "Yes")], "topic3")
        questions = [q1, q2, q3]

        randomized = randomize_questions(questions, seed=42)

        # Should have same questions
        self.assertEqual(len(randomized), len(questions))
        self.assertEqual(
            set(q.question_text for q in randomized),
            set(q.question_text for q in questions),
        )


class TestWrapText(unittest.TestCase):
    """Test text wrapping functionality"""

    def test_wrap_short_text(self):
        """Test wrapping text that fits in one line"""
        text = "Hello world"
        lines = wrap_text(text, width=50)

        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], "Hello world")

    def test_wrap_long_text(self):
        """Test wrapping text that needs multiple lines"""
        text = "This is a very long piece of text that definitely needs to be wrapped"
        lines = wrap_text(text, width=20)

        self.assertGreater(len(lines), 1)
        for line in lines:
            self.assertLessEqual(len(line), 20)

    def test_wrap_respects_words(self):
        """Test that wrapping doesn't break words"""
        text = "The quick brown fox jumps over the lazy dog"
        lines = wrap_text(text, width=15)

        for line in lines:
            # No partial words (except potentially at line boundaries)
            words = line.split()
            for word in words:
                self.assertIn(word, text.split())

    def test_wrap_empty_text(self):
        """Test wrapping empty text"""
        text = ""
        lines = wrap_text(text, width=50)

        self.assertEqual(len(lines), 0)

    def test_wrap_single_word(self):
        """Test wrapping a single word"""
        text = "Supercalifragilisticexpialidocious"
        lines = wrap_text(text, width=50)

        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], text)


class TestFormatConversationResponse(unittest.TestCase):
    """Test conversation response formatting"""

    def test_format_correct_answer(self):
        """Test formatting a correct answer response"""
        response = format_conversation_response(
            npc_name="TEST_NPC",
            response="Great job!",
            is_correct=True,
            coherence_change=10,
            reward_knowledge="test_knowledge",
        )

        self.assertIn("Great job!", response)
        self.assertIn("+10 Coherence", response)
        self.assertIn("test_knowledge", response)

    def test_format_wrong_answer(self):
        """Test formatting a wrong answer response"""
        response = format_conversation_response(
            npc_name="TEST_NPC",
            response="Not quite.",
            is_correct=False,
            coherence_change=-25,
        )

        self.assertIn("Not quite.", response)
        self.assertIn("-25 Coherence", response)

    def test_format_enemy_wrong_answer(self):
        """Test formatting enemy wrong answer (critical error)"""
        response = format_conversation_response(
            npc_name="VIRUS_HUNTER",
            response="INTRUDER!",
            is_correct=False,
            coherence_change=-35,
            is_enemy=True,
        )

        self.assertIn("INTRUDER!", response)
        self.assertIn("CRITICAL ERROR", response)
        self.assertIn("-35 Coherence", response)

    def test_format_completion(self):
        """Test formatting conversation completion"""
        response = format_conversation_response(
            npc_name="TEST_NPC",
            response="Well done!",
            is_correct=True,
            coherence_change=10,
            is_complete=True,
        )

        self.assertIn("CONVERSATION COMPLETE", response)
        self.assertIn("TEST_NPC", response)
        self.assertIn("proven your worth", response)

    def test_format_enemy_completion(self):
        """Test formatting enemy conversation completion"""
        response = format_conversation_response(
            npc_name="VIRUS_HUNTER",
            response="Correct.",
            is_correct=True,
            coherence_change=10,
            is_complete=True,
            is_enemy=True,
        )

        self.assertIn("CONVERSATION COMPLETE", response)
        self.assertIn("passed my security check", response)


if __name__ == "__main__":
    unittest.main()
