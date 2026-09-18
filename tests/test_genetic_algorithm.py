"""Tests for the pure logic in `genetic_algorithm_demo.py`.

Stdlib `unittest` and nothing else, deliberately. The demos are standalone PEP
723 scripts rather than a package, so there is no project to `uv sync` and no
test dependency to resolve -- `python3 -m unittest discover -s tests` from the
repo root is the whole story, on any interpreter meeting the `>=3.13` floor the
scripts declare. The genetic algorithm demo is the one with `dependencies = []`,
which is why it is the one tested here; the perceptron and neural-net demos need
numpy.

What is covered is the engine: fitness, selection, crossover, mutation, and the
one generation cycle that composes them. The orchestrator around it is
print-driven and interactive, and is not tested.

Randomness is seeded per test rather than stubbed, so these exercise the real
`random` calls. Where a property holds for every seed -- a child's length, a
gene being drawn from CHARSET -- it is asserted over many draws instead.
"""

import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from genetic_algorithm_demo import (  # noqa: E402
    TOURNAMENT_SIZE,
    GeneticAlgorithm,
    GeneticAlgorithmDemo,
    Individual,
)


class TestIndividualFitness(unittest.TestCase):
    def test_an_exact_match_scores_one(self):
        ind = Individual("Hello")
        ind.calculate_fitness("Hello")
        self.assertEqual(ind.fitness, 1.0)

    def test_no_matching_characters_scores_zero(self):
        ind = Individual("aaaaa")
        ind.calculate_fitness("bbbbb")
        self.assertEqual(ind.fitness, 0.0)

    def test_a_partial_match_scores_the_fraction(self):
        ind = Individual("Hexxo")
        ind.calculate_fitness("Hello")
        self.assertEqual(ind.fitness, 3 / 5)

    def test_position_matters_not_just_the_characters(self):
        ind = Individual("olleH")
        ind.calculate_fitness("Hello")
        # Only the middle 'l' lands in the right place.
        self.assertEqual(ind.fitness, 1 / 5)

    def test_a_length_mismatch_raises_rather_than_scoring_the_prefix(self):
        # The `strict=True` on the zip is load-bearing: without it "He" would
        # score a perfect 1.0 against "Hello".
        ind = Individual("He")
        with self.assertRaises(ValueError):
            ind.calculate_fitness("Hello")


class TestGeneSource(unittest.TestCase):
    def setUp(self):
        self.ga = GeneticAlgorithm("Hello World")

    def test_every_gene_comes_from_the_charset(self):
        random.seed(1)
        for _ in range(500):
            self.assertIn(self.ga.random_gene(), GeneticAlgorithm.CHARSET)

    def test_an_individual_is_created_at_the_target_length(self):
        random.seed(2)
        ind = self.ga.create_individual()
        self.assertEqual(len(ind.genes), len("Hello World"))
        self.assertTrue(set(ind.genes) <= set(GeneticAlgorithm.CHARSET))

    def test_the_charset_cannot_produce_a_character_outside_itself(self):
        random.seed(3)
        drawn = {self.ga.random_gene() for _ in range(2000)}
        self.assertTrue(drawn <= set(GeneticAlgorithm.CHARSET))


class TestPopulation(unittest.TestCase):
    def setUp(self):
        self.ga = GeneticAlgorithm("Hello World", population_size=20)
        random.seed(4)
        self.ga.initialize_population()

    def test_initialize_fills_the_population_to_size(self):
        self.assertEqual(len(self.ga.population), 20)

    def test_evaluate_all_sorts_fittest_first(self):
        scores = [ind.fitness for ind in self.ga.population]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_every_individual_is_scored(self):
        for ind in self.ga.population:
            self.assertGreaterEqual(ind.fitness, 0.0)
            self.assertLessEqual(ind.fitness, 1.0)

    def test_select_parent_returns_the_fittest_of_the_tournament(self):
        # A population exactly the size of a tournament means the tournament is
        # the whole population, so the winner is the single best individual.
        ga = GeneticAlgorithm("Hello World", population_size=TOURNAMENT_SIZE)
        ga.population = [Individual("a" * 11) for _ in range(TOURNAMENT_SIZE)]
        for i, ind in enumerate(ga.population):
            ind.fitness = i / 10
        best = ga.population[-1]
        random.seed(5)
        for _ in range(20):
            self.assertIs(ga.select_parent(), best)


class TestCrossover(unittest.TestCase):
    def setUp(self):
        self.ga = GeneticAlgorithm("HELLO_WORLD")
        self.a = Individual("AAAAAAAAAAA")
        self.b = Individual("bbbbbbbbbbb")

    def test_the_child_is_the_target_length(self):
        random.seed(6)
        for _ in range(100):
            child = self.ga.crossover(self.a, self.b)
            self.assertEqual(len(child.genes), len("HELLO_WORLD"))

    def test_the_child_is_a_prefix_of_a_and_a_suffix_of_b(self):
        random.seed(7)
        for _ in range(100):
            child = self.ga.crossover(self.a, self.b)
            split = child.genes.count("A")
            self.assertEqual(child.genes, "A" * split + "b" * (11 - split))

    def test_the_child_always_takes_something_from_each_parent(self):
        # `randint(1, len - 1)` excludes both ends, so a child is never a clone.
        random.seed(8)
        for _ in range(200):
            child = self.ga.crossover(self.a, self.b)
            self.assertIn("A", child.genes)
            self.assertIn("b", child.genes)


