import numpy as np
from docplex.mp.model import Model


class CutStockProblem:
    """
    An instance of the cutting stock problem
    """

    def __init__(self, roll_width: int, size: np.ndarray, demand: np.ndarray) -> None:
        """
        Create instance
        """
        assert len(size) == len(demand)
        assert roll_width >= size.max()
        # Width of one roll
        self.roll_width = roll_width
        # Size of cuts
        self.size = size
        # Demand for each cut
        self.demand = demand
        self.sense = "max"

    @classmethod
    def random(cls, n):
        """
        Generate a random instance
        """
        sizes = np.random.randint(1, 100, size=n)
        demands = np.random.randint(1, 100, size=n)
        roll_width = np.random.randint(sizes.max(), sizes.sum())
        return cls(roll_width, sizes, demands)

    def get_cplex_model(self) -> Model:
        # Sets
        B = range(len(self.demand))  # bins
        I = range(len(self.size))  # items
        BI = [(b, i) for b in B for i in I]

        # Model and dvars
        m = Model("CutstockModel")
        x = m.integer_var_dict(BI, name="n_items")
        y = m.binary_var_dict(B, name="bin")

        # Meet demand
        m.add_constraints(m.sum(x[b, i] for b in B) >= self.demand[i] for i in I)

        # Dont exceed roll width, if roll chosen
        m.add_constraints(
            m.sum(x[b, i] for i in I) <= self.roll_width * y[b] for b in B
        )

        # Minimize bins required
        m.minimize(m.sum(y))

        return m

    def cplex_solve(self, **kwargs) -> float:
        m = self.get_cplex_model()
        m.solve(**kwargs)
        return m.objective_value
