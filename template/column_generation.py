from problem import Problem
from typing import Any


class SubProblem:
    """
    The subproblem solver.
    The particular implementation of `solve(...)` is highly dependent on the specific application.
    However, it must be able to fixed (and release) variables and resolve.

    Attributes
     - problem (Problem) : the particular problem instances

    Methods
     - add_fixed_vars(fixings : list[tuple]) : Adds in the variable fixings provided.
     - remove_fixed_vars(fixings : list[tuple]) : Removes all fixings, resets for next solve.
     - solve(dual_values : Any) : Solves the subproblem for given dual variables.
    """

    def __init__(self, problem: Problem):
        """Basic subproblem constructor, only contains `problem` attribute"""
        self.problem = problem

    def add_fixed_vars(self, fixings):
        """Add in the fixed variables as listed in `fixings`"""
        pass

    def remove_fixed_vars(self):
        """Removes all fixed variables"""
        pass

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
        obj_val: float | None = None
        solution: Any | None = None
        return obj_val, solution


class RestrictedMasterProblem:
    """
    The restricted master problem solver.

    This class should handle the list of extreme points, and the blend variables.
    It should have a quick way of introducing new extreme points and continuous dvars.

    Attributes
     - extreme_points (list) : A list of extreme points
     - problem (Problem) : problem instance

    Methods
     - add_extreme_point(x) : add's `x` to the list of extreme points, and adds another
            blend variable to the RMP formulation.
     - add_fixed_vars(fixings : list[tuple]) : Adds in the variable fixings provided.
     - remove_fixed_vars(fixings : list[tuple]) : Removes all fixings, resets for next solve.
     - solve() : Solves the RMP.
     - get_dual_values() : returns the dual values that can then be used by the subproblem solver.
     - get_reduced_costs() : returns the reduced cost of the current blend.
    """

    def __init__(self, problem: Problem):
        self.problem = problem
        self.extreme_point = []
        self.solution = None

    def add_extreme_point(self, x):
        """Adds a new extreme point to the formulation, and to the RMP formulation"""
        # Add point to list
        self.extreme_point.append(x)
        # Add in a new blend dvar lambda to the RMP formulation
        pass

    def add_fixed_vars(self, fixings):
        """Add in the fixed variables as listed in `fixings`"""
        pass

    def remove_fixed_vars(self):
        """Removes all fixed variables"""
        pass

    def solve(self):
        """Solve the RMP LP"""
        pass

    def is_feasible(self) -> bool:
        """Returns turn only when RMP is feasible and solved successfully"""
        pass

    def get_objective_value(self) -> float:
        """Returns objective value of last solve"""
        pass

    def get_solution(self):
        """Returns the most recent solution"""
        pass

    def get_dual_values(self):
        """Gets the dual values list of size n"""
        dual_values: Any = None
        return dual_values

    def get_reduced_cost(self):
        """Gets the reduced cost of last solve"""
        reduced_cost: Any = None
        return reduced_cost


class ColumnGenerationSolver:
    MAX_ITERATION = 250

    def __init__(self, problem: Problem):
        self.problem = problem
        self.sp = SubProblem(problem)
        self.rmp = RestrictedMasterProblem(problem)

    def solve(self, fixings):
        self._add_fixed_vars(fixings)
        iteration = 0
        while iteration < self.MAX_ITERATION:
            # Solve RMP
            iteration += 1
            self.rmp.solve()

            # Check feasibility (fixed values may make it infeasible)
            if not self.rmp.is_feasible():
                return None, None

            # Get dual values
            dual_values = self.rmp.get_dual_values()
            reduced_cost = self.rmp.get_reduced_cost()

            # Generate extreme point
            ep, sp_objval = self.sp.solve(dual_values)
            self.rmp.add_extreme_point(ep)

            # Check stopping criteria
            if (sp_objval - reduced_cost <= 1e-6 and self.problem.sense == "max") or (
                sp_objval - reduced_cost >= 1e-6 and self.problem.sense == "min"
            ):
                return self.rmp.get_objective_value(), self.rmp.get_solution()
        self._remove_fixed_vars()

    def _add_fixed_vars(self, fixings):
        """Add in the fixed variables as listed in `fixings`"""
        self.rmp.add_fixed_vars(fixings)
        self.sp.add_fixed_vars(fixings)

    def _remove_fixed_vars(self):
        """Removes all fixed variables"""
        self.rmp.remove_fixed_vars()
        self.sp.remove_fixed_vars()
