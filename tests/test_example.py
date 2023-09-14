from cut_stock_example.column_generation import ColumnGenerationSolver
from cut_stock_example.problem import CutStockProblem

""" Test problem """


def test_random_constructor():
    ct = CutStockProblem.random(100)
    assert isinstance(ct, CutStockProblem)


def test_heuristic():
    ct = CutStockProblem.random(100)
    x = ct.get_heuristic_solution()
    assert (x.sum(axis=0) >= ct.demand).all


def test_cplex_solver():
    ct = CutStockProblem.random(100)
    ct.cplex_solve()


""" Test column generation """


def test_cs_convergence():
    ct = CutStockProblem.random(100)
    cg = ColumnGenerationSolver(ct)
    cg.solve()


def test_valid_bound():
    # Column generation **should** be an upper bound
    ct = CutStockProblem.random(25)
    cg = ColumnGenerationSolver(ct)
    cg.solve()

    assert cg.rmp.get_objective_value() >= ct.cplex_solve()
