from __future__ import annotations  # Needed for nice future-typing

from typing import Any


class Problem:
    """
    All information required to solve a problem instance.
    This includes parameters, sets, coefficients, constraints etc.
    Once created, the Solver class should not modify anything in here.
    Should also contain a *sense*, which is whether the problem is a max or min problem.
    Particular implementation of this class depends on specific application.
    """

    def __init__(self) -> None:
        """
        Base problem instance
        """
        # If problem is maximisation or minimisation type
        self.sense = "max"
        if self.sense not in ["max", "min"]:
            raise TypeError(f"Problem sense is not valid : {self.sense}")

    @classmethod
    def example_generator(cls) -> Problem:
        """
        Use an instance generator to create your problem.
        Very useful for generating instances of a similar type.
        """
        return cls()
