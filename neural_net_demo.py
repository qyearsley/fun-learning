#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "numpy",
# ]
# ///
"""
NEURAL NETWORK: A Literate Demonstration
=========================================

A neural network is a collection of interconnected artificial neurons organized in layers.
Unlike a single perceptron, a neural network with hidden layers can learn complex patterns
that aren't linearly separable - like XOR!

Network Architecture:
- Input Layer: 2 neurons (x1, x2)
- Hidden Layer: 3 neurons (with sigmoid activation)
- Output Layer: 1 neuron (with sigmoid activation)

The Learning Process:
1. Forward Propagation: Data flows from inputs through hidden layer to output
2. Calculate Error: Compare prediction with correct answer
3. Backward Propagation: Calculate how much each weight contributed to error
4. Update Weights: Adjust all weights to reduce error
5. Repeat until the network learns the pattern
"""

import sys
import time

import numpy as np

# Network and training defaults
DEFAULT_LEARNING_RATE = 0.5
DEFAULT_MAX_EPOCHS = 5000
VERBOSE_INTERVAL = 500
SIGMOID_CLIP = 500
DECISION_THRESHOLD = 0.5
CONVERGENCE_THRESHOLD = 0.01
ACCEPTABLE_ERROR = 0.1


def get_validated_input(prompt: str, default, min_val, max_val, cast=float):
    """Prompt until the user enters a value in [min_val, max_val], or accepts the default."""
    while True:
        try:
            val = input(prompt).strip()
            if val == "":
                return default
            val = cast(val)
            if min_val <= val <= max_val:
                return val
            print(f"  Please enter a value between {min_val} and {max_val}")
        except ValueError:
            print("  Please enter a valid number")
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)


def sigmoid(x: np.ndarray) -> np.ndarray:
    """
    Sigmoid activation function: outputs smooth values between 0 and 1.

    Formula: σ(x) = 1 / (1 + e^(-x))

    This is better than the step function because:
    - It's differentiable (needed for backpropagation)
    - Outputs smooth probabilities instead of hard 0/1
    """
    return 1 / (1 + np.exp(-np.clip(x, -SIGMOID_CLIP, SIGMOID_CLIP)))


def sigmoid_derivative(x: np.ndarray) -> np.ndarray:
    """
    Derivative of sigmoid: σ'(x) = σ(x) * (1 - σ(x))

    This tells us how much to adjust weights during backpropagation.
    """
    sx = sigmoid(x)
    return sx * (1 - sx)


class NeuralNetwork:
    """
    A simple feedforward neural network with one hidden layer.

    Architecture: 2 -> 3 -> 1
    - 2 input neurons
    - 3 hidden neurons
    - 1 output neuron
    """

    def __init__(self, learning_rate: float = 0.5):
        """
        Initialize the neural network with random weights.

        Weight matrices:
        - weights_input_hidden: [2 x 3] connects inputs to hidden layer
        - weights_hidden_output: [3 x 1] connects hidden to output
        - bias_hidden: [3] biases for hidden neurons
        - bias_output: [1] bias for output neuron
        """
        self.learning_rate = learning_rate

        # Initialize weights with small random values
        self.weights_input_hidden = np.random.randn(2, 3) * 0.5
        self.weights_hidden_output = np.random.randn(3, 1) * 0.5
        self.bias_hidden = np.random.randn(3) * 0.5
        self.bias_output = np.random.randn(1) * 0.5

        # Store activations for visualization
        self.input_values = None
        self.hidden_values = None
        self.output_value = None
        self.hidden_weighted_sum = None
        self.output_weighted_sum = None

    def forward(self, inputs: np.ndarray) -> float:
        """
        Forward propagation: calculate network output for given inputs.

        Steps:
        1. Calculate weighted sum for hidden layer
        2. Apply sigmoid activation to get hidden layer values
        3. Calculate weighted sum for output layer
        4. Apply sigmoid activation to get final output
        """
        self.input_values = inputs

        # Hidden layer
        self.hidden_weighted_sum = np.dot(inputs, self.weights_input_hidden) + self.bias_hidden
        self.hidden_values = sigmoid(self.hidden_weighted_sum)

        # Output layer
        self.output_weighted_sum = (
            np.dot(self.hidden_values, self.weights_hidden_output) + self.bias_output
        )
        self.output_value = sigmoid(self.output_weighted_sum)

        return self.output_value[0]

    def backward(self, inputs: np.ndarray, target: float):
        """
        Backward propagation: calculate gradients and update weights.

        The Chain Rule:
        - Start from the output error
        - Work backwards through the network
        - Calculate how much each weight contributed to the error
        - Update weights to reduce error
        """
        # Output layer error - convert to scalar for cleaner math
        output_error = target - self.output_value[0]
        output_delta = output_error * sigmoid_derivative(self.output_weighted_sum)[0]

        # Hidden layer error (backpropagate the error)
        # Each hidden neuron's error is proportional to its weight to the output
        hidden_error = self.weights_hidden_output.flatten() * output_delta
        hidden_delta = hidden_error * sigmoid_derivative(self.hidden_weighted_sum)

        # Update weights and biases
        # Output layer weights: (3, 1) += (3,) * scalar reshaped
        self.weights_hidden_output += (
            self.learning_rate * self.hidden_values.reshape(-1, 1) * output_delta
        )
        self.bias_output[0] += self.learning_rate * output_delta

        # Hidden layer weights: (2, 3) += outer((2,), (3,))
        self.weights_input_hidden += self.learning_rate * np.outer(inputs, hidden_delta)
        self.bias_hidden += self.learning_rate * hidden_delta

        return abs(output_error)

    def train_step(self, inputs: np.ndarray, target: float) -> tuple[float, float]:
        """
        Perform one complete training step: forward pass + backward pass.

        Returns:
            (prediction, error)
        """
        prediction = self.forward(inputs)
        error = self.backward(inputs, target)
        return prediction, error

    def predict(self, inputs: np.ndarray) -> int:
        """Make a binary prediction (0 or 1) for given inputs."""
        output = self.forward(inputs)
        return 1 if output >= DECISION_THRESHOLD else 0


