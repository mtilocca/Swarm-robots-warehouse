from enum import Enum
from numpy import sqrt
from statistics import mean
import sys

import numpy
import yaml
import random

from agent import Agent, Agent_State
from AGV import Order, Order_State  

'''
Object used to store the information regarding the pick up stations in the initialization of
the environment class from the data in the input file 
'''
class PickupStation():
    def __init__(self, coordinate):
        self.coordinate = coordinate

    def getCoordinate(self):
        return self.coordinate

'''
Object used to store the information regarding the Delivery stations in the initialization of
the environment class from the data in the input file 
'''
class DeliveryStation():
    def __init__(self, coordinate):
        self.coordinate = coordinate

    def getCoordinate(self):
        return self.coordinate


class WareHouse_Env():

    def __init__(self, input_config_file, render=True):
        """
        Creates a grid world of a warehouse, where multiples agents are supposed to collect items from pickup station
        and bring them to the delivery station. The Warehouse contains also obstacles

        :param input_config_file: yaml file that contains the word configuration
        """
        # Load experiment parameters from the input.yaml file
        params = read_config_file(input_config_file)

        # Prepare for save the history to output.yaml file
        self.output = {"schedule": None}

        # Set the world grid
        self.dimensions = params["map"]["dimensions"]
        self.map = numpy.zeros(self.dimensions, dtype=object)

        # Add pickupStation to list deliveryStation to the map
        self.pickupStations = []
        for pickupStation in list(params["map"]["pickupStation"]):
            self.pickupStations.append(PickupStation(coordinate=pickupStation))


      
        self.deliveryStations = []
        for deliveryStation in list(params["map"]["deliveryStation"]):
            self.deliveryStations.append(DeliveryStation(coordinate=deliveryStation))

        # Add obstacles to the map
        self.obstacles = []
        for obs in params["map"]["obstacles"]:
            self.obstacles.append(obs)

        # Create agents
        self.agents = []
        for agentId, d in enumerate(params["agents"]):
            agent = Agent(d["name"], self.map, position=tuple(d["start"]))
            self.agents.append(agent)

        # Create Orders
        self.order_list = []
        for i in range(len(params["order"]["orders_"])):  # Create as many orders as total_orders
            id_code = params["order"]["orders_"][i]["id_code"]
            quantity = params["order"]["orders_"][i]["requested_quantities"]
            timestep_begin = params["order"]["orders_"][i]["timestep"]
            PickUP = params["order"]["orders_"][i]["pickupStation"]
            Delivery = params["order"]["orders_"][i]["deliveryStation"]  
            order = Order(Delivery[0], PickUP[0], quantity, timestep_begin, id_code)
            print("ORDER", order.id_code, order.pickupStation, order.deliveryStation, "quantity:", order.requested_quantities, "time_begin:",
                  order.timestep_begin)
            self.order_list.append(order)
            

        # Check if all agents are done
        self._done = False

        # Render in Terminal option
        self.renderMap(0)

    def step(self, timestep):

        # Assign orders to agents
        '''
         Orders are distributed here. Agent bid with distance to pickup station of order.
         In a bid the agent closest to the order gets the order.
        '''
        for order in self.order_list:
            if order.get_order_state() == 0 and order.getTimestep_begin() <= timestep:
                winner = None
                winnerDistance = None
                for agent in self.agents:
                    if agent.getState() == Agent_State._Done:  # Agent is _Done
                        distance = self.callForProposal(agent, order)
                        if winner == None or distance < winnerDistance:
                            winnerDistance = distance
                            winner = agent
                if winner != None:
                    winner.setOrder(order, timestep, winner.getId())
                    for i in range(len(self.order_list)):
                        if order.getOrderId() == self.order_list[i].id_code:
                            self.order_list[i].agent_assigned = winner.getId()


        # Let agents make their moves
        for agent in self.agents:
            self.map[agent.getPosition()[0], agent.getPosition()[1]] = 0  # Reset position of agent
            agent.makesMove(timestep, self.map)
            self.renderMap(timestep)

        # Print for console
        self.renderMap(timestep, False)

        # Save history
        self.save_stepHistory()

    def callForProposal(self, agent, order):
        """
        Return distance of agent to orders pickupstation
        """
        return sqrt((order.getPickupStation()[0] - agent.getPosition()[0]) ** 2 + (
                    order.getPickupStation()[1] - agent.getPosition()[1]) ** 2)

    # Render stations
    def renderMap(self, timestep, printBool=False):
        """
        Renders the map completely new everytime.
        """

        # Render everything to zero
        self.map = numpy.zeros(self.dimensions, dtype=object)

        # Add obstacles
        for obs in self.obstacles:
            self.map[obs] = "*"

        # Add pickup stations
        for pickupStation in self.pickupStations:
            self.map[pickupStation.getCoordinate()] = "P"

        # Add delivery stations -- follow same logic as for pickup stations 
        
        for deliveryStation in self.deliveryStations:
            self.map[deliveryStation.getCoordinate()] = "D"

        # Add agents
        for agent in self.agents:
            if self.is_in_P_station(agent):
                self.map[agent.getPosition()] = f"P@A{agent.agentId}"
            elif self.is_in_D_station(agent):  # change it ---> how ? 
                self.map[agent.getPosition()] = f"D@A{agent.agentId}"
            else:
                self.map[agent.getPosition()] = f"A{agent.getId()}"

        if printBool:
            print("#################", timestep)
            print(self.map)

    def is_in_P_station(self, agent):
        for pickupStation in self.pickupStations:
            if pickupStation.getCoordinate() == agent.getPosition():
                return True
        return False

    def is_in_D_station(self, agent):
        for deliveryStation in self.deliveryStations:
            if deliveryStation.getCoordinate() == agent.getPosition():
                return True 
        return False

    # similar logic for meeting points 

    def allOrdersDone(self):
        """
        Return true if all orders are delivered
        """
        for order in self.order_list:
            if order.get_order_state() != 3:
                return False
        return True

    def save_stepHistory(self):
        data = {}
        for agent in self.agents:
            data[agent.getId()] = agent.getStepsHistory()
        self.output["schedule"] = data

    # Update env state to done if all agents are _Done and no more orders
    def everythingDone(self):
        """
        End simulation if all orders had been delivered.
        """
        if self.order_list != []:
            return False
        for agent in self.agents:
            # print("agent.state != Agent_State._Done", agent.state, Agent_State._Done, agent.state != Agent_State._Done)
            if agent.state != Agent_State._Done:
                return False
        return True


