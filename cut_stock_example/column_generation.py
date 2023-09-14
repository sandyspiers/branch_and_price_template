from typing import Any

import numpy as np
from docplex.mp.model import Model

from .problem import CutStockProblem


class SubProblem:
    """
    The subproblem solver.
    This is simply an integer knapsack solver, using Cplex

    Attributes
     - problem (CutStockProblem) : the particular problem instances
     - mdl (DocplexModel) : formulation of an integer knapsack using docplex
     - x (list[docplex.dvar]) : Decision vars for knapsack problem

    Methods
     - add_branch_constraints(fixings : list[tuple]) : Adds in the variable fixings provided.
     - remove_branch_constraints() : Removes all fixings, resets for next solve.
     - solve(dual_values : Any) : Solves the subproblem for given dual variables.
                        Dual values become the objective coeffecients of knapsack problem.
    """

    def __init__(self, problem: CutStockProblem):
        """Subproblem constructor.  Saves the problem instances, and creates base KP model"""
        # Save the problem instance
        self.problem = problem
        # Create subproblem knapsack problem model
        self.mdl = Model("SP")
        self.x = self.mdl.integer_var_list(problem.num_items)
        self.mdl.add_constraint(
            self.mdl.scal_prod(self.x, problem.size) <= problem.roll_width
        )

    def add_branch_constraints(self, branch_constraints):
        """Add in the fixed variables as listed in `fixings`"""
        pass

    def remove_branch_constraints(self):
        """Removes all fixed variables"""
        pass

    def get_objective_value(self):
        return self.mdl.objective_value

    def solve(self, dual_values) -> tuple[float | None, Any | None]:
        """
        Solves the subproblem, for given fixed values (pre-provided) and given dual values.

        Parameters
         - dual_values (Any) : The dual values from the restricted master problem.
            these link up with the subproblem to generate new extreme points

        Returns
         - obj_value (float) : objective value of the solution
        If problem infeasible, returns None,None
         - solution (Any) : Solution of the SP, to be used as a new extreme point
        """
        # Maximise the dual values
        assert len(dual_values) == len(self.x)
        self.mdl.maximize(self.mdl.scal_prod(self.x, dual_values))
        sol = self.mdl.solve()
        if sol is not None:
            # Return objval and solution
            return self.mdl.objective_value, np.array(sol.get_value_list(self.x))
        # Otherwise, was infeasible
        return None, None


class RestrictedMasterProblem:
    """
    The restricted master problem solver.

    This class should handle the list of extreme points, and the blend variables.
    We use the trick of auxilary variables to make it easy to formulate this part.

    Attributes
     - problem (CutStockProblem) : problem instance
     - extreme_points (list) : A list of extreme points
     - mdl (DocplexModel) : Docplex model formulation of the RMP

    Methods
     - add_extreme_point(x) : add's `x` to the list of extreme points,
            and adds another blend variable to the RMP formulation.
     - add_branch_constraints(fixings : list[tuple]) : Adds in the variable fixings provided.
     - remove_branch_constraints() : Removes all fixings, resets for next solve.
     - solve() : Solves the RMP.
     - get_dual_values() : returns the dual values that can then be used by the subproblem solver.
     - get_reduced_costs() : returns the reduced cost of the current blend.
    """

    def __init__(self, problem: CutStockProblem):
        """
        RMP constructor.
        Saves the problem, and constructs the RMP model using CPLEX.
        """
        # Save problem
        self.problem = problem

        # List of extreme points
        self.extreme_points = []

        # Build the RMP model
        self.mdl = Model("RMP")

        # Construct an initial lambda dummy, to outline model structure
        # dummy is set with UB=0 so it is never actually included
        dummy = self.mdl.continuous_var(ub=0, name="dummy")
        self.lamba = []  # dont put dummy into list

        # Meet demand constraint
        self.demand_cts = self.mdl.add_constraints(
            dummy >= float(problem.demand[i]) for i in range(problem.num_items)
        )

        # Minimize bins required (equiv. num extreme points needed)
        self.mdl.minimize(dummy)

        # Solution x[b,i]
        self.solution = None

    def add_extreme_point(self, x):
        """Adds a new extreme point the RMP formulation"""
        # Create new lambda variable
        lamba = self.mdl.continuous_var(name=f"lambda_{len(self.extreme_points)}")
        self.lamba.append(lamba)

        # Add point to list
        self.extreme_points.append(x)

        # Add to demand constraint
        for i in range(self.problem.num_items):
            self.demand_cts[i].lhs += lamba * x[i]

        # Add to obj
        self.mdl.objective_expr += lamba

    def add_branch_constraints(self, branch_constraints):
        """Add in the fixed variables as listed in `fixings`"""
        pass

    def remove_branch_constraints(self):
        """Removes all fixed variables"""
        pass

    def solve(self):
        """Solve the RMP LP"""
        self.mdl.solve()

    def is_feasible(self) -> bool:
        """Returns turn only when RMP is feasible and solved successfully"""
        if self.mdl.solution is None:
            return False
        return True

    def get_objective_value(self) -> float:
        """Returns objective value of last solve"""
        return self.mdl.objective_value

    def get_solution(self):
        """Returns the most recent solution"""
        return np.array([l.solution_value for l in self.lamba])

    def get_dual_values(self) -> np.ndarray:
        """Gets the dual values list of size n"""
        return np.array([ct.dual_value for ct in self.demand_cts])

    def get_reduced_cost(self) -> int:
        """Gets the reduced cost of last solve"""
        # For this formulation, reduced cost is 1
        return 1


class ColumnGenerationSolver:
    MAX_ITERATION = 250

    def __init__(self, problem: CutStockProblem):
        self.problem = problem
        self.sp = SubProblem(problem)
        self.rmp = RestrictedMasterProblem(problem)
        x_heur = self.problem.get_heuristic_solution()
        for ep in x_heur:
            self.rmp.add_extreme_point(ep)

    def solve(self, fixings=None):
        """
        Solves the column generation procedure, returns a partial solution
        """
        self._add_branch_constraints(fixings)
        iteration = 0
        while iteration < self.MAX_ITERATION:
            # Solve RMP
            iteration += 1
            self.rmp.solve()

            # Check feasibility (fixed values may make it infeasible)
            if not self.rmp.is_feasible():
                self._remove_branch_constraints()
                return None, None

            # Get dual values
            dual_values = self.rmp.get_dual_values()
            reduced_cost = self.rmp.get_reduced_cost()

            # Generate extreme point
            sp_objval, ep = self.sp.solve(dual_values)
            self.rmp.add_extreme_point(ep)

            # Check stopping criteria
            if (sp_objval - reduced_cost <= 1e-6 and self.problem.sense == "max") or (
                sp_objval - reduced_cost >= 1e-6 and self.problem.sense == "min"
            ):
                break
        self._remove_branch_constraints()
        return self.rmp.get_solution()

    def _add_branch_constraints(self, fixings):
        """Add in the fixed variables as listed in `fixings`"""
        self.rmp.add_branch_constraints(fixings)
        self.sp.add_branch_constraints(fixings)

    def _remove_branch_constraints(self):
        """Removes all fixed variables"""
        self.rmp.remove_branch_constraints()
        self.sp.remove_branch_constraints()
