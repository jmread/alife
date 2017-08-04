from numpy import *

class SARSA():

    alpha = 0.1
    epsilon = 0.5
    gamma = 0.9

    def __init__(self,D,L):
        self.D = D
        self.L = L                # ...
        K = 2**D                  # discrete states
        J = 2**L                  # discrete actions
        self.Q = random.rand(K,J) # genetically inherited
        self._s = 0
        self._a = 0

    a2y = array([
            [+0.0,0.01],
            [+0.2,1.5],
            [-0.2,1.5],
            [+0.0,1.5]
        ])


    def act(self,x,r,done=False):
        '''
            Act
            ----
        '''

        # discretize
        s = int(((x > 0.2)*(2**arange(x.size,dtype=uint64))).sum())

        # GET STATE/ACTION
        _s = self._s # previous state
        _a = self._a # previous action

        # CHOOSE AN ACTION
        a = 0
        if random.rand() > self.epsilon:
            a = random.choice(2**self.L)
        else:
            a = argmax(self.Q[s,:])
        self.epsilon = self.epsilon * 0.99999

        # UPDATE MODEL
        self.Q[_s,_a] = self.Q[_s,_a] + self.alpha * (r + self.gamma * self.Q[s,a] - self.Q[_s,_a])

        # SET STATE/ACTION
        self._s = s
        self._a = a

        # undiscretize
        y = self.a2y[a] #unpackbits(uint8(a))[-self.L:] * array([0.1,2.1])
        return y

    def copy_of(self):
        b = SARSA(self.D,self.L)
        b.Q = copy(self.Q)
        b.alpha = self.alpha + random.randn() * (b.alpha * 0.05)
        b.epsilon = self.epsilon + random.randn() * (b.epsilon * 0.05)
        b.gamma = self.gamma + random.randn() * (b.gamma * 0.05)
        return b