class NetworkVisualizer:
    """Handles ASCII visualization of the neural network."""

    @staticmethod
    def draw_network(nn: NeuralNetwork, show_weights: bool = False):
        """
        Draw the network with labelled boxes and a "bus" between layers
        showing full connectivity (every input connects to every hidden,
        every hidden connects to the output).

        The double-line bus (║═╠╣╔╗╚╝╬) carries the matrix-multiply: each
        layer's output is multiplied by a weight matrix to produce the next
        layer's input.
        """
        print("\n" + "=" * 70)
        print("  NETWORK STATE".center(70))
        print("=" * 70)

        # Pre-training (forward() not yet called), activations are None — show 0.0
        def val(arr, i):
            return arr[i] if arr is not None else 0.0

        i1, i2 = val(nn.input_values, 0), val(nn.input_values, 1)
        h1, h2, h3 = val(nn.hidden_values, 0), val(nn.hidden_values, 1), val(nn.hidden_values, 2)
        o1 = val(nn.output_value, 0)

        print()
        print("    Input              Hidden               Output")
        print()
        print("    ┌─ I1 ─┐")
        print(f"    │ {i1:4.2f} │═══╗     ╔══┌─ H1 ─┐══╗")
        print(f"    └──────┘   ║     ║  │ {h1:4.2f} │  ║")
        print("               ║     ║  └──────┘  ║")
        print("               ╠═════╣  ┌─ H2 ─┐  ║   ┌─ O1 ─┐")
        print(f"               ║     ╠══│ {h2:4.2f} │══╬══→│ {o1:4.2f} │")
        print("               ║     ║  └──────┘  ║   └──────┘")
        print("    ┌─ I2 ─┐   ║     ║  ┌─ H3 ─┐  ║")
        print(f"    │ {i2:4.2f} │═══╝     ╚══│ {h3:4.2f} │══╝")
        print("    └──────┘            └──────┘")
        print()
        print("                ↑              ↑")
        print("            2×3 weights    3×1 weights")

        if show_weights:
            print("\n" + "-" * 70)
            print("  WEIGHT MATRICES".center(70))
            print("-" * 70 + "\n")

            print("  Input → Hidden:")
            print("           H1      H2      H3")
            print(
                f"    I1  [{nn.weights_input_hidden[0][0]:6.3f} {nn.weights_input_hidden[0][1]:6.3f} {nn.weights_input_hidden[0][2]:6.3f}]"
            )
            print(
                f"    I2  [{nn.weights_input_hidden[1][0]:6.3f} {nn.weights_input_hidden[1][1]:6.3f} {nn.weights_input_hidden[1][2]:6.3f}]"
            )
            print(
                f"  Bias  [{nn.bias_hidden[0]:6.3f} {nn.bias_hidden[1]:6.3f} {nn.bias_hidden[2]:6.3f}]"
            )

            print("\n  Hidden → Output:")
            print(f"    H1  [{nn.weights_hidden_output[0][0]:6.3f}]")
            print(f"    H2  [{nn.weights_hidden_output[1][0]:6.3f}]")
            print(f"    H3  [{nn.weights_hidden_output[2][0]:6.3f}]")
            print(f"  Bias  [{nn.bias_output[0]:6.3f}]")

        print("=" * 70)

    @staticmethod
    def draw_training_step(inputs: list[int], target: int, prediction: float, error: float):
        """Draw a single training step with visual feedback."""
        pred_binary = 1 if prediction >= DECISION_THRESHOLD else 0
        status = "✓" if abs(target - prediction) < DECISION_THRESHOLD else "✗"

        # Create a visual bar for the prediction confidence
        bar_length = 20
        filled = int(prediction * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)

        print(
            f"  {status} Input: [{inputs[0]}, {inputs[1]}] → Target: {target} | "
            f"Prediction: {prediction:.3f} [{bar}] {pred_binary} | Error: {error:.3f}"
        )


