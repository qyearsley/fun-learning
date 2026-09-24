"""Tests for the pure logic in `neural_net_demo.py`.

Needs numpy; see `test_perceptron.py` beside this file for why this directory
is a separate suite and how to run it.

What is covered is the network: the sigmoid and its derivative, the forward
pass, and -- the part most worth checking -- that `backward` really follows the
gradient. That is tested against a finite-difference estimate rather than
against hand-derived numbers, so a sign error or a transposed matrix in the
backprop fails here even though the network would still train, slowly and
wrongly. The visualiser and the interactive demo are not tested, apart from
`progress_bar`.
"""

import copy
import sys
import unittest
import warnings
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from neural_net_demo import (  # noqa: E402
    DECISION_THRESHOLD,
    NeuralNetwork,
    progress_bar,
    sigmoid,
    sigmoid_derivative,
)

XOR = [([0, 0], 0), ([0, 1], 1), ([1, 0], 1), ([1, 1], 0)]
PARAMETERS = ("weights_input_hidden", "weights_hidden_output", "bias_hidden", "bias_output")


def loss(nn, inputs, target):
    """Half squared error: the loss whose gradient `backward` descends."""
    return 0.5 * (target - nn.forward(inputs)) ** 2


class TestSigmoid(unittest.TestCase):
    def test_zero_maps_to_one_half(self):
        self.assertEqual(sigmoid(np.array(0.0)), 0.5)

    def test_it_is_symmetric_about_one_half(self):
        x = np.linspace(-6, 6, 25)
        np.testing.assert_allclose(sigmoid(x) + sigmoid(-x), 1.0)

    def test_it_stays_strictly_inside_zero_and_one_for_moderate_inputs(self):
        y = sigmoid(np.linspace(-30, 30, 61))
        self.assertTrue(np.all((y > 0) & (y < 1)))

    def test_huge_inputs_do_not_overflow(self):
        # SIGMOID_CLIP exists for this. Without it np.exp(1000) warns and the
        # demo prints a RuntimeWarning into the middle of the training output.
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            y = sigmoid(np.array([-1e4, 1e4]))
        np.testing.assert_allclose(y, [0.0, 1.0], atol=1e-12)

    def test_the_derivative_peaks_at_one_quarter(self):
        self.assertEqual(sigmoid_derivative(np.array(0.0)), 0.25)
        x = np.linspace(-6, 6, 25)
        self.assertTrue(np.all(sigmoid_derivative(x) <= 0.25))

    def test_the_derivative_matches_a_finite_difference(self):
        x = np.linspace(-4, 4, 17)
        h = 1e-6
        numeric = (sigmoid(x + h) - sigmoid(x - h)) / (2 * h)
        np.testing.assert_allclose(sigmoid_derivative(x), numeric, rtol=1e-6)


class TestForward(unittest.TestCase):
    def setUp(self):
        np.random.seed(0)
        self.nn = NeuralNetwork()

    def test_the_output_is_a_probability(self):
        for inputs, _ in XOR:
            out = self.nn.forward(np.array(inputs))
            self.assertGreater(out, 0.0)
            self.assertLess(out, 1.0)

    def test_it_records_the_activations_for_the_visualiser(self):
        self.nn.forward(np.array([1, 0]))
        self.assertEqual(self.nn.hidden_values.shape, (3,))
        self.assertEqual(self.nn.output_value.shape, (1,))
        np.testing.assert_allclose(self.nn.hidden_values, sigmoid(self.nn.hidden_weighted_sum))

    def test_it_does_not_change_the_weights(self):
        before = copy.deepcopy(self.nn)
        self.nn.forward(np.array([1, 1]))
        for name in PARAMETERS:
            np.testing.assert_array_equal(getattr(self.nn, name), getattr(before, name))

    def test_predict_thresholds_the_output(self):
        for inputs, _ in XOR:
            x = np.array(inputs)
            expected = 1 if self.nn.forward(x) >= DECISION_THRESHOLD else 0
            self.assertEqual(self.nn.predict(x), expected)


class TestBackward(unittest.TestCase):
    def test_every_update_is_minus_lr_times_the_numerical_gradient(self):
        h = 1e-6
        lr = 0.5
        for seed in range(5):
            for inputs, target in XOR:
                np.random.seed(seed)
                nn = NeuralNetwork(learning_rate=lr)
                x = np.array(inputs, dtype=float)

                # Estimate dL/dp for every parameter by nudging it both ways.
                numeric = {}
                for name in PARAMETERS:
                    p = getattr(nn, name)
                    grad = np.zeros_like(p)
                    for idx in np.ndindex(p.shape):
                        original = p[idx]
                        p[idx] = original + h
                        up = loss(nn, x, target)
                        p[idx] = original - h
                        down = loss(nn, x, target)
                        p[idx] = original
                        grad[idx] = (up - down) / (2 * h)
                    numeric[name] = grad

                before = copy.deepcopy(nn)
                nn.forward(x)
                nn.backward(x, target)
                for name in PARAMETERS:
                    step = getattr(nn, name) - getattr(before, name)
                    np.testing.assert_allclose(
                        step,
                        -lr * numeric[name],
                        rtol=1e-4,
                        atol=1e-9,
                        err_msg=f"{name}, seed {seed}, input {inputs}",
                    )

    def test_it_returns_the_absolute_error_before_the_update(self):
        np.random.seed(1)
        nn = NeuralNetwork()
        x = np.array([1, 0])
        out = nn.forward(x)
        self.assertAlmostEqual(nn.backward(x, 1), abs(1 - out))

    def test_a_small_step_reduces_the_error_on_that_example(self):
        for seed in range(10):
            np.random.seed(seed)
            nn = NeuralNetwork(learning_rate=0.05)
            x = np.array([0, 1])
            before = loss(nn, x, 1)
            nn.train_step(x, 1)
            self.assertLess(loss(nn, x, 1), before, f"seed {seed}")


class TestTraining(unittest.TestCase):
    def test_it_learns_xor(self):
        # One seed, as a smoke test that the pieces compose. Not every seed
        # converges in the demo's 5000 epochs -- a 2-3-1 sigmoid net can stall
        # in a local minimum -- so this is not asserted for all of them.
        np.random.seed(0)
        nn = NeuralNetwork(learning_rate=0.5)
        for _ in range(5000):
            for inputs, target in XOR:
                nn.train_step(np.array(inputs), target)
        for inputs, target in XOR:
            self.assertEqual(nn.predict(np.array(inputs)), target, inputs)


class TestProgressBar(unittest.TestCase):
    def test_it_is_always_the_requested_width(self):
        for fraction in (0.0, 0.33, 0.5, 1.0):
            self.assertEqual(len(progress_bar(fraction, 20)), 20)

    def test_it_fills_in_proportion(self):
        self.assertEqual(progress_bar(0.5, 10), "█" * 5 + "░" * 5)

    def test_out_of_range_fractions_are_clamped(self):
        self.assertEqual(progress_bar(-1.0, 4), "░░░░")
        self.assertEqual(progress_bar(2.0, 4), "████")


if __name__ == "__main__":
    unittest.main()
