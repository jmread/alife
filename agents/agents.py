# Misc. (stuff for display)
from pprint import pprint
import pygame
import matplotlib
matplotlib.use("Agg")
import matplotlib.backends.backend_agg as agg
import pylab
#from matplotlib import pyplot as plt
#import matplotlib.patches as mpatches
#from matplotlib.collections import PatchCollection



def human_interface(sock, world_info):

    '''
        Human Interface
        ---------------

        2. Launch the GUI
        3. Enter the main loop
    '''

    # Extract info
    d_A = world_info['d_A']
    d_S = world_info['d_S']

    # Set some defaults
    COLOR_RED  = (255, 0, 0)
    COLOR_BLUE  = (0, 0, 255)
    COLOR_GREEN  = (0, 255, 0)
    COLOR_YELLOW  = (255, 255, 0)
    COLOR_MAGENTA  = (255, 0, 255)
    COLOR_WHITE  = (255, 255, 255)

    # --------------
    # Launch the GUI
    # --------------

    pygame.display.init()
    pygame.font.init()
    pygame.display.set_caption("Human Agent")
    screen = pygame.display.set_mode((400, 400))

    # Launch plot           # Inches,      100 dots per inch, so the resulting buffer is 400x200 pixels
    rgb_index = [COLOR_RED,COLOR_GREEN,COLOR_BLUE,COLOR_RED,COLOR_GREEN,COLOR_BLUE,COLOR_RED,COLOR_GREEN,COLOR_BLUE,COLOR_YELLOW,COLOR_MAGENTA]
    color_index = 'rgbrgbrgbym'
    style_index = ['-','-','-',':',':',':','--','--','--','-','-']
    fig = pylab.figure(figsize=[4, 2], dpi=100)
    ax = fig.gca()
    lines = [ax.plot(np.arange(100), np.zeros(100), color_index[i]+style_index[i], lw=2) for i in range(d_S)]
    ax.set_ylim([-0.1,1.1])

    color_index = 'kkck'
    style_index = ['-','-',':','o-']
    ax_r=ax.twinx()
    ax_r.set_ylim([-1,10])
    canvas = agg.FigureCanvasAgg(fig)
    liner = [ax.plot(np.arange(100), np.zeros(100), color_index[j]+style_index[j], lw=2) for j in range(d_A+1+1)]

    T = 10000 # max trajectory length
    tau = np.zeros((T,d_S+d_A+1+1))

    # Enter the main loop
    running = True
    action = np.zeros((d_A,),dtype=np.float32)
    t = 1
    while running:
        # Encode and send the action
        o, r, _ = step(sock, action[:], d_S+2)

        # Log
        tau[t,0:d_S] = o
        tau[t-1,-2] = r

        if np.abs(r) > 0:
            # If done, save the finished trajectory
            with open('data.csv', mode='a') as file:
                print("r[t] = %3.2f write out" % r)
                D = np.hstack([np.arange(1,t).reshape(-1,1),tau[1:t,:]])
                np.savetxt(file, D, fmt='%3.2f', delimiter=',')
            tau[:,:] = 0
            t = 0
            tau[t,:] = tau[t,:]

        # Prepare the screen
        screen.fill((0,0,0))
        # Plot env history
        if t > 2:
            for i, line_ in enumerate(lines):  
                line_[0].set_data(np.arange(0,t),tau[0:t, i])
            for j, line_ in enumerate(liner):  
                line_[0].set_data(np.arange(0,t-1),tau[0:t-1, d_S+j])

        #ax.set_data(tau)
        canvas.draw()
        renderer = canvas.get_renderer()
        raw_data = renderer.tostring_rgb()
        size = canvas.get_width_height()
        surf = pygame.image.fromstring(raw_data, size, "RGB")
        screen.blit(surf, (0,0))
        # Draw env state
        for j in range(d_S):
            pygame.draw.circle(screen, COLOR_WHITE, (20+j*20,250), 10)
            pygame.draw.circle(screen, rgb_index[j], (20+j*20,250), int(10*abs(o[j])))
        # Update display
        pygame.display.update()
        pygame.display.flip()
        # Get and send action 
        #print("[Client-Human] a[%d] ~ pi(s[%d])" % (t,t))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    action[1] = 1
                if event.key == pygame.K_RIGHT:
                    action[0] = np.pi/8
                #elif event.key == pygame.K_LEFT:
                #    action = np.array([-np.pi/8,0.],dtype=np.float32)
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                    action[1] = 0
                if event.key == pygame.K_RIGHT or event.key == pygame.K_LEFT:
                    action[0] = 0.0

        tau[t,d_S:d_S+d_A] = action

        # Tick
        t += 1

    sock.close()

