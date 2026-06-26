# Numpy
import numpy as np
np.set_printoptions(threshold=np.inf, precision=1)

# For network
from net.net_utils import get_connection, base_addr as server_addr, base_port as server_port
from net.net_utils import parse_string

# For the environment
import gymnasium as gym
from gymnasium import spaces
from gymnasium import ObservationWrapper, ActionWrapper

# For the agent
from stable_baselines3 import DDPG
from stable_baselines3 import SAC
from stable_baselines3 import DQN
from stable_baselines3 import PPO

class SocketEnvironment(gym.Env):

    '''
        Socket Environment
        ------------------

        Externally, this should look like a standard gymnasium environment.

        Main assumption (TODO change this): 

        We are using continuous spaces, 
            between -1 and +1 for action space (of dimension d_A). 
            between 0 and 1 for observtaion space (of dimension d_S). 
    '''

    def __init__(self,sock, world_info):
        super(SocketEnvironment, self).__init__()

        self.sock = sock
        self.d_A = world_info['d_A']
        self.d_S = world_info['d_S']
        self.n = self.d_S + 2

        self.observation_space = spaces.Box(low=0, high=1, shape=(self.d_S,), dtype=np.float32)
        self.action_space = spaces.Box(low=-1, high=+1, shape=(self.d_A,), dtype=np.float32)
        self.state0 = np.zeros(self.d_S,dtype=np.float32)
        #self.action_space = spaces.Discrete(2)

    def reset(self, seed=None, options=None):
        print("EOE/RESET: "+str(self.state0))
        return self.state0, {}

    def step(self, action):
        '''
            0. Clear the backlog
            1. Send the action
            2. Wait for, and decode the observation

            TODO proper synchronisation
        '''
        assert (not np.isnan(action).any())

        # Clear the blacklog
        # TODO

        # Encode and send the action
        #print("               Sending! (length %d): %s" % (len(action),str(action)))
        self.sock.send(action.tobytes())

        # Wait for new message corresponding to *that* action
        data = np.frombuffer(sock.recv(self.n*4), dtype=np.float32)
        #print("               Received! (length %d): %s" % (len(data),str(data)))

        # Decompose into elements
        obs = data[0:-2]
        rwd = data[-2]
        done = bool(abs(rwd) > 0)
        if done:
            self.state0[:] = obs
        t = data[-1]

        return obs, rwd, done, False, {'t' : t}

    def render(self, mode='human'):
        # Optional: Render the environment's state
        pass


class StackedMarkovianFilter(): 
    '''
        Stacked Markov Filter
    '''

    def __init__(self,d_S,d_A):
        self.d_S = d_S
        self.d_A = d_A
        self._a = np.zeros(d_A)

    def do_filter(self,D):
        # append state and prev-action space, 
        n, d = D.shape
        X = np.zeros((n-1,self.d_S+self.d_A))
        X[:,0:self.d_S] = D[1:,0:self.d_S]
        X[:,self.d_S:] = D[0:-1,self.d_S:self.d_S+self.d_A]
        Y = D[1:,0:self.d_A]
        return X, Y

    def push(self,o,a):
        x = np.zeros((1,self.d_S+self.d_A))
        x[0,0:self.d_S] = o
        x[0,self.d_S:] = self._a[:]
        self._a = a
        return x


class AlifeWrapper(ObservationWrapper):

    '''
        An official best wrapper for ALife.
        Let's start things simple (GPS-observation only) then try Markovian stacking. 
    '''

    def __init__(self, env):
        super(AlifeWrapper, self).__init__(env)
        IDX_FLAG = 9
        # Define the new observation space to match the filtered observations (2 elements)
        obs_shape = (1,)
        self.observation_space = gym.spaces.Box(
            low=env.observation_space.low[[IDX_FLAG]],
            high=env.observation_space.high[[IDX_FLAG]],
            dtype=env.observation_space.dtype
        )

    def observation(self, observation):
        # Return only the 3rd and 7th values of the observation
        return observation[[IDX_FLAG]]



def sb_client(env, spec):

    '''
        Stable Baselines Filter
        -----------------------
    '''

    # TODO Put the right wrapper on it; this is not working!!
    #env = AlifeWrapper(env)

    if spec == 'SAC':
        model = SAC("MlpPolicy", env, verbose=1)
    elif spec == 'DDPG': 
        model = DDPG("MlpPolicy", env, verbose=1)
    elif spec == 'PPO': 
        model = PPO("MlpPolicy", env, verbose=1)
    else:
        raise ValueError('Now such specification')

    model.learn(total_timesteps=10000)
    model.save("%s_dpg_custom_env" % spec)

import sys

if __name__ == "__main__":
    """
        Connect to server with argument name_version@ip:port.
        Sever will send info about the World it is hosting
        Create an environment, wrap it around the socket, 
        Launch the agent. 
    """

    server_str = sys.argv[1]

    # Parse connection details 
    client_name, server_addr, server_port = parse_string(server_str)

    # Connect to server
    print('[Client] Connecting (via: %s@%s:%d)' % (client_name,server_addr,server_port))
    sock, world_info = get_connection(server_addr,server_port)
    print("[Client] Connected, world:", str(world_info))

    # Send "Hello, World! I am ... God? Player?"
    print("[Client] Hello world! I am:", str(client_name))
    sock.send(client_name.encode())

    # Declare the Environment
    cenv = SocketEnvironment(sock, world_info)

    if '_' not in client_name: 
        client_fn = getattr(__import__('client'), client_name+'_client')
        client_fn(cenv)
    else:
        client_type, spec = client_name.split("_")
        client_fn = getattr(__import__('client'), client_type+'_client')
        client_fn(cenv, spec)

