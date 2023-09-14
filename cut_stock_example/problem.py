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
        # Number of different sizes
        self.num_items = len(size)
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

    def get_heuristic_solution(self) -> np.ndarray:
        """
        Returns a greedy heuristic solution by just packing in order
        """
        x = [np.zeros(self.num_items)]
        for i in range(self.num_items):
            d = 0
            while d < self.demand[i]:
                if x[-1].dot(self.size) + self.size[i] > self.roll_width:
                    x.append(np.zeros(self.num_items))
                x[-1][i] += 1
                d += 1
        return np.array(x)

    def get_bins_upper_bound(self) -> int:
        """
        Get the maximum number of bins that could be required.
        """
        return self.get_heuristic_solution().shape[0]

    def get_cplex_model(self) -> Model:
        # Sets
        B = range(self.get_bins_upper_bound())  # bins
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
