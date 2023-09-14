from cut_stock_example.problem import CutStockProblem


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