#from sklearn.neural_network import MLPRegressor


#from sklearn.ensemble import RandomForestRegressor

# Now, rf_regressor is ready to be trained with your data

def agent_imitation(sock, world_info):
    '''
        Imitation Agent
        ---------------

        Imitation learning, requires some human trajectories to be saved first. 

    '''
    # Extract info
    d_A = world_info['d_A']
    d_S = world_info['d_S']

    # Init stuff
    f = RandomForestRegressor( n_estimators=100, random_state=42  )
    fil = StackedMarkovianFilter(d_S, d_A)

    # Training
    # 1. Load in raw trajectories.
    D = np.loadtxt('data.csv', delimiter=',')

    # 2. Filter/preprocess trajectories (append action)
    X, Y = fil.do_filter(D)

    # 3. Train
    f.fit(X,Y)

    # 4. Prepare default action
    a = np.zeros((d_A,),dtype=np.float32)

    running = True
    while running:
        # Interact with the environment 
        o, r, done = step(sock, a, d_S+2)

        # Filter the state space
        x = fil.push(o, a)

        # Choose action
        a = f.predict(x)
        print("f : %s -> %s" % (o,a))


def agent_interface(sock, world_info):

    '''
        Agent Interface
        ---------------

    '''

    # Extract info
    d_A = world_info['d_A']
    d_S = world_info['d_S']

    # Init stuff
    f = MLPRegressor()
    tau = np.zeros((d_A + d_S + 1,1000))
    D = []

    # Prepare defaults
    a = np.zeros((d_A,),dtype=np.float32)
    g = 0
    t = 0

    running = True
    while running:

        # Interact with the environment 
        o, r, done = step(sock, a,d_S+2)
        g = g + r

        print("[Client-Bot] Receiving observation s[%d] <-- ..." % t)

        # Update/ Conceive next action

        if done:
            # Update
            # store trajectory (s[t], r(s[t+1],a[t+1],....,s[T],a[T]) ; a[t])
            tau[0:t,-1] = g
            D = np.vstack([D, tau[0:t,:]])
            # retrain model
            X = [D[:,0:d_S],D[:,-1]]
            Y = D[:,d_S:d_S+d_A]
            f.fit(X,Y)
            t = 0
            g = 0

        elif f is not None:
            # Clever prediction
            #g = np.max(D[:,-1])
            x = fil.push(s,a)
            a = f.predict(x)
            tau.append((o, a))

        else:
            # Random prediction
            a[:] = np.random.rand(2)
            tau.append((o, a))

        t = t + 1

def hc_interface(sock, world_info):

    '''
        RL Interface
        ---------------

        Hand-coded it works!
    '''

    # Extract info
    d_A = world_info['d_A']
    d_S = world_info['d_S']

    a = np.zeros(d_A,dtype=np.float32)

    while True:

        # Interact with the environment 
        o, r, _ = step(sock, np.array(a), d_S+2)
        # Filter the observation
        x = f.push(o)
        # Decide on an action
        if x[0] > 0.8:
            # Go!
            a = np.array([0,0.8],dtype=np.float32)
        else:
            # Turn!
            a = np.array([np.pi/8,0.0],dtype=np.float32)


class QFilter(): 

    '''
        Provide filtering suited to QLearning
        -------------------------------------
    '''

    def __init__(self,d_S,d_A):
        self.d_S = d_S
        self.d_A = d_A
        self.d_X = 1
        self.d_Y = 1

        self.bins = {
                9 : [0,0.9]
        }
        states = list(range(len(self.bins[9])+1))
        actions = [0, 1]


    def o2x(self,o):
        '''
        color_index = 'rgbrgbrgbym'
        '''
        x = np.zeros(self.d_X)
        x[0] = np.digitize(o[9], bins=self.bins[9])
        return x

    def y2a(self,y):
        '''
            it should also work if y is binary
        '''
        # TODO accelleration and stuff
        if y >= 0.5:
            return np.array([0,0.8],dtype=np.float32)
        else:
            return np.array([np.pi/8,0.0],dtype=np.float32)