class TestMutation(unittest.TestCase):
    def test_a_zero_rate_leaves_the_genes_alone(self):
        ga = GeneticAlgorithm("Hello World", mutation_rate=0.0)
        original = Individual("Hello World")
        random.seed(9)
        for _ in range(50):
            self.assertEqual(ga.mutate(original).genes, "Hello World")

    def test_a_rate_of_one_redraws_every_position(self):
        ga = GeneticAlgorithm("Hello World", mutation_rate=1.0)
        original = Individual("\0" * 11)
        random.seed(10)
        mutated = ga.mutate(original)
        self.assertEqual(len(mutated.genes), 11)
        # NUL is not in CHARSET, so every position must have been replaced.
        self.assertNotIn("\0", mutated.genes)
        self.assertTrue(set(mutated.genes) <= set(GeneticAlgorithm.CHARSET))

    def test_mutation_preserves_length(self):
        ga = GeneticAlgorithm("Hello World", mutation_rate=0.5)
        random.seed(11)
        for _ in range(100):
            self.assertEqual(len(ga.mutate(Individual("Hello World")).genes), 11)

    def test_mutation_returns_a_new_individual(self):
        ga = GeneticAlgorithm("Hello World", mutation_rate=1.0)
        original = Individual("Hello World")
        random.seed(12)
        self.assertIsNot(ga.mutate(original), original)
        self.assertEqual(original.genes, "Hello World")


class TestEvolveGeneration(unittest.TestCase):
    def setUp(self):
        self.ga = GeneticAlgorithm("Hello World", population_size=30, mutation_rate=0.05)
        random.seed(13)
        self.ga.initialize_population()

    def test_the_population_size_is_held(self):
        for _ in range(5):
            self.ga.evolve_generation()
            self.assertEqual(len(self.ga.population), 30)

    def test_elitism_means_the_best_fitness_never_falls(self):
        best = self.ga.population[0].fitness
        for _ in range(25):
            self.ga.evolve_generation()
            self.assertGreaterEqual(self.ga.population[0].fitness, best)
            best = self.ga.population[0].fitness

    def test_the_generation_counter_and_history_advance_together(self):
        for expected in range(1, 6):
            self.ga.evolve_generation()
            self.assertEqual(self.ga.generation, expected)
            self.assertEqual(len(self.ga.history), expected)

    def test_evolution_makes_progress_on_a_short_target(self):
        ga = GeneticAlgorithm("Hello", population_size=60, mutation_rate=0.05)
        random.seed(14)
        ga.initialize_population()
        start = ga.population[0].fitness
        for _ in range(60):
            ga.evolve_generation()
        self.assertGreater(ga.population[0].fitness, start)


class TestTargetValidation(unittest.TestCase):
    def test_a_single_character_is_rejected(self):
        # `crossover` splits at randint(1, len - 1), an empty range for len 1.
        problem = GeneticAlgorithmDemo.target_problem("a")
        self.assertIsNotNone(problem)
        self.assertIn("two characters", problem)

    def test_an_empty_target_is_rejected(self):
        self.assertIsNotNone(GeneticAlgorithmDemo.target_problem(""))

    def test_a_character_outside_the_charset_is_rejected_and_named(self):
        problem = GeneticAlgorithmDemo.target_problem("café")
        self.assertIsNotNone(problem)
        self.assertIn("é", problem)

    def test_a_digit_is_outside_the_charset(self):
        # CHARSET is letters, space and punctuation -- no digits.
        problem = GeneticAlgorithmDemo.target_problem("Route 66")
        self.assertIsNotNone(problem)
        self.assertIn("6", problem)

    def test_every_built_in_target_is_usable(self):
        for target in GeneticAlgorithmDemo.DEFAULT_TARGETS:
            self.assertIsNone(GeneticAlgorithmDemo.target_problem(target), target)

    def test_a_plain_phrase_is_accepted(self):
        self.assertIsNone(GeneticAlgorithmDemo.target_problem("Hello World"))


class TestDisplayHelpers(unittest.TestCase):
    def setUp(self):
        self.demo = GeneticAlgorithmDemo()

    def test_the_fitness_bar_is_always_the_requested_width(self):
        for fitness in (0.0, 0.1, 0.5, 0.99, 1.0):
            self.assertEqual(len(self.demo.fitness_bar(fitness, width=30)), 30)

    def test_an_empty_bar_at_zero_and_a_full_one_at_one(self):
        self.assertEqual(self.demo.fitness_bar(0.0, width=10), "░" * 10)
        self.assertEqual(self.demo.fitness_bar(1.0, width=10), "█" * 10)

    def test_the_bar_fills_in_proportion(self):
        self.assertEqual(self.demo.fitness_bar(0.5, width=10), "█" * 5 + "░" * 5)

    def test_format_individual_rejects_a_length_mismatch(self):
        # Same `strict=True` reasoning as calculate_fitness: a silent truncation
        # would render a half-coloured phrase that looked like progress.
        with self.assertRaises(ValueError):
            self.demo.format_individual(Individual("He"), "Hello")

    def test_format_individual_marks_matches_and_mismatches_apart(self):
        out = self.demo.format_individual(Individual("Hexxo"), "Hello")
        self.assertIn("\033[32m", out)  # at least one match
        self.assertIn("\033[31m", out)  # at least one mismatch
        # Every character survives, colour codes aside.
        self.assertEqual(
            out.replace("\033[32m", "").replace("\033[31m", "").replace("\033[0m", ""), "Hexxo"
        )


if __name__ == "__main__":
    unittest.main()