class NeuralNetDemo:
    """
    Interactive demonstration of a 2-3-1 neural network learning XOR.
    Run via NeuralNetDemo().run() or execute this file directly.
    """

    # XOR truth table - the classic problem that perceptrons can't solve!
    XOR_DATA = [
        ([0, 0], 0),
        ([0, 1], 1),
        ([1, 0], 1),
        ([1, 1], 0),
    ]

    def __init__(self):
        self.network = None
        self.visualizer = NetworkVisualizer()

    def print_header(self):
        """Display the program header."""
        print("\n" + "=" * 70)
        print("  NEURAL NETWORK LEARNING DEMONSTRATION".center(70))
        print("=" * 70)
        print("\n📚 What is a Neural Network?")
        print("   A neural network is multiple artificial neurons working together in layers.")
        print("   Unlike a single perceptron, networks with 'hidden layers' can learn")
        print("   complex patterns by combining simple features in sophisticated ways.\n")
        print("🎯 The Challenge: XOR (Exclusive OR)")
        print("   XOR outputs 1 when inputs are DIFFERENT, 0 when they're the SAME.")
        print("   This is NOT linearly separable - you can't draw a single straight line")
        print("   to separate the cases! A perceptron fails at this, but a neural network")
        print("   with a hidden layer can learn it.\n")

    def print_xor_table(self):
        """Display the XOR truth table."""
        print("\n🎯 XOR Truth Table")
        print("-" * 40)
        print("  Input 1 | Input 2 | Output")
        print("  --------|---------|--------")
        for inputs, output in self.XOR_DATA:
            print(f"    {inputs[0]}     |    {inputs[1]}    |   {output}")
        print()

    def explain_architecture(self):
        """Explain the network architecture."""
        print("\n🏗️  Network Architecture")
        print("-" * 40)
        print("  • Input Layer: 2 neurons (x1, x2)")
        print("  • Hidden Layer: 3 neurons with sigmoid activation")
        print("  • Output Layer: 1 neuron with sigmoid activation")
        print("  • Total weights: 2×3 + 3×1 = 9 weights + 4 biases = 13 parameters\n")
        print("💡 Why hidden layers?")
        print("   The hidden layer learns to create NEW features from the inputs.")
        print("   These features can represent complex patterns like 'inputs are different'")
        print("   which is what XOR needs!\n")

    def train_with_visualization(self, max_epochs: int = 5000, verbose_interval: int = 500):
        """
        Train the neural network with visualization.

        Args:
            max_epochs: Maximum number of training epochs
            verbose_interval: How often to show detailed visualization
        """
        print("\nStarting training...")
        print(f"   Learning rate: {self.network.learning_rate}")
        print(f"   Max epochs: {max_epochs}")
        print(f"   Convergence threshold: Average error < {CONVERGENCE_THRESHOLD}\n")

        # Show initial network state
        print("📊 Initial Network State:")
        self.visualizer.draw_network(self.network, show_weights=True)

        input("\nPress Enter to start training...")
        print()

        try:
            for epoch in range(max_epochs):
                total_error = 0

                # Decide if this is a verbose epoch
                is_verbose = (epoch % verbose_interval == 0) or (epoch < 5)

                if is_verbose:
                    print(f"\n{'=' * 70}")
                    print(f"  EPOCH {epoch + 1}/{max_epochs}".center(70))
                    print(f"{'=' * 70}\n")

                # Train on each example
                for inputs, target in self.XOR_DATA:
                    inputs_array = np.array(inputs)
                    prediction, error = self.network.train_step(inputs_array, target)
                    total_error += error

                    if is_verbose:
                        self.visualizer.draw_training_step(inputs, target, prediction, error)

                avg_error = total_error / len(self.XOR_DATA)

                if is_verbose:
                    print(f"\n  Average Error: {avg_error:.4f}")
                    time.sleep(0.5)
                elif epoch % 100 == 0:
                    # Show progress for non-verbose epochs
                    bar_length = 30
                    progress = epoch / max_epochs
                    filled = int(progress * bar_length)
                    bar = "█" * filled + "░" * (bar_length - filled)
                    print(
                        f"\r  Progress: [{bar}] Epoch {epoch}/{max_epochs} | Avg Error: {avg_error:.4f}",
                        end="",
                        flush=True,
                    )

                # Check for convergence
                if avg_error < CONVERGENCE_THRESHOLD:
                    print(f"\n\nConverged after {epoch + 1} epochs!")
                    print(f"   Final average error: {avg_error:.6f}")
                    return True
        except KeyboardInterrupt:
            print("\n\nTraining interrupted.")
            return False

        print("\n\nTraining complete (max epochs reached)")
        print(f"   Final average error: {avg_error:.6f}")
        return avg_error < ACCEPTABLE_ERROR

    def test_network(self):
        """Test the trained network on all XOR examples."""
        print("\n" + "=" * 70)
        print("  FINAL TEST".center(70))
        print("=" * 70 + "\n")

        print("Testing learned behavior:")
        print("  Input 1 | Input 2 | Expected | Predicted | Confidence | Result")
        print("  --------|---------|----------|-----------|------------|--------")

        correct = 0
        for inputs, target in self.XOR_DATA:
            output = self.network.forward(np.array(inputs))
            prediction = 1 if output >= DECISION_THRESHOLD else 0
            is_correct = prediction == target
            correct += is_correct
            result = "✓" if is_correct else "✗"

            # Confidence bar
            confidence = output if prediction == 1 else (1 - output)
            bar_length = 10
            filled = int(confidence * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)

            print(
                f"    {inputs[0]}     |    {inputs[1]}    |    {target}     |     {prediction}     | "
                f"[{bar}] {confidence:.2f} |   {result}"
            )

        accuracy = (correct / len(self.XOR_DATA)) * 100
        print(f"\n📊 Accuracy: {accuracy:.0f}% ({correct}/{len(self.XOR_DATA)} correct)")

        # Show final network with all values
        self.visualizer.draw_network(self.network, show_weights=True)

    def explain_learning(self):
        """Explain what the network learned."""
        print("\n" + "=" * 70)
        print("  UNDERSTANDING WHAT THE NETWORK LEARNED".center(70))
        print("=" * 70 + "\n")

        print("💡 How did it learn XOR?\n")
        print("   The hidden layer learned to detect useful patterns:")
        print("   • Some neurons might activate when EITHER input is 1")
        print("   • Other neurons might activate when BOTH inputs are 1")
        print("   • The output neuron combines these to detect 'different inputs'\n")

        print("   Let's see what each hidden neuron learned:")
        print("   (Testing each combination and observing hidden layer activations)\n")

        for inputs, target in self.XOR_DATA:
            self.network.forward(np.array(inputs))
            print(f"   Input: [{inputs[0]}, {inputs[1]}] → Output: {target}")
            print(
                f"     Hidden neurons: [H1={self.network.hidden_values[0]:.3f}, "
                f"H2={self.network.hidden_values[1]:.3f}, "
                f"H3={self.network.hidden_values[2]:.3f}]"
            )
            print(
                f"     Final output: {self.network.output_value[0]:.3f} → {self.network.predict(np.array(inputs))}\n"
            )

        print("   The hidden layer transforms the problem into a space where")
        print("   XOR becomes linearly separable! This is the power of neural networks.")

    def run(self):
        """Main program loop."""
        self.print_header()
        self.print_xor_table()
        self.explain_architecture()

        # Ask for learning rate
        print("⚙️  Configuration")
        print("-" * 40)
        learning_rate = get_validated_input(
            f"Enter learning rate (0.1-2.0, or press Enter for {DEFAULT_LEARNING_RATE}): ",
            DEFAULT_LEARNING_RATE,
            0.1,
            2.0,
        )

        # Initialize network
        self.network = NeuralNetwork(learning_rate=learning_rate)

        # Train
        self.train_with_visualization(
            max_epochs=DEFAULT_MAX_EPOCHS, verbose_interval=VERBOSE_INTERVAL
        )

        # Test
        self.test_network()

        # Explain
        self.explain_learning()

        # Conclusion
        print("\n" + "=" * 70)
        print("  CONCLUSION".center(70))
        print("=" * 70 + "\n")
        print("🎓 Key Lessons:")
        print("   • Single perceptrons can only learn linearly separable patterns")
        print("   • Neural networks with hidden layers can learn complex patterns like XOR")
        print("   • Hidden layers create new feature representations")
        print("   • Backpropagation efficiently trains all weights simultaneously")
        print("   • Modern networks scale this up to millions of parameters and many layers,")
        print("     but the fundamentals are the same.\n")


if __name__ == "__main__":
    demo = NeuralNetDemo()
    try:
        demo.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted.")
        sys.exit(0)
