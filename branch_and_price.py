from __future__ import annotations  # Needed for nice future-typing
from typing import Any
from problem import Problem
from column_generation import ColumnGenerationSolver


class Solution:
    """
    A basic container for a solution of a problem instance (can be incumbent or optimal).
    Particular implementation of this class depends on specific application,
    but **must** always have an objective value!
    """

    def __init__(self, x: Any, objective_value: float) -> None:
        """
        A basic constructor for a solution of a problem instance (can be incumbent or optimal).

         - x (any) : given solution
         - objective_value(float) : objective value of solution on problem
        """
        self.x = x
        self.objective_value = objective_value


class Node:
    """
    A node of the branch and bound tree.

    Contains a `root_problem`, a `parent_node`, and a fixed variable.
    Then, call `get_fixed_vars()` to get a list of variable fixings from all parent nodes.
    Calling `solve` solves the root problem with the given variable fixings.
    """

    def __init__(self, parent_node: Node | None) -> None:
        """
        Constructor not to be called directly!
        Instead use the classmethod `get_root_node` or `get_child_node`!
        """
        # Parent node (None if root node)
        self._parent_node = parent_node
        # Reference to the root problem
        if isinstance(parent_node, Node):
            self._cg_solver: ColumnGenerationSolver = parent_node._cg_solver
        # The fixed variable at this node
        self._fixed_var: tuple = None

    def add_fixed_var(self, var, val):
        """
        Add a fixed variable to this node.
        Fixes `var` to `val`.
        Specific notation/implementation should depend on application.
        """
        self._fixed_var = (var, val)

    def get_fixed_vars(self) -> list[tuple]:
        """
        Returns a list of all fixed values at a node.
        Recursively calls the parents fixed variable, and its parents, etc.etc.
        Terminates at the root node.
        """
        if self._parent_node is None:
            if self._fixed_var is None:
                return []
            else:
                return [self._fixed_var]
        else:
            return [self._fixed_var] + self._parent_node.get_fixed_vars()

    def solve(self) -> tuple[float, Any]:
        """
        Solves this node, based on the info in this branch and the root problem
        Returns the bound, and the partial solution.
        The partial solution is anything required to either
         1. Repair solution to get a new incumbent, or
         2. Make branching decisions off.
        """
        return self._cg_solver.solve(self.get_fixed_vars())

    def _set_cg_solver(self, cg_solver: ColumnGenerationSolver):
        """
        Sets the root problem
        """
        self._cg_solver = cg_solver

    @classmethod
    def create_child(cls, node: Node):
        """
        Returns a child of `node`.
        """
        return cls(node)

    @classmethod
    def get_root_node(cls, problem: Problem):
        """
        Creates the first root node.
        This starts with formulated the base `RootProblem` for the solver.
        No parent node, and no var fixings.
        """
        node = Node(None)
        node._set_cg_solver(ColumnGenerationSolver(problem))
        return node


class BranchAndPriceSolver:
    """
    An instance of branch and bound solver.
    """

    # Default parameters.
    # Should be a dictionary containing parameter -> value
    DEFAULT_PARAMETERS = {}

    def __init__(self, problem: Problem) -> None:
        """
        Basic constructor of branch and bound solver for a problem instance
        """
        # Problem instance to solve
        self.problem: Problem = problem
        # Grab the default parameter set
        self.parameters = BranchAndPriceSolver.DEFAULT_PARAMETERS
        # Best solution and incumbent
        self.solution: Solution = None
        self._incumbent_solution: Solution = None
        # List of nodes yet to explore
        self._node_list: list[Node] = []

    def solve(self):
        """
        Solves the problem instance using branch and bound.
        """
        # Add in the root node
        self._node_list.append(Node.get_root_node(self.problem))

        # While there are still nodes to explore
        while len(self._node_list) > 0:
            # Get the next node
            node = self._get_next_node()

            # Solve the node
            node_bound, partial_solution = node.solve()

            # Attempt to repair
            repaired_solution = self._heuristic_repair(partial_solution)

            # Did it manage to repair a solution?
            if repaired_solution is not None:
                # Is the incumbent still none?
                if self._incumbent_solution is None:
                    self._incumbent_solution = repaired_solution
                # If not, is this new solution better?
                elif (
                    repaired_solution.objective_value
                    > self._incumbent_solution.objective_value
                ):
                    # Improved solution found!
                    self._incumbent_solution = repaired_solution

            # Check if upper bound < lower bound
            if (
                node_bound < self._incumbent_solution.objective_value
                and self.problem.sense == "max"
            ) or (
                node_bound > self._incumbent_solution.objective_value
                and self.problem.sense == "min"
            ):
                # Bound failed!!
                # Dont branch! Go straight to next node
                continue

            # Create branches
            children = self._make_children(node, partial_solution)
            if children is not None:
                for child in children:
                    self._node_list.append(child)

        # Branch and bound complete
        self.solution = self._incumbent_solution
        return self.solution

    def _get_next_node(self) -> Node:
        """
        Gets the next node from the list, and removes it from the list
        Suggestion is to use `self._node_list.pop(index)`.

        For instance,
         - `return self._node_list.pop(-1)` would get the last node (most recently added).
            This is equivalently **depth-first-search**.
         - `return self._node_list.pop(0)` would get the first node.
            This is equivalently **breadth-first-search**.
        Alternatively, could scan each node for best bound / most promising
        """
        # Use depth first as example...
        return self._node_list.pop(-1)

    def _heuristic_repair(self, partial_solution: Any) -> Solution | None:
        """
        Attempts to repair a partial solution.
        If succeeds, returns Solution.
        Otherwise, returns none.
        """
        return None

    def _make_children(
        self, parent_node: Node, partial_solution: Any
    ) -> tuple[Node, Node] | None:
        """
        Takes the partial solution, and returns 2 new child nodes.
        These nodes are added to node list in the order they are returned.
        Therefore, branching direction is also technically managed here.
        """
        # Create children.
        child1 = Node.create_child(parent_node)
        child2 = Node.create_child(parent_node)

        # Now, base on `partial solution`, choose a branching variable
        # Then carefully select which direction to branch first.
        # child1.add_fixed_var(var,val1)
        # child2.add_fixed_var(var,val2)
        # If there are no fractional, return None
        return child1, child2
