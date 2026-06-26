#! /usr/bin/env python3

# Standard Python libraries
import threading 
import time

# Math libraries
import numpy as np
np.set_printoptions(threshold=np.inf, precision=1)

# Only needed for some asserts
import numbers

# For networking
from net.carriers import Carrier
from net.net_utils import host_connections, base_port

# For database
import sqlite3

# TODO import only as specified on the command line
from worlds.toyworld.toyworld import ToyWorld
from worlds.bugworld.aworld import World

def print_carriers(carrier_dic, DEBUG=False): 
    if not DEBUG:
        return
    print("---------- CARRIERS ------------")
    for c_id in carrier_dic.keys():
        print(('%2d | ' % c_id) + ("status=%d, s_id=%d, info=%s" % (carrier_dic[c_id].status,0,carrier_dic[c_id].info)))
    print("--------------------------------")

class Server:
    """ A Headless Server.
    """

    def __init__(self, env, server_cfg):

        FPS = server_cfg['fps']

        self.RUNNING = True

        # Init database table
        conn = sqlite3.connect(env.__class__.__name__+'.db')
        cursor = conn.cursor()
        for create_table_query in [
            "CREATE TABLE IF NOT EXISTS Users (Name TEXT PRIMARY KEY, code TEXT, points INTEGER DEFAULT 0, health FLOAT, pos_x FLOAT, pos_y FLOAT);", 
            "CREATE TABLE IF NOT EXISTS Records (Run TEXT NOT NULL, Name TEXT NOT NULL, Tick INTEGER DEFAULT 0, Reward FLOAT);"]: 
            cursor.execute(create_table_query)

        print("[Server] Lauch manager thread (to host connection, provide carriers)")
        waiting_room = {}
        carrier_dic = {} 

        world_info = env.get_info()
        manager = threading.Thread(target=host_connections,args=(self,base_port,waiting_room,world_info))
        manager.start()

        ## MAIN LOOP ##

        print("[Server] Enter main loop")
        t = 0                                     
        while self.RUNNING:
            t = t + 1

            # -------------------------------------------------------------
            # Managing Carriers <-> Creatures (Network Overhead)
            # For all sprites: Add to register (if alive and carried) or decommision (if no carrier).
            # -------------------------------------------------------------
            while True:
                new, old = self.manage_carriers(carrier_dic, waiting_room, cursor)

                for i in new:
                    print("NEW agent")
                    env.add_agent(i)

                for i in old:
                    print("DEL agent")
                    env.del_agent(i)

                if len(carrier_dic) > 0:
                    break

                print("Waiting for connection ...")
                time.sleep(1)
                 
            # -------------------------------------------------------------
            # get a[t-1] <-- get action (from agent, via socket)
            # -------------------------------------------------------------

            A = {}
            for c_id, carrier in carrier_dic.items():
                A[c_id] = carrier.get_vector() 

            # -------------------------------------------------------------
            # Environment deals with Creature actions
            # s[t], r[t] ~ p(. , . | s[t-1], a[t-1])
            # o[t] = phi(s[t])
            # -------------------------------------------------------------
            O, R, _ = env.step(A)

            print(O,R,_)

            # -------------------------------------------------------------
            # send o[t], r[t] --> agent
            # -------------------------------------------------------------

            for i, carrier in carrier_dic.items():

                n = len(O[i])
                msg = np.zeros(n+2, dtype=np.float32)
                msg[0:n] = O[i] 
                msg[-2] = R[i]
                msg[-1] = t # _[i]   n.b. I am temporarily commandiering this slot for 't'
                carrier.send_vector(msg) 

            # -------------------------------------------------------------
            # Database update (Calculation Overhead) -- do this occasionally
            # -------------------------------------------------------------

            for cid, r in R.items():
                assert(isinstance(r,numbers.Real))
                if abs(r) > 0:
                    name = carrier_dic[cid]
                    print("[Server] t = %d (updating points, agent '%s' got R+=%3.2f)" % (t,str(carrier_dic[cid].info),r))
                    query = "UPDATE Users SET points = points + ? WHERE Name = ?"
                    cursor.execute(query, (r, carrier_dic[cid].info))
                    query = "INSERT INTO Records (Run, Name, Tick, Reward) VALUES (?, ?, ?, ?)"
                    cursor.execute(query, (server_cfg['run'], carrier_dic[cid].info, t, r))
                    conn.commit()

            # -------------------------------------------------------------
            # Brief pause
            # -------------------------------------------------------------
            print_carriers(carrier_dic)
            time.sleep(1/FPS)
            self.SERVER_RUNNING = True

        conn.close()

    def manage_carriers(self, carrier_dic, waiting_room, cursor):
        '''
            move people in the waiting room to carriers (if status ok)
            clean dead carriers
        '''

        new_carriers = []
        old_carriers = []
        nul_carriers = []

        for c_id, carrier in waiting_room.items():
            print("[Server] Found carrier %d in the Waiting Room ..." % c_id)
            if carrier.status > 0: 
                print("[Server] Let's welcome on board carrier %d (name: %s) ..." % (c_id, carrier.info))
                carrier_dic[c_id] = carrier
                new_carriers.append(c_id)
                query = "INSERT OR IGNORE INTO Users (Name, points) VALUES (?, ?)"
                cursor.execute(query, (carrier.info, 0))
            elif carrier.status == 0:
                # Handshake not completed, keep waiting ...
                print("[Server] New carrier-connection detected (%d), status '%s' but handshake not completed yet (no info), do nothing/keep waiting..." % (c_id,carrier.status))
            else:
                print("[Server] Carrier in waiting room (%d), but status '%s' -- has apparently disconnected...; queue for removal" % (c_id,carrier.status))
                nul_carriers.append(c_id)

        for c_id in nul_carriers:
            del waiting_room[c_id]
        for c_id in new_carriers:
            del waiting_room[c_id]

        for c_id in carrier_dic.keys():

            if carrier_dic[c_id].status == 1:
                # no connection or disconnection, just doing a normal update ..
                pass

            elif carrier_dic[c_id].status < 0:
                # Lifecycle finished, kill the sprite, schedule the carrier for deletion
                print("[Server] Kill carrier.")
                old_carriers.append(c_id)

        for c_id in old_carriers:
            del carrier_dic[c_id]

        return new_carriers, old_carriers

import sys
from datetime import datetime

if __name__ == '__main__':
    timestamp = datetime.now()
    #env = ToyWorld()

    server_cfg = {
        'fps' : 20,
        'run' : timestamp.strftime("%Y-%m-%d %H:%M:%S")
    }
    env_name = sys.argv[1] if len(sys.argv) > 1 else "ToyWorld"  # Default to "ToyWorld" if no argument is provided
    env = globals()[env_name]()
    print("[Server] Starting server for world '%s'" % env_name)
    server = Server(env, server_cfg)


