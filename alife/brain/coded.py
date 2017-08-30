from numpy import *

from numpy.linalg import norm

class Coded():
    '''
        Coded
        -----
        A hard-coded brain, with some simple (and incomplete) set of responses to certain sensory input.
    '''

    food = 1
    _y = zeros(2)

    def __init__(self,food_id):

        self.limit = 1. + random.rand() * 6.
        self._y[1] = random.rand() * self.limit
        self.my_id = food_id
        if food_id == 3: 
            # Herbivore
            self.food = 1
            self.friend = 2
            self.enemy = 0
        else: 
            # Predator
            self.food = 2
            self.friend = 0
            self.enemy = 1

    def act(self,x,r=None):

        y = ones(2) * self._y

        BODY_INDEX = 0
        ANT1_INDEX = 3
        ANT2_INDEX = 6

        if x[BODY_INDEX+self.food] >= 1.0 and x[BODY_INDEX+self.friend] < 0.1 and x[BODY_INDEX+self.enemy] < 0.1:
            # Under food (and nothing else), stop
            y[1] = 0.

        elif x[ANT1_INDEX+self.food] > 0.1 or x[ANT2_INDEX+self.food] > 0.1:
            # If food in field of vision, proceed
            y[1] = self.limit * random.rand()
            y[0] = 0.0

        elif x[ANT1_INDEX+self.friend] > 0.3 or x[ANT2_INDEX+self.friend] > 0.3:
            # If friend in field of vision, stop and rotate
            y[1] = 0.01
            y[0] = 0.1 + random.randn() * 0.1

        elif x[ANT1_INDEX+self.enemy] > 0.1 or x[ANT2_INDEX+self.enemy] > 0.1:
            # If enemy in field of vision, stop and rotate
            y[1] = 0.01
            y[0] = 0.1 + random.randn() * 0.1

        elif min(x[ANT1_INDEX:ANT1_INDEX+3]) > 0.2 or min(x[ANT2_INDEX:ANT2_INDEX+3]) > 0.2:
            # Wall ahead, turn
            y[1] = 0.01
            y[0] = 0.1 + random.randn() * 0.1

        elif sum(x[ANT1_INDEX:ANT1_INDEX+3]) < 0.05 and sum(x[ANT2_INDEX:ANT2_INDEX+3]) < 0.05:
            # Nothing, select a random speed
            y[1] = self.limit * random.rand()
            y[0] = 0.01

        # Else continue as before ...
        return y

    def learn(self,r):
        return

    def copy_of(self):
        return Coded(self.my_id)
