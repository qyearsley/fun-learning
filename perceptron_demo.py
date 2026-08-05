#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "numpy",
# ]
# ///
"""
PERCEPTRON: A Literate Demonstration
=====================================

A perceptron is the simplest form of a neural network - a single artificial neuron
that can learn to classify inputs into two categories. This program demonstrates
how a perceptron learns through examples.

The Learning Process:
1. Start with random weights and bias
2. Make a prediction for an input
3. Compare prediction with correct answer
4. Adjust weights based on the error
5. Repeat until it learns the pattern
"""

import numpy as np
import sys
import time
from typing import Tuple

# Training defaults
DEFAULT_LEARNING_RATE = 0.1
DEFAULT_MAX_EPOCHS = 25
TRAINING_DELAY = 0.2


class Perceptron:
    """
    A single artificial neuron that learns to classify binary inputs.

    Mathematical Model:
    -------------------
    output = activation(w1*x1 + w2*x2 + ... + wn*xn + bias)

    Where:
    - w = weights (importance of each input)
    - x = inputs
    - bias = threshold adjustment
    - activation = step function (0 or 1)
    """

    def __init__(self, n_inputs: int, learning_rate: float = 0.1):
        """
        Initialize the perceptron with random weights.

        Args:
            n_inputs: Number of input features
            learning_rate: How much to adjust weights each step (typically 0.01 - 0.5)
        """
        self.weights = np.random.randn(n_inputs) * 0.5
        self.bias = np.random.randn() * 0.5
        self.learning_rate = learning_rate
        self.n_inputs = n_inputs

    def activation(self, x: float) -> int:
        """
        Step activation function: outputs 1 if x >= 0, else 0.
        This makes the perceptron a binary classifier.
        """
        return 1 if x >= 0 else 0

    def predict(self, inputs: np.ndarray) -> int:
        """Compute weighted sum of inputs and apply step activation."""
        weighted_sum = np.dot(inputs, self.weights) + self.bias
        return self.activation(weighted_sum)

    def weighted_sum(self, inputs: np.ndarray) -> float:
        """Pre-activation value: w·x + b. Sign of this determines the prediction."""
        return float(np.dot(inputs, self.weights) + self.bias)

    def train_step(self, inputs: np.ndarray, target: int) -> Tuple[int, float, float]:
        """
        Perform one training step (one example).

        The Learning Rule:
        -----------------
        error = target - prediction
        weight_change = learning_rate × error × input

        Intuition: If we predicted wrong, adjust weights in the direction
        that would have given the correct answer.

        Returns:
            (prediction, error, weighted_sum)
        """
        weighted_sum = self.weighted_sum(inputs)
        prediction = self.activation(weighted_sum)
        error = target - prediction

        # Update weights: move them in the direction that reduces error
        self.weights += self.learning_rate * error * inputs
        self.bias += self.learning_rate * error

        return prediction, abs(error), weighted_sum

    def get_state(self) -> str:
        weights_str = ", ".join([f"w{i}={w:.3f}" for i, w in enumerate(self.weights)])
        return f"[{weights_str}, bias={self.bias:.3f}]"


