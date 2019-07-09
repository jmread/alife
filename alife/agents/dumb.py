#from alife.rl.agent import Agent
import numpy as np

class DumbAgent():
    '''
        A dumb agent; just takes random actions.
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
            **kwargs : additional arguments

        """

        self.obs_space = obs_space
        self.act_space = act_space

        self.name = "Fred"
        if 'name' in kwargs:
            self.name = kwargs['name']


    def __str__(self):
        ''' Return a string representation (e.g., a label) for this agent '''
        return ("\nName: %s" % self.name)

    def act(self,obs,reward,done=False):
        """
            Act.

            Parameters
            ----------

            obs : numpy array 
                observation of the current state
            reward : float
                the current reward recieved
            done : 
                True if the episode is over now

            Returns
            -------

            A random action to take
        """

        return self.act_space.sample()


