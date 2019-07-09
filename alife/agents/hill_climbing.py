import numpy as np
from numpy.random import choice as sample
from numpy.random import rand
from alife.agents.models import SLP, MLP, ESN, linear, sigmoid

class SimpleHillClimber():
    '''
        Hill Climbing Agent.

        Just a simple accept/reject routine. 
    '''

    def __init__(self, obs_space, action_space, max_episode_length=50, num_episodes_per_test=100, alpha=0.1, H=0, **kwargs):
        """
            Init.
        """

        self.state_space = obs_space
        self.act_space = action_space
        n_states = obs_space.shape[0]
        n_actions = -1
        fo = linear

        try:
            # continous action space
            n_actions = action_space.shape[0]
            self.stochastic_policy = False
            print("[Info] Continuous action space; discrete policy")
        except:
            # discrete action space
            n_actions = action_space.n
            fo = sigmoid
            self.stochastic_policy = True
            print("[Info] Discrete action space; stochastic policy")

        # Max length of an episode 
        self.T = max_episode_length
        # Step counter
        self.t = 0
        # Each episode gets longer by this much after each round
        self.T_increment = 0

        # Number of episodes per test
        self.num_episodes_per_test = num_episodes_per_test
        # Test (set of episodes) counter
        self.i_episode = 0
        # Round (set of episodes) counter: successful ones; with an accept
        self.n_success = 0
        # Round (set of episodes) counter: total
        self.n_rounds = 0
        # Return for the current episode
        self.R = 0 
        # Mean return per episode (best so far)
        self.best_avg_R = -100000
        # Store test result here
        self.memory = np.zeros(num_episodes_per_test)
        # Probability of random restart in the hill climbing
        self.p_restart = 0.1
        # Other data (stored for debugging purposes)
        self.data = []

        # Alpha (step size / learning rate)
        self.alpha_init = alpha
        self.alpha = self.alpha_init
        self.alpha_decay = 1 # 0.99999

        # Specified number of hidden units 
        if 'H' in kwargs:
            n_hidden = kwargs['H']

        # Create the model/policy
        try:
            self.h = self.load(H)
        except: 
            print("Warning: no saved versions to load")

            if H > 0:
                self.h = MLP(n_states,n_actions,H,fo)
            elif H < 0:
                self.h = ESN(n_states,n_actions,-H,fo)
            else:
                self.h = SLP(n_states,n_actions,fo)

        self.h_prop = self.h.copy(modify=True)



    def update_policy(self,obs,reward,done=False):
        """
            Update Policy.

            We get an idea how well we are performing by the reward. Although, 
            of course this reward is associated with this agent in general, so 
            we should store an episode before making any decision. The storage 
            is done here, but we can store a batch elsewhere and feed it each 
            instance here if we want too -- should make no difference. 

        """

        # Update the return for the current episode
        self.R = self.R + reward

        # Counting (each step of the episode of max length T)
        self.t = self.t + 1

        if self.t > self.T or done:
            # End of the episode ; reset
            self.memory[self.i_episode] = self.R
            self.t = 0
            self.R = 0
            self.alpha = self.alpha * self.alpha_decay
            self.i_episode = self.i_episode + 1

        if self.i_episode >= self.num_episodes_per_test:
            # End of set of episodes ; reset
            self.i_episode = 0
            self.n_rounds += 1
            self.T = self.T + self.T_increment

            # Calculate the average return per episode
            avg_R = np.mean(self.memory)
            # Store data 
            self.data.append(avg_R)

            # Do we accept the new set of parameters?
            if avg_R > self.best_avg_R:
                # Accept
                self.best_avg_R = avg_R
                self.h = self.h_prop.copy()
                self.n_success += 1
            else:
                # Reject (i.e., back to the old policy)
                self.h_prop = self.h.copy()

            # Modify the policy again / take another step in parameter space
            self.h_prop.modify(alpha=self.alpha,alpha_b=self.alpha*0.1,prob_reset=self.p_restart)



    def act(self,obs,reward=None,done=False):
        """
            Act.

            Parameters
            ----------

            obs : numpy array
                the state observation
            reward : float
                the reward obtained in this state
                (If None, we still need to act anyway)
            done : if the episode is finished

            Returns
            -------

            numpy array
                the action to take
        """

        # If given a reward, it means we can update the policy already!
        if reward is not None:
            self.update_policy(obs,reward,done)

        y = self.h_prop.predict(obs)

        if self.stochastic_policy:
            # stochastic policy (suppose softmax), return a discrete action
            return np.argmax(y)
        else:
            # deterministic policy (suppose linear), clip the continuous action into range
            print("y", y)
            print("clipped", self.act_space.low)
            print("clipped", self.act_space.high)
            a = np.clip(y, self.act_space.low, self.act_space.high)
            print("a", a)
            return a

        return y

    def __str__(self):
        ''' Return a string representation/description for this agent.
            This will appear as label when we click on the bug in ALife
        '''
        s = ""
        s += "Hill Climber (%s)\n" % str(self.h.__class__.__name__) 
        s += "step=%d/%d\n" % (self.t,self.T)  
        s += "episode=%d/%d\n" % (self.i_episode,self.num_episodes_per_test)  
        s += "avg(R)=%3.2f\n" % self.R
        s += "avg(R)*=%3.2f\n" % self.best_avg_R
        s += "[" 
        j = 1
        while j < len(self.data) and j <= 10:
            s += "%3.2f " % self.data[-j]
            j = j + 1
        s += "]\n" 
        return s + ("alpha=%3.2f\naccept rate=%d/%d" % (self.alpha,self.n_success,self.n_rounds))

