"""
run.py -- launch the World with pygame rendering.

Usage:
    python run.py

Close the window or press Escape to quit.
"""

from alife import World


def main():
    env = World(render_mode="human")
    observations, infos = env.reset(seed=42, options={'map_name' : "new_4"})

    # Test agents
    env.add_agent(0, 'agent_0') 
    env.add_agent(1, 'agent_1') 

    print(f"Agents: {env.agents}")

    while env.agents:
        actions = {a: env.action_space(a).sample() for a in env.agents}
        observations, rewards, terminations, truncations, infos = env.step(actions)
        env.render()

    print("Episode finished.")
    env.close()


if __name__ == "__main__":
    main()
