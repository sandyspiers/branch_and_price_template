from cut_stock_example.problem import CutStockProblem

ct = CutStockProblem.random(1000)
ct.cplex_solve(log_output=True)
