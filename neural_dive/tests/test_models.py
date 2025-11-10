"""
Unit tests for data models.
"""

import unittest
from neural_dive.models import Answer, Question, Conversation
from neural_dive.enums import NPCType


class TestAnswer(unittest.TestCase):
    """Test the Answer model"""

    def test_answer_creation(self):
        """Test creating an answer"""
        answer = Answer(
            text="O(log n)",
            correct=True,
            response="Correct!",
            reward_knowledge="binary_search",
        )

        self.assertEqual(answer.text, "O(log n)")
        self.assertTrue(answer.correct)
        self.assertEqual(answer.response, "Correct!")
        self.assertEqual(answer.reward_knowledge, "binary_search")
        self.assertEqual(answer.enemy_penalty, 35)  # Default from config

    def test_answer_without_reward(self):
        """Test creating an answer without knowledge reward"""
        answer = Answer(text="O(n)", correct=False, response="Not quite.")

        self.assertIsNone(answer.reward_knowledge)


class TestQuestion(unittest.TestCase):
    """Test the Question model"""

    def test_question_creation(self):
        """Test creating a question with answers"""
        answers = [
            Answer("O(n)", False, "Too slow."),
            Answer("O(log n)", True, "Correct!", "binary_search"),
        ]

        question = Question(
            question_text="What is the time complexity?",
            answers=answers,
            topic="algorithms",
        )

        self.assertEqual(question.question_text, "What is the time complexity?")
        self.assertEqual(len(question.answers), 2)
        self.assertEqual(question.topic, "algorithms")

    def test_question_has_correct_answer(self):
        """Test that questions have correct answers marked"""
        answers = [
            Answer("Wrong", False, "No."),
            Answer("Right", True, "Yes!"),
        ]

        question = Question("Test?", answers, "test")
        correct_answers = [a for a in question.answers if a.correct]

        self.assertEqual(len(correct_answers), 1)
        self.assertEqual(correct_answers[0].text, "Right")


class TestConversation(unittest.TestCase):
    """Test the Conversation model"""

    def setUp(self):
        """Set up test conversation"""
        self.answers1 = [
            Answer("A", False, "No."),
            Answer("B", True, "Yes!", "knowledge1"),
        ]
        self.answers2 = [
            Answer("C", True, "Correct!", "knowledge2"),
            Answer("D", False, "Wrong."),
        ]
        self.question1 = Question("Q1?", self.answers1, "topic1")
        self.question2 = Question("Q2?", self.answers2, "topic2")

        self.conversation = Conversation(
            npc_name="TEST_NPC",
            greeting="Hello!",
            questions=[self.question1, self.question2],
            npc_type=NPCType.SPECIALIST,
        )

    def test_conversation_creation(self):
        """Test creating a conversation"""
        self.assertEqual(self.conversation.npc_name, "TEST_NPC")
        self.assertEqual(self.conversation.greeting, "Hello!")
        self.assertEqual(len(self.conversation.questions), 2)
        self.assertEqual(self.conversation.npc_type, NPCType.SPECIALIST)
        self.assertEqual(self.conversation.current_question_idx, 0)
        self.assertFalse(self.conversation.completed)

    def test_get_current_question(self):
        """Test getting the current question"""
        current = self.conversation.get_current_question()

        self.assertIsNotNone(current)
        self.assertEqual(current.question_text, "Q1?")

    def test_advance_question(self):
        """Test advancing to next question"""
        self.conversation.advance_question()

        self.assertEqual(self.conversation.current_question_idx, 1)
        current = self.conversation.get_current_question()
        self.assertEqual(current.question_text, "Q2?")

    def test_advance_to_completion(self):
        """Test advancing until conversation is complete"""
        self.assertFalse(self.conversation.is_complete())

        self.conversation.advance_question()
        self.assertFalse(self.conversation.is_complete())

        self.conversation.advance_question()
        self.assertTrue(self.conversation.is_complete())
        self.assertTrue(self.conversation.completed)

    def test_get_current_question_when_complete(self):
        """Test that get_current_question returns None when complete"""
        self.conversation.current_question_idx = 2
        current = self.conversation.get_current_question()

        self.assertIsNone(current)


if __name__ == "__main__":
    unittest.main()