class PerceptronDemo:
    """
    Interactive demonstration of perceptron learning on logic gates.
    Run via PerceptronDemo().run() or execute this file directly.
    """

    # Logic gate truth tables: (input1, input2) -> output
    GATES = {
        'AND': [
            ([0, 0], 0),
            ([0, 1], 0),
            ([1, 0], 0),
            ([1, 1], 1),
        ],
        'OR': [
            ([0, 0], 0),
            ([0, 1], 1),
            ([1, 0], 1),
            ([1, 1], 1),
        ],
        'NAND': [
            ([0, 0], 1),
            ([0, 1], 1),
            ([1, 0], 1),
            ([1, 1], 0),
        ],
        'NOR': [
            ([0, 0], 1),
            ([0, 1], 0),
            ([1, 0], 0),
            ([1, 1], 0),
        ],
        'XOR': [  # XOR is NOT linearly separable - perceptron will fail!
            ([0, 0], 0),
            ([0, 1], 1),
            ([1, 0], 1),
            ([1, 1], 0),
        ],
    }

    def __init__(self):
        self.perceptron = None
        self.gate_name = None

    def print_header(self):
        print("\n" + "="*70)
        print("  PERCEPTRON LEARNING DEMONSTRATION".center(70))
        print("="*70)
        print("\n📚 What is a Perceptron?")
        print("   A perceptron is an artificial neuron that learns to classify")
        print("   inputs by adjusting 'weights' - numbers that determine how")
        print("   important each input is for making a decision.\n")

    def print_gate_info(self, gate_name: str):
        print(f"\n🎯 Learning Target: {gate_name} Gate")
        print("-" * 40)
        print(f"Truth Table for {gate_name}:")
        print("  Input 1 | Input 2 | Output")
        print("  --------|---------|--------")
        for inputs, output in self.GATES[gate_name]:
            print(f"    {inputs[0]}     |    {inputs[1]}    |   {output}")
        print()

        if gate_name == 'XOR':
            print("⚠️  WARNING: XOR is NOT linearly separable!")
            print("   A single perceptron CANNOT learn XOR perfectly.")
            print("   This demonstrates the perceptron's limitation.")
            print("   (Neural networks with hidden layers can learn XOR)\n")

    def select_gate(self) -> str:
        print("Available Logic Gates:")
        gates = list(self.GATES.keys())
        default_idx = 1  # AND
        for i, gate in enumerate(gates, 1):
            marker = "⚠️ " if gate == "XOR" else "✓ "
            tag = " (default)" if i == default_idx else ""
            print(f"  {i}. {marker}{gate}{tag}")

        while True:
            try:
                choice = input(f"\nSelect a gate (1-{len(gates)}, Enter for {default_idx}, 'q' to quit): ").strip()
                if choice == "":
                    return gates[default_idx - 1]
                if choice.lower() == 'q':
                    sys.exit(0)
                idx = int(choice) - 1
                if 0 <= idx < len(gates):
                    return gates[idx]
                print(f"Please enter a number between 1 and {len(gates)}")
            except (ValueError, KeyboardInterrupt):
                print("\nExiting...")
                sys.exit(0)

    @staticmethod
    def decision_bar(weighted_sum: float, width: int = 21) -> str:
        """
        Visualize the weighted sum on a centered axis. The midpoint is the
        decision boundary (sum = 0): a marker to the right means the
        perceptron predicts 1, to the left means 0. Distance from center
        is the magnitude (informal "confidence").
        """
        # Map weighted_sum onto [-1, 1] via tanh-like clamp, then to [0, width-1]
        clamped = max(-3.0, min(3.0, weighted_sum)) / 3.0
        center = width // 2
        position = center + int(round(clamped * center))
        position = max(0, min(width - 1, position))
        cells = ["─"] * width
        cells[center] = "│"  # decision boundary
        cells[position] = "●"
        return "".join(cells)

    def train_with_visualization(self, max_epochs: int = 20, delay: float = 0.3):
        """
        Train the perceptron with real-time visualization.

        An 'epoch' is one complete pass through all training examples.
        """
        training_data = self.GATES[self.gate_name]

        print("\nStarting training...")
        print(f"   Initial state: {self.perceptron.get_state()}\n")

        try:
            for epoch in range(max_epochs):
                print(f"\n{'=' * 70}")
                print(f"  EPOCH {epoch + 1}/{max_epochs}".center(70))
                print(f"{'=' * 70}\n")

                total_error = 0

                # Train on each example
                for inputs, target in training_data:
                    inputs_array = np.array(inputs)
                    prediction, error, ws = self.perceptron.train_step(inputs_array, target)
                    total_error += error

                    status = "✓" if error == 0 else "✗"
                    bar = self.decision_bar(ws)
                    print(f"  {status} Input: [{inputs[0]}, {inputs[1]}] → Target: {target} | "
                          f"Sum: {ws:+6.3f} [{bar}] {prediction} | Error: {int(error)}")

                    time.sleep(delay * 0.5)

                # Show updated weights after each epoch
                print(f"\n  Updated: {self.perceptron.get_state()}")
                print(f"  Total errors this epoch: {int(total_error)}")

                # If perfect accuracy, we're done!
                if total_error == 0:
                    print("\n  Converged — the perceptron has learned the pattern.")
                    return True

                time.sleep(delay)
        except KeyboardInterrupt:
            print("\n\nTraining interrupted.")
            return False

        print("\nTraining complete (max epochs reached)")
        return False

    def test_perceptron(self):
        """Test the trained perceptron on all examples."""
        print("\n" + "="*70)
        print("  FINAL TEST".center(70))
        print("="*70 + "\n")

        training_data = self.GATES[self.gate_name]
        correct = 0

        print("Testing learned behavior:")
        print("  Input 1 | Input 2 | Expected | Predicted | Decision (sum) | Result")
        print("  --------|---------|----------|-----------|----------------|--------")

        for inputs, target in training_data:
            arr = np.array(inputs)
            ws = self.perceptron.weighted_sum(arr)
            prediction = self.perceptron.activation(ws)
            is_correct = prediction == target
            correct += is_correct
            result = "✓" if is_correct else "✗"
            bar = self.decision_bar(ws, width=11)
            print(f"    {inputs[0]}     |    {inputs[1]}    |    {target}     |     {prediction}     | "
                  f"[{bar}] {ws:+5.2f} |   {result}")

        accuracy = (correct / len(training_data)) * 100
        print(f"\n📊 Accuracy: {accuracy:.0f}% ({correct}/{len(training_data)} correct)")
        print(f"   Final weights: {self.perceptron.get_state()}")

    def explain_weights(self):
        """Explain what the learned weights mean."""
        print("\n" + "="*70)
        print("  UNDERSTANDING THE LEARNED WEIGHTS".center(70))
        print("="*70 + "\n")

        print("💡 What do these numbers mean?\n")
        print(f"   w0 = {self.perceptron.weights[0]:.3f}  (importance of first input)")
        print(f"   w1 = {self.perceptron.weights[1]:.3f}  (importance of second input)")
        print(f"   bias = {self.perceptron.bias:.3f}  (threshold adjustment)\n")

        print("   The perceptron makes decisions using:")
        print("   output = activate(w0×input0 + w1×input1 + bias)")
        print(f"   output = activate({self.perceptron.weights[0]:.2f}×input0 + "
              f"{self.perceptron.weights[1]:.2f}×input1 + {self.perceptron.bias:.2f})\n")

        print("   If the result is ≥ 0 → output 1")
        print("   If the result is < 0 → output 0")

    def run(self):
        """Main program loop."""
        self.print_header()

        # Select gate
        self.gate_name = self.select_gate()
        self.print_gate_info(self.gate_name)

        # Initialize perceptron
        learning_rate = DEFAULT_LEARNING_RATE
        self.perceptron = Perceptron(n_inputs=2, learning_rate=learning_rate)

        print("⚙️  Perceptron Configuration:")
        print("   • Inputs: 2")
        print(f"   • Learning rate: {learning_rate}")
        print("   • Activation: Step function (binary output)")

        # Train
        input("\nPress Enter to start training...")
        self.train_with_visualization(max_epochs=DEFAULT_MAX_EPOCHS, delay=TRAINING_DELAY)

        # Test
        self.test_perceptron()

        # Explain
        self.explain_weights()


if __name__ == "__main__":
    demo = PerceptronDemo()
    try:
        demo.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted.")
        sys.exit(0)