def ql2_interface(env):

    '''
        QL Interface II
        ---------------

        Q-Learning, for the test environment (ToyWorld).
        (integrated filter, not used as a separate class).

    '''

    # Initialize Q-table with states {0, 1, 2, 4} and actions {-1, 0, +1}
    states = [0, 1, 2, 3]
    actions = [-1, 0, 1]
    Q = {s: {a: 0.0 for a in actions} for s in states}

    # Hyperparameters
    alpha = 0.1         # Learning rate
    gamma = 0.9         # Discount factor
    epsilon = 0.9       # Exploration rate

    a = 0
    _s = 0
    t = 1


def ql_interface(env):

    '''
        QL Interface I
        --------------

        Q-Learning, for the test environment (ToyWorld).
        (integrated filter, not used as a separate class).

    '''

    # Initialize Q-table with states {0, 1, 2, 4} and actions {-1, 0, +1}
    states = [0, 1, 2, 3]
    actions = [-1, 0, 1]
    Q = {s: {a: 0.0 for a in actions} for s in states}

    # Hyperparameters
    alpha = 0.1         # Learning rate
    gamma = 0.9         # Discount factor
    epsilon = 0.9       # Exploration rate

    a = 0
    _s = 0
    t = 1

    while True:

        # Choose action using epsilon-greedy policy
        if np.random.rand() < epsilon:
            a = np.random.choice(actions)  # Explore: random action
        else:
            a = max(Q[_s], key=Q[_s].get)  # Exploit: best action for current state

        # Interact with the environment 
        o, r, done, info = env.step(np.array([a],dtype=np.float32))

        #print("[Client-Bot] Received observation s[%d=%d] <-- %s after sending action %a ..." % (t,_,str(s),str(a)))
        t_master = int(info['t'])
        assert(t_master != t)

        s = int(o[0])
        if done:
            epsilon = epsilon * 0.9
        #pprint(Q)

        _q = Q[_s][a]
        next_max = max(Q[s].values())  
        Q[_s][a] = _q + alpha * (r + gamma * next_max - _q)

        _s = s

        t = t + 1

class AFilter(): 

    '''
        Provide filtering suited to AWorld
        ----------------------------------
    '''

    def __init__(self,d_S,d_A):
        self.d_S = d_S
        self.d_A = d_A
        self.d_X = 1
        self.d_Y = 1

    def o2x(self,o):
        '''
        color_index = 'rgbrgbrgbym'
        '''
        x = np.zeros(self.d_X)
        x[0] = np.digitize(o[9], bins=[0, 0.9])
        return x

    def y2a(self,y):
        '''
            it should also work if y is binary
        '''
        # TODO accelleration and stuff
        if y >= 0.5:
            return np.array([0,0.8],dtype=np.float32)
        else:
            return np.array([np.pi/8,0.0],dtype=np.float32)



class ToyFilter(): 

    '''
        This filter is built for ToyWorld, 
        which we know takes 1d state and 1d actions.

        We convert o[0]=2 into y=[0,0,1,0] (etc).
        We convert a[0]=0 into x=[-1] and a[0]=1 into x=[1].
    '''

    def __init__(self,d_S,d_A):
        self.d_X = 4
        self.d_Y = 1

    def x2o(self,o):
        '''
            o[0]=2 => y=[0,0,1,0]
        '''
        assert (not np.isnan(o).any())
        x = np.zeros(self.d_X)
        x[int(o[0])] = 1
        return x

    def y2a(self,y):
        return np.array([y * 2 - 1],dtype=np.float32)



from agents.reinforce import REINFORCE

def rl_interface(env):

    '''
        RL Interface
        ---------------

        REINFORCE, for the Aworld Environment
    '''

    print("-- REINFORCE -- ")

    #f = AFilter(d_S,d_A)
    f = ToyFilter(env.d_S,env.d_A)
    p = REINFORCE(f.d_X, f.d_Y)
    a = env.reset()

    while True:

        # Interact with the environment 
        o, r, _ = env.step(a)
        # Filter the observation
        x = f.x2o(o)
        # Decide on an action
        y = p.act_and_learn(x, r)
        a[:] = f.y2a(y)
        #print("a=",a)

    # And launch the appropriate interface
#    if client_name == 'human': 
#        human_interface(sock, world_info)
#    elif client_name == 'agent': 
#        agent_interface(sock, world_info)
#    elif client_name == 'clone': 
#        agent_imitation(sock, world_info)
#    elif client_name[0:2] == 'ql': 
#        ql_interface(SocketEnvironment(sock, world_info))
#    elif client_name == 'rl': 
#        rl_interface(SocketEnvironment(sock, world_info))
#    elif client_name[0:2] == 'sb': 
#        sb_interface(SocketEnvironment(sock, world_info), spec)

