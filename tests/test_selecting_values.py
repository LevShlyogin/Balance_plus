import unittest

from utils.base_for_selection import ProblemDefinition
from utils.selection_methods import AnalyticalSolver, BisectionSolver, NewtonSolver


class TestSolvers(unittest.TestCase):

    def setUp(self):
        """Выполняется перед каждым тестом. Создает общие объекты."""
        self.problem = ProblemDefinition()
        self.target_delta = 0.001
        # Эталонное значение, посчитанное заранее самым точным методом
        self.expected_x = 2.0694058273

    def test_analytical_solver(self):
        """Тест: Аналитический решатель находит точное значение."""
        solver = AnalyticalSolver(self.problem)
        result = solver.solve(self.target_delta)
        self.assertAlmostEqual(result, self.expected_x, places=7)

    def test_newton_solver_convergence(self):
        """Тест: Метод Ньютона сходится к правильному значению."""
        solver = NewtonSolver(self.problem, tol=1e-9)
        result = solver.solve(self.target_delta, initial_guess=2.0)
        self.assertAlmostEqual(result, self.expected_x, places=7)
        self.assertGreater(solver.iterations, 1)  # Должен сделать >1 итерации
        self.assertLess(solver.iterations, 10)  # Но не слишком много

    def test_bisection_solver_convergence(self):
        """Тест: Метод дихотомии сходится к правильному значению."""
        solver = BisectionSolver(self.problem, tol=1e-7)
        result = solver.solve(self.target_delta, a=1.0, b=3.0)
        self.assertAlmostEqual(result, self.expected_x, places=6)  # Точность ниже
        self.assertGreater(solver.iterations, 10)  # Требует больше итераций

    def test_newton_fails_to_converge(self):
        """Тест: Метод Ньютона вызывает ошибку, если не сходится (стоп-кран)."""
        # Используем очень малое кол-во итераций, чтобы гарантировать ошибку
        solver = NewtonSolver(self.problem, max_iter=1)
        with self.assertRaisesRegex(RuntimeError, "не сошелся за 1 итераций"):
            solver.solve(self.target_delta, initial_guess=10.0)

    def test_bisection_fails_bad_initial_range(self):
        """Тест: Метод дихотомии вызывает ошибку при неверном начальном интервале."""
        solver = BisectionSolver(self.problem)
        # На отрезке [3, 10] f(x) одного знака для данной задачи
        with self.assertRaisesRegex(ValueError, "функция имеет одинаковый знак"):
            solver.solve(self.target_delta, a=3.0, b=10.0)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False, verbosity=2)