def read_config_file(config_file):
    with open(config_file, 'r') as input_file:
        try:
            params = yaml.load(input_file, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)
    return params


def write_output_file(output_file, output):
    with open(output_file, 'w') as output_yaml:
        yaml.safe_dump(output, output_yaml)

if __name__ == "__main__":
    input_file ="input.yaml" 
    env = WareHouse_Env(input_config_file=input_file)
    timestep = 0

    agentState =[]
    pairsState = []

    while True:
        env.step(timestep)

        timestep += 1
        
        if timestep > 500 or env.allOrdersDone():  
            print("Done with", timestep, "timesteps.")
            break

    # Print results
    totallist = []
    deliverytimelist = []
    waitingtimelist = []
    t_difflist = []
    losslist = []
    maxdeliverylist = []
    dperformedlist = []
    mindistancelist = []
    performeddistancelist = []
    simulationtimelist = []

    
    for j in range(len(env.order_list)):
        E = env.order_list[j]
        #print("Order;", E.id_code, "; agent", E.agent_assigned, "; agent pos:", E.agent_pos, "; pickup:",
         #     E.pickupStation,  "; delivery:", E.deliveryStation , "; d_required:", round(E.distance, 1), "; t_begin:", E.timestep_begin, "; t_pick:",
         #     E.timestep_pick, "; t_end:", E.timestep_end, "; t_diff:", (E.timestep_pick - E.timestep_begin),
         #     "; d_performed:", (E.timestep_end - E.timestep_pick), "; loss:",
         #     round((E.timestep_end - E.timestep_pick - E.distance), 2))

            # Add delivery station to the metrics 
        print(E.id_code, round((E.timestep_end - E.timestep_pick - E.distance), 2))
        # print("Order", E.id_code, " agent", E.agent_assigned)
        # print("agent pos:", E.agent_pos, "pickup: ", E.pickupStation, "distance: ", round( sqrt((E.agent_pos[0] - E.pickupStation[0])**2 + (E.agent_pos[1] - E.pickupStation[1])**2), 1))
        # print("quantity:", E.requested_quantities, " t_begin:", E.timestep_begin)
        # print("t_begin:", E.timestep_begin, "t_pick:", E.timestep_pick, " t_end: ",  E.timestep_end)
        # print("d_performed:", (E.timestep_end - E.timestep_pick))
        # print("loss: ", round((E.timestep_end - E.timestep_pick - E.distance), 2))
        totallist.append(E.timestep_end - E.timestep_begin)
        waitingtimelist.append(E.timestep_pick - E.timestep_begin)
        deliverytimelist.append(E.timestep_end - E.timestep_pick)
        t_difflist.append(E.timestep_pick - E.timestep_begin) #DISTANCE T_DIFF

        maxdeliverylist.append(E.timestep_end)
        dperformedlist.append((E.timestep_end - E.timestep_pick))

        mindistancelist.append(round(E.distance, 1))
        performeddistancelist.append((E.timestep_end - E.timestep_pick))
        losslist.append(round((E.timestep_end - E.timestep_pick - E.distance), 2))  # losslist
        simulationtimelist.append(E.timestep_end)

    orderchangelist = []
    for agent in env.agents:
        i = 0
        for first, second in zip(agent.order_log, agent.order_log[1 : ] + agent.order_log[ : 1]):
            if (first != second):
                i = i + 1

    
    write_output_file("./output.yaml", env.output)
    print(" avg delivery: " + str(mean(deliverytimelist)) + " avg total: " + str(
        mean(totallist)) + " avg waitinglist: " + str(mean(waitingtimelist)))

    #print(sys.argv[1])

    

    filehandler2 = open('maxdeliverytimeagents.txt', 'a')
    filehandler2.write(str(max(maxdeliverylist)))
    filehandler2.write("\n")
    filehandler2.close()


    filehandler3 = open('averagelosstime.txt', 'a')
    filehandler3.write(str(mean(losslist)))
    filehandler3.write("\n")
    filehandler3.close()

    filehandler4 = open('average_d_performed.txt', 'a')
    filehandler4.write(str(mean(dperformedlist)))
    filehandler4.write("\n")
    filehandler4.close()

    filehandler5 = open('Exp_mapArea_results.txt', 'a')
    #filehandler5.write(sys.argv[1] + '''
    #'''

    #''')
    filehandler5.write("\n\n")
    filehandler5.write("average min distance \n")
    filehandler5.write(str(mean(mindistancelist)))
    filehandler5.write("\n")


    filehandler5.write("average performed distance \n")#
    filehandler5.write(str(mean(performeddistancelist)))
    filehandler5.write("\n")


    filehandler5.write("average loss \n")#
    filehandler5.write(str(mean(losslist)))
    filehandler5.write("\n")


    filehandler5.write("max loss \n")#
    filehandler5.write(str(max(losslist)))
    filehandler5.write("\n")


    filehandler5.write("max simulation time \n")
    filehandler5.write(str(max(simulationtimelist)))
    filehandler5.write("\n")



    filehandler5.close()