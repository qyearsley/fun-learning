"""Tests for the pure logic in `perceptron_demo.py`.

This directory needs numpy, so it is a separate suite from `tests/` and has no
`__init__.py` -- a bare `python3 -m unittest discover -s tests` does not recurse
into it, and the stdlib suite keeps needing nothing installed. Run it with uv,
which resolves numpy the same way the demo does when you run it:

    uv run --no-project --python 3.13 --with 'numpy>=2.0,<3' \\
        python -m unittest discover -s tests/numpy

What is covered is the neuron: the step activation, the weighted sum, the
learning rule, and whether it converges on the gates it should and fails on the
one it cannot. The demo around it is print-driven and is not tested, apart from
the static `decision_bar`.
"""

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from perceptron_demo import Perceptron, PerceptronDemo  # noqa: E402


def fixed(weights, bias, learning_rate=0.1):
    """A perceptron with known weights, so a test does not depend on a seed."""
    p = Perceptron(n_inputs=len(weights), learning_rate=learning_rate)
    p.weights = np.array(weights, dtype=float)
    p.bias = float(bias)
    return p


def train(p, gate, epochs):
    """Run the demo's training loop without the printing. True if it converged."""
    for _ in range(epochs):
        errors = 0
        for inputs, target in PerceptronDemo.GATES[gate]:
            _, error, _ = p.train_step(np.array(inputs), target)
            errors += error
        if errors == 0:
            return True
    return False


class TestActivation(unittest.TestCase):
    def setUp(self):
        self.p = fixed([0.0, 0.0], 0.0)

    def test_zero_fires(self):
        # `>=` rather than `>`: a sum exactly on the boundary is a 1.
        self.assertEqual(self.p.activation(0.0), 1)

    def test_just_below_zero_does_not_fire(self):
        self.assertEqual(self.p.activation(-1e-9), 0)

    def test_the_magnitude_does_not_matter(self):
        self.assertEqual(self.p.activation(1e9), 1)
        self.assertEqual(self.p.activation(-1e9), 0)


class TestWeightedSum(unittest.TestCase):
    def test_it_is_w_dot_x_plus_b(self):
        p = fixed([2.0, -3.0], 0.5)
        self.assertAlmostEqual(p.weighted_sum(np.array([1, 1])), 2.0 - 3.0 + 0.5)
        self.assertAlmostEqual(p.weighted_sum(np.array([0, 0])), 0.5)

    def test_it_returns_a_plain_float(self):
        # The demo formats it with `:+6.3f`; a 0-d array would format too, but
        # the annotation promises a float.
        self.assertIs(type(fixed([1.0, 1.0], 0.0).weighted_sum(np.array([1, 0]))), float)

    def test_predict_agrees_with_the_sign_of_the_sum(self):
        p = fixed([1.0, 1.0], -1.5)  # an AND gate
        for inputs, target in PerceptronDemo.GATES["AND"]:
            x = np.array(inputs)
            self.assertEqual(p.predict(x), p.activation(p.weighted_sum(x)))
            self.assertEqual(p.predict(x), target)


class TestLearningRule(unittest.TestCase):
    def test_a_correct_prediction_changes_nothing(self):
        p = fixed([1.0, 1.0], -1.5)
        prediction, error, _ = p.train_step(np.array([1, 1]), 1)
        self.assertEqual((prediction, error), (1, 0))
        np.testing.assert_array_equal(p.weights, [1.0, 1.0])
        self.assertEqual(p.bias, -1.5)

    def test_a_missed_one_moves_weights_toward_the_input(self):
        # Predicted 0, wanted 1: error is +1, so each weight gains lr * input.
        p = fixed([0.0, 0.0], -1.0, learning_rate=0.25)
        prediction, error, ws = p.train_step(np.array([1, 0]), 1)
        self.assertEqual((prediction, error, ws), (0, 1, -1.0))
        np.testing.assert_allclose(p.weights, [0.25, 0.0])
        self.assertAlmostEqual(p.bias, -0.75)

    def test_a_false_one_moves_weights_away_from_the_input(self):
        p = fixed([0.5, 0.5], 0.0, learning_rate=0.25)
        prediction, error, _ = p.train_step(np.array([0, 1]), 0)
        self.assertEqual((prediction, error), (1, 1))
        np.testing.assert_allclose(p.weights, [0.5, 0.25])
        self.assertAlmostEqual(p.bias, -0.25)

    def test_the_reported_error_is_a_magnitude(self):
        # `train_step` returns abs(error) so the demo can sum it as a count.
        p = fixed([0.5, 0.5], 0.0)
        _, error, _ = p.train_step(np.array([1, 1]), 0)
        self.assertEqual(error, 1)


class TestConvergence(unittest.TestCase):
    # The perceptron convergence theorem promises these four finish. The bound
    # depends on the margin, so the epoch budget is generous, and checked over
    # many seeds rather than trusting one.
    SEPARABLE = ("AND", "OR", "NAND", "NOR")

    def test_every_linearly_separable_gate_is_learned(self):
        for gate in self.SEPARABLE:
            for seed in range(50):
                np.random.seed(seed)
                p = Perceptron(n_inputs=2, learning_rate=0.1)
                self.assertTrue(train(p, gate, epochs=200), f"{gate}, seed {seed}")

    def test_a_learned_gate_predicts_its_whole_truth_table(self):
        np.random.seed(0)
        p = Perceptron(n_inputs=2)
        train(p, "NAND", epochs=200)
        for inputs, target in PerceptronDemo.GATES["NAND"]:
            self.assertEqual(p.predict(np.array(inputs)), target)

    def test_xor_is_never_learned(self):
        # No straight line splits XOR, so no weights can get all four right.
        # This is the limitation the demo exists to show.
        for seed in range(20):
            np.random.seed(seed)
            p = Perceptron(n_inputs=2)
            self.assertFalse(train(p, "XOR", epochs=200), f"seed {seed}")


class TestDecisionBar(unittest.TestCase):
    bar = staticmethod(PerceptronDemo.decision_bar)

    def test_it_is_always_the_requested_width(self):
        for ws in (-100.0, -3.0, -0.4, 0.0, 0.4, 3.0, 100.0):
            self.assertEqual(len(self.bar(ws, width=21)), 21)
            self.assertEqual(len(self.bar(ws, width=11)), 11)

    def test_zero_puts_the_marker_on_the_boundary(self):
        # The marker overwrites the boundary glyph, so there is no "│" left.
        self.assertEqual(self.bar(0.0, width=5), "──●──")

    def test_positive_sums_sit_right_of_centre_and_negative_left(self):
        self.assertEqual(self.bar(1.5, width=11), "─────│─●───")
        self.assertEqual(self.bar(-1.5, width=11), "───●─│─────")

    def test_the_marker_clamps_at_the_ends(self):
        self.assertEqual(self.bar(3.0, width=5), "──│─●")
        self.assertEqual(self.bar(1e6, width=5), "──│─●")
        self.assertEqual(self.bar(-1e6, width=5), "●─│──")


if __name__ == "__main__":
    unittest.main()
