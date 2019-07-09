#from alife.rl.agent import Agent
import numpy as np

class Dumb():
    '''
        A dumb agent; does nothing.
    '''

    def __init__(self, obs_space, act_space, **kwargs):
        """
            Init.


            Parameters
            ----------

            obs_space : BugSpace
                observation space
            act_space : BugSpace
                action space

        """
        self.obs_space = obs_space
        self.act_space = act_space
        self.name = "Fred"
        if 'name' in kwargs:
            self.name = kwargs['name']


    def __str__(self):
        ''' Return a string representation (e.g., a label) for this agent '''
        return ("Dumb Agent\nName: %s" % self.name)

    def act(self,obs,reward,done=False):
        """
            Act.

            Parameters
            ----------

            obs : numpy array of length D
                the state at the current time
            reward : float
                the reward signal at the current time

            Returns
            -------

            A number array of length L 
                (the action to take)
        """

        n_actions = self.act_space.shape[0]
        return np.zeros((n_actions))


