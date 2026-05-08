#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""
GENETIC ALGORITHM: A Literate Demonstration
=============================================

A genetic algorithm (GA) finds solutions through evolution rather than calculus.
Instead of following a gradient, it maintains a *population* of candidate solutions
and uses selection, crossover, and mutation to breed better ones over generations.

The Evolutionary Process:
1. Create a random population of candidate solutions
2. Evaluate fitness: how close is each candidate to the goal?
3. Selection: pick the fittest candidates as parents
4. Crossover: combine two parents to create offspring
5. Mutation: randomly tweak offspring to explore new possibilities
6. Repeat until a solution is found

This demo evolves a population of random strings toward a target phrase,
making the mechanics of evolution visible in real time.

How this relates to ML:
- Neural nets optimize via gradient descent (calculus: follow the slope)
- Genetic algorithms optimize via evolution (biology: survival of the fittest)
- Both are searching for good solutions in a vast space
- GAs don't need a differentiable loss function, just a fitness score

Author: Claude Code
"""

import random
import sys
import time
from typing import List, Tuple


class Individual:
    """
    A single candidate solution in the population.

    In this demo, each individual is a string of characters.
    Its "DNA" is the sequence of characters, and its fitness
    is how many characters match the target.
    """

    def __init__(self, genes: str):
        self.genes = genes
        self.fitness = 0.0

    def calculate_fitness(self, target: str):
        """Fraction of characters matching the target (0.0 = none, 1.0 = perfect)."""
        matches = sum(1 for a, b in zip(self.genes, target) if a == b)
        self.fitness = matches / len(target)

    def __repr__(self) -> str:
        return self.genes


class GeneticAlgorithm:
    """
    The evolutionary engine.

    Parameters:
    - population_size: how many candidates to maintain each generation
    - mutation_rate: probability of mutating each gene (character)
    - elite_count: top N individuals guaranteed to survive to next generation
    """

    CHARSET = (
        'abcdefghijklmnopqrstuvwxyz'
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        ' .,!?\'"-:;'
    )

    def __init__(self, target: str, population_size: int = 100,
                 mutation_rate: float = 0.02, elite_count: int = 2):
        self.target = target
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.elite_count = elite_count
        self.generation = 0
        self.population: List[Individual] = []
        self.history: List[float] = []

    def random_gene(self) -> str:
        return random.choice(self.CHARSET)

    def create_individual(self) -> Individual:
        genes = ''.join(self.random_gene() for _ in range(len(self.target)))
        return Individual(genes)

    def initialize_population(self):
        """Step 1: Create the initial random population."""
        self.population = [self.create_individual() for _ in range(self.population_size)]
        self.evaluate_all()

    def evaluate_all(self):
        """Step 2: Calculate fitness for every individual."""
        for individual in self.population:
            individual.calculate_fitness(self.target)
        self.population.sort(key=lambda ind: ind.fitness, reverse=True)

    def select_parent(self) -> Individual:
        """
        Step 3: Tournament selection.

        Pick a small random group and return the fittest.
        This balances exploitation (picking the best) with exploration
        (giving weaker individuals a chance).
        """
        tournament_size = 5
        tournament = random.sample(self.population, tournament_size)
        return max(tournament, key=lambda ind: ind.fitness)

    def crossover(self, parent_a: Individual, parent_b: Individual) -> Individual:
        """
        Step 4: Single-point crossover.

        Pick a random split point. The child gets genes from parent A
        before the split, and genes from parent B after it.

        Parent A: HELLO_WO | RLD
        Parent B: xyzzy_ab | cde
        Child:    HELLO_WO | cde

        This combines traits from both parents, analogous to
        biological reproduction.
        """
        split = random.randint(1, len(self.target) - 1)
        child_genes = parent_a.genes[:split] + parent_b.genes[split:]
        return Individual(child_genes)

    def mutate(self, individual: Individual) -> Individual:
        """
        Step 5: Random mutation.

        Each character has a small chance of being replaced with
        a random character. This introduces novelty that crossover
        alone cannot produce.

        Without mutation, the population can get stuck if no individual
        has the right character at a certain position.
        """
        genes = list(individual.genes)
        for i in range(len(genes)):
            if random.random() < self.mutation_rate:
                genes[i] = self.random_gene()
        return Individual(''.join(genes))

    def evolve_generation(self) -> Individual:
        """Run one complete cycle: select parents, breed offspring, replace population."""
        self.generation += 1
        new_population: List[Individual] = []

        # Elitism: the top N survive unchanged, so the best solution is never lost
        new_population.extend(self.population[:self.elite_count])

        # Fill remaining slots by breeding from the current population
        while len(new_population) < self.population_size:
            parent_a = self.select_parent()
            parent_b = self.select_parent()
            child = self.crossover(parent_a, parent_b)
            child = self.mutate(child)
            new_population.append(child)

        self.population = new_population
        self.evaluate_all()
        self.history.append(self.population[0].fitness)
        return self.population[0]


class GeneticAlgorithmDemo:
    """Interactive demonstration of genetic algorithm evolution."""

    DEFAULT_TARGETS = [
        "Hello World",
        "To be or not to be",
        "Evolution finds a way",
        "Survival of the fittest",
    ]

    def __init__(self):
        self.ga = None

    def print_header(self):
        print("\n" + "=" * 70)
        print("  GENETIC ALGORITHM DEMONSTRATION".center(70))
        print("=" * 70)
        print("\n📚 What is a Genetic Algorithm?")
        print("   A search method inspired by biological evolution.")
        print("   Instead of following gradients (like neural networks),")
        print("   it breeds a population of solutions using:")
        print("     1. Selection  - the fittest survive")
        print("     2. Crossover  - parents combine to make children")
        print("     3. Mutation   - random changes introduce novelty\n")
        print("🎯 This demo evolves random strings toward a target phrase.")
        print("   Watch how the population converges over generations.\n")

    def select_target(self) -> str:
        print("Target phrases:")
        for i, target in enumerate(self.DEFAULT_TARGETS, 1):
            print(f"  {i}. \"{target}\"")
        print(f"  {len(self.DEFAULT_TARGETS) + 1}. Enter your own")

        while True:
            try:
                choice = input(f"\nSelect (1-{len(self.DEFAULT_TARGETS) + 1}): ").strip()
                if choice.lower() == 'q':
                    sys.exit(0)
                idx = int(choice)
                if 1 <= idx <= len(self.DEFAULT_TARGETS):
                    return self.DEFAULT_TARGETS[idx - 1]
                elif idx == len(self.DEFAULT_TARGETS) + 1:
                    custom = input("Enter target phrase: ").strip()
                    if custom:
                        return custom
                    print("Please enter a non-empty string")
                else:
                    print(f"Enter a number between 1 and {len(self.DEFAULT_TARGETS) + 1}")
            except (ValueError, KeyboardInterrupt):
                print("\nExiting...")
                sys.exit(0)

    def configure(self) -> Tuple[int, float]:
        print("\n⚙️  Configuration")
        print("-" * 40)

        # Population size
        while True:
            try:
                val = input("  Population size (50-500, Enter for 150): ").strip()
                if val == "":
                    pop_size = 150
                    break
                pop_size = int(val)
                if 50 <= pop_size <= 500:
                    break
                print("  Enter a value between 50 and 500")
            except (ValueError, KeyboardInterrupt):
                print("\nExiting...")
                sys.exit(0)

        # Mutation rate
        while True:
            try:
                val = input("  Mutation rate (0.01-0.1, Enter for 0.02): ").strip()
                if val == "":
                    mut_rate = 0.02
                    break
                mut_rate = float(val)
                if 0.01 <= mut_rate <= 0.1:
                    break
                print("  Enter a value between 0.01 and 0.1")
            except (ValueError, KeyboardInterrupt):
                print("\nExiting...")
                sys.exit(0)

        return pop_size, mut_rate

    def format_individual(self, individual: Individual, target: str) -> str:
        """Color-code matching characters for visual feedback."""
        result = []
        for gene, goal in zip(individual.genes, target):
            if gene == goal:
                result.append(f"\033[32m{gene}\033[0m")  # Green for match
            else:
                result.append(f"\033[31m{gene}\033[0m")  # Red for mismatch
        return ''.join(result)

    def fitness_bar(self, fitness: float, width: int = 30) -> str:
        filled = int(fitness * width)
        return "█" * filled + "░" * (width - filled)

    def run_evolution(self, target: str, pop_size: int, mut_rate: float):
        self.ga = GeneticAlgorithm(
            target=target,
            population_size=pop_size,
            mutation_rate=mut_rate,
            elite_count=2,
        )

        print(f"\n  Target:          \"{target}\"")
        print(f"  Population:      {pop_size}")
        print(f"  Mutation rate:   {mut_rate}")
        print(f"  Selection:       Tournament (size 5)")
        print(f"  Crossover:       Single-point")
        print(f"  Elitism:         Top 2 survive unchanged")

        input("\n  Press Enter to start evolution...")
        print()

        self.ga.initialize_population()
        best = self.ga.population[0]

        print("  Gen  | Best Fitness           | Best Individual")
        print("  " + "-" * 64)

        max_generations = 5000
        start_time = time.time()

        while best.fitness < 1.0 and self.ga.generation < max_generations:
            best = self.ga.evolve_generation()

            # Display every generation for the first 20, then at intervals
            gen = self.ga.generation
            show = (gen <= 20 or gen % 10 == 0 or best.fitness == 1.0)

            if show:
                bar = self.fitness_bar(best.fitness)
                colored = self.format_individual(best, target)
                print(f"  {gen:4d} | {best.fitness:.3f} {bar} | {colored}")

        elapsed = time.time() - start_time

        # Results
        print("\n" + "=" * 70)
        if best.fitness == 1.0:
            print("  🎉 EVOLVED SUCCESSFULLY".center(70))
        else:
            print("  ⏱️  MAX GENERATIONS REACHED".center(70))
        print("=" * 70)

        print(f"\n📊 Results:")
        print(f"   Result:       \"{best.genes}\"")
        print(f"   Target:       \"{target}\"")
        print(f"   Generations:  {self.ga.generation}")
        print(f"   Time:         {elapsed:.2f}s")
        print(f"   Final fitness: {best.fitness:.4f}")

        # Show fitness progression
        self.show_fitness_graph()

    def show_fitness_graph(self):
        history = self.ga.history
        if not history:
            return

        print("\n  Fitness Over Generations")
        print("  " + "-" * 52)

        height = 10
        width = min(50, len(history))

        # Sample history to fit width
        if len(history) > width:
            step = len(history) / width
            sampled = [history[int(i * step)] for i in range(width)]
        else:
            sampled = history

        for row in range(height, 0, -1):
            threshold = row / height
            line = "  "
            if row == height:
                line += "1.0|"
            elif row == height // 2:
                line += "0.5|"
            else:
                line += "   |"
            for val in sampled:
                if val >= threshold:
                    line += "*"
                else:
                    line += " "
            print(line)

        print("   0.0+" + "-" * width)
        label_start = "Gen 1"
        label_end = f"Gen {len(history)}"
        padding = width - len(label_start) - len(label_end)
        print("       " + label_start + " " * max(padding, 1) + label_end)

    def explain(self):
        print("\n" + "=" * 70)
        print("  💡 HOW IT WORKED".center(70))
        print("=" * 70)

        print("""
  The GA found the target without any gradient or calculus:

  Selection:  Fitter strings (more matching characters) were more likely
              to be chosen as parents. This is "survival of the fittest."

  Crossover:  Two parent strings were split and recombined. If parent A
              has the right first half and parent B has the right second
              half, their child might get both right halves.

  Mutation:   Random character replacements introduced characters that
              no individual in the population had yet. Without mutation,
              the search can get permanently stuck.

  Elitism:    The top 2 individuals survived unchanged each generation,
              ensuring the best solution found so far is never lost.

  Compared to neural network training:
  - Neural nets: adjust weights by following the error gradient (calculus)
  - GA: adjust solutions by breeding the fittest candidates (evolution)
  - Both: iteratively improve toward a goal without being told the answer
  - GA advantage: works without a differentiable objective function
  - GA disadvantage: much less efficient for high-dimensional problems
""")

    def run(self):
        self.print_header()

        while True:
            target = self.select_target()
            pop_size, mut_rate = self.configure()
            self.run_evolution(target, pop_size, mut_rate)
            self.explain()

            print("\n" + "=" * 70)
            choice = input("\nRun again with different settings? (Y/n): ").strip().lower()
            if choice == 'n':
                print("\n🎓 Key takeaway: evolution is a general-purpose optimizer.")
                print("   It's slower than gradient descent for smooth problems,")
                print("   but works on anything you can score.\n")
                break


if __name__ == "__main__":
    demo = GeneticAlgorithmDemo()
    try:
        demo.run()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!")
        sys.exit(0)
