import numpy as np
np_random = np.random.RandomState()

class BugSpace():
    """
        Continous spaces in the form of numpy arrays.
        
        Like the Box space in aigym.
    """

    def __init__(self, low, high, shape):
        """
            Create a space as vector shape.

            Like Box, there are two kinds of input; e.g., 5 continuous values 
            between 0 and 1 (inclusive):
                BugSpace(0.0, 1.0, (3,))    
                BugSpace(np.array([0.0,0.0,0.0]), np.array([1.0,1.0,1.0]))
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

    def contains(self, x):
        """
            Anything in R-space is OK.
        """
        #return isinstance(x, np.ndarray) and x.shape == (self.N,)
        return x.shape == self.shape and (x >= self.low).all() and (x <= self.high).all()

    @property
    def shape(self):
        return self.low.shape

#A = BugSpace(0.0, 1.0, (5,))
#x = np.random.rand(5)
#print(len(x))
#print(A.contains(x))
