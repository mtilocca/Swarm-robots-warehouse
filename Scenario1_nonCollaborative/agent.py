from enum import Enum
from numpy import sqrt

from main import Pathfinder
from AGV import Order, Order_State

class Agent_State(Enum):
    _Done = 0
    _Picking = 1
    _Delivering = 2


'''
The agent layer is one of the two main ones together with the environment. 
a number of Agent objects is created by the environment once it reads the configuration file. 

Based on the information of the input file each agent can be initialized with 

- a unique id 
- a unique position in the map 
'''

class Agent:

    def __init__(self, agentId, map, position):
        self.agentId = agentId
        self.map = map
        self.pickupStation = position
        self.deliveryStation = position
        self.startingPosition = position # Return here after orders are finished
        self.position = position
        self.stepsHistory = []
        self.state = Agent_State._Done
        self.order_switchcount = 0
        self.order_log = []
        self.order = None
        self.goal = position

        self.pathfinder = Pathfinder()

        # temp_dict = {"x": self.position[0], "y": self.position[1], "t": 0}
        # self.stepsHistory.append(temp_dict)

    def getPosition(self):
        return self.position

    def getId(self):
        return self.agentId

    def getOrder(self):
        return self.order

    # Get the state of the Agent
    def getState(self):
        return self.state

    # Get the step history of the Agent
    def getStepsHistory(self):
        return self.stepsHistory

    '''
    Main function responsible for updating the agent state and goal. The function is called by the self.MakesMove function 
    when the agent has reached a goal or when an order is assigned. either collaborative or not. 

    Input: the value of the new state corresponding to the AGENT_STATE 
    '''
    def update_agent_state(self, newState):
        if self.order == None:
            return
        elif newState == 0:# "_Done"
            self.state = Agent_State._Done
            self.goal = self.startingPosition
            #print("self.startingPosition14", self.goal)
        elif newState == 1:# "_Picking"
            self.order_switchcount += 1
            self.order_log.append(self.order.id_code)
            self.state = Agent_State._Picking
            self.goal = self.order.get_objective()
            #print("self.pickupStation24", self.goal)
        elif newState == 2:# "_Delivering"
            self.state = Agent_State._Delivering
            self.goal = self.order.get_objective()
            #print("self.deliveryStation.coordinate34", self.goal)

    '''
    When the agent has reached the pick up point this function has the goal to update the agent state and communicate with the order
    layer the pick up the order by changing the order state  and registering the time-step of pick up 
    '''

    def pick_order(self, timestep):
        self.order.set_order_state(2)
        self.order.timestep_pick = timestep
        self.update_agent_state(2)
        #print("Order ", self.order.id_code , " picked by agent", self.agentId, ". New Goal: ", self.goal)



    '''
    When the agent has reached the Delivery point this function has the goal to update the agent state and communicate with the order
    layer the Delivery the order by changing the order state  and registering the time-step of the Delivery
    '''

    def deliver_order(self, timestep):
        self.order.set_order_state(3)
        self.order.timestep_end = timestep
        self.update_agent_state(0)
        #print("Order ", self.order.id_code , " delivered by agent", self.agentId)

    def setOrder(self, order, timestep, ID):
        self.order = order
        self.pickupStation = order.pickupStation
        self.order.assign_order(self.agentId, timestep, self.position)
        #self.order.set_order_state(1)
        self.update_agent_state(1)


    '''
    Main function called at each time step for every agent in the environment layer.  It links the agent layer to the environment, 
    the order and path finding layer 
    '''
    def makesMove(self, timestep, map):

        if self.state == Agent_State._Done and self.position == self.goal:
            print("DONE HERE",self.state, Agent_State._Done)
            temp_dict = {"x": self.position[0], "y": self.position[1], "t": timestep}
            self.stepsHistory.append(temp_dict)# Save steps for visualization
            return self.position
        elif self.state == Agent_State._Picking and self.position == self.goal:# Picks up good for order
            print("PICKING HERE",self.state, Agent_State._Picking)
            temp_dict = {"x": self.position[0], "y": self.position[1], "t": timestep}
            self.stepsHistory.append(temp_dict)# Save steps for visualization
            self.pick_order(timestep)
            return self.position
        elif self.state == Agent_State._Delivering and self.position == self.goal:# Delivers good
            print("DELIVERING HERE",self.state, Agent_State._Delivering)
            temp_dict = {"x": self.position[0], "y": self.position[1], "t": timestep}
            self.stepsHistory.append(temp_dict)# Save steps for visualization
            self.deliver_order(timestep)
            return self.position

        # Find next step
        #print("self.goal)", self.goal)
        x, y = self.pathfinder.solve(self.agentId ,map.copy(), self.position, self.goal)

        self.position = (x, y)
       

        # Save steps for visualization
        temp_dict = {"x": self.position[0], "y": self.position[1], "t": timestep}
        self.stepsHistory.append(temp_dict)

        #print("End of MakesMove:", self.position)
        return self.position
