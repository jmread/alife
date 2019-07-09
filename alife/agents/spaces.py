import numpy as np
np_random = np.random.RandomState()

class ContinuousBugSpace():
    """
        A continous spaces determined by a numpy arrays.
        
        Like the Box space in gym.
    """

    def __init__(self, low, high, shape=None):
        """
            Create a space as vector shape.
        """
        if shape is None:
            assert low.shape == high.shape
            self.low = low
            self.high = high
        else:
            assert np.isscalar(low) and np.isscalar(high)
            self.low = np.zeros(shape) + low
            self.high = np.zeros(shape) + high

    def sample(self):
        """
            Uniformly randomly sample a random element of this space
        """
        return np_random.uniform(low=self.low, high=self.high, size=self.low.shape)

    @property
    def shape(self):
        return self.low.shape


class DiscreteBugSpace():

    def __init__(self, n):
        assert n >= 0
        self.n = n

    def sample(self):
        return np.random.choice(self.n)
