import networkx as nx
import json
from dataclasses import dataclass
from typing import Dict
import random
import matplotlib.pyplot as plt

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


@dataclass
class Action:
    new_node: int
    event_name_and_option_text: Dict[str, str]

class GameState:
    def __init__(self, start_node = 0, strength = 0, knowledge = 0, charme = 0, money = 0):
        self.node = start_node
        self.strength = strength
        self.knowledge = knowledge
        self.charme = charme
        self.money = money
        self.graph = built_static_node_graph()
        self.round_number = 0

    def determine_event_options(self, node):
        """
        Returns a List of Dicts of the form {event name, option name}
        """
        legal_options = []
        if self.graph.nodes[node]["event_id"] != -1:
            event_name = self.graph.nodes[node]["event information"]["name"]
            options = self.graph.nodes[node]["option information"]
            for opt in options:
                if opt["cost"] <= self.money: # cost
                    option_text = opt["text"]
                    legal_options.append({"event name": event_name, "option text": option_text})
            return legal_options
        else:
            return [{"event name": "No-event node", "option text": "No event options"}]
        
    def reachable_within_steps(self, steps):
        """
        Returns list of node int ids that can be reached from current gamestate.node with certain number of steps.
        """
        lengths = nx.single_source_shortest_path_length(self.graph, self.node)
        possible_nodes = []
        for n, d in lengths.items():
            if 0 < d <= steps:
                possible_nodes.append(n)
        return possible_nodes
    
    def take_action(self, action:Action):
        # TODO include trading values (2 strength for 1 charme)

        # Assign local vars
        event_node = action.new_node
        event_name = action.event_name_and_option_text["event name"]
        option_text = action.event_name_and_option_text["option text"]

        # Check validity of action 
        if self.graph.nodes[event_node]["event information"]["name"] != event_name:
            logger.error(f"Action event name {event_name} does not match event defined at node.")
            return -1
        
        options = self.graph.nodes[event_node]["option information"] 
        we_have_an_issue = True
        for opt_idx_enum, opt in enumerate(options):
            if opt["text"] == option_text:
                we_have_an_issue = False
                opt_idx = opt_idx_enum

        if we_have_an_issue:
            logger.error(f"Action option text {option_text} does not match event defined at node.")
            return -1
        
        required_money = self.graph.nodes[event_node]["option information"][opt_idx]["cost"]
        if required_money > self.money:
            logger.error(f"Insufficient money available: {self.money}. Cost should we checked in determine_event_options. issue")
            return -1

        # Acquire option reqs
        reqs = (self.graph.nodes[event_node]["option information"][opt_idx]["values"][0], self.graph.nodes[event_node]["option information"][opt_idx]["values"][1], self.graph.nodes[event_node]["option information"][opt_idx]["values"][2]) # strength, knowledge, charme

        # Dice roll
        amount_of_dice_rolls = self.graph.nodes[event_node]["event information"]["area"]
        dice_results = []
        for _ in range(amount_of_dice_rolls):
            dice_results.append(random.randint(1, 6))
        additional_power = max(dice_results)
        logger.info(f"Additional power: {additional_power}")

        # Compare reqs with character power + roll
        character_powers = (self.strength, self.knowledge, self.charme)
        total_deficit = 0
        for character_power, req in zip(character_powers, reqs):
            diff = req - character_power
            if diff > 0:
                total_deficit = total_deficit + diff

        if additional_power >= total_deficit:
            outcome = "positive"
            logger.info(f"{event_name}: {option_text}: Positive")
        else:
            outcome = "negative"
            logger.info(f"{event_name}: {option_text}: Negative, total total_deficit: {total_deficit}")

        # Make pos/neg changes
        self.node = self.graph.nodes[event_node]["option information"][opt_idx][outcome]["new node"]
        self.strength = self.strength + self.graph.nodes[event_node]["option information"][opt_idx][outcome]["changes"][0]
        self.knowledge = self.knowledge + self.graph.nodes[event_node]["option information"][opt_idx][outcome]["changes"][1]
        self.charme = self.charme + self.graph.nodes[event_node]["option information"][opt_idx][outcome]["changes"][2]
        self.money = self.money + self.graph.nodes[event_node]["option information"][opt_idx][outcome]["moneyChange"]

        self.round_number = self.round_number +1
        return self
    

    def print_current_game_state(self):

        G = self.graph

        xs = [G.nodes[n]["x"] for n in G.nodes]
        ys = [G.nodes[n]["y"] for n in G.nodes]

        # Create two side-by-side plots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 10))

        # --- LEFT: node scatter plot ---
        ax1.scatter(xs, ys, s=175)
        ax1.set_xlim(0, 4959)
        ax1.set_ylim(0, 7016)
        ax1.set_aspect('equal', adjustable='box')
        ax1.invert_yaxis()
        ax1.set_xticks([])
        ax1.set_yticks([])

        # labels
        for n in G.nodes:
            x = G.nodes[n]["x"]
            y = G.nodes[n]["y"]
            ax1.text(x, y, str(n), fontsize=10, ha="center", va="center")

        # highlight one node
        target = self.node
        tx = G.nodes[target]["x"]
        ty = G.nodes[target]["y"]

        ax1.scatter([tx], [ty], s=400, color="red", edgecolors="black", zorder=3)
        ax1.text(tx, ty, str(target), ha="center", va="center",
                fontsize=12, color="white", zorder=4)

        # --- RIGHT: panel with 4 integers ---
        values = (f"Strength: {self.strength}", f"Knowledge: {self.knowledge}", f"Charme:{self.charme}", f"Aramik:{self.money}")  

        ax2.set_xticks([])
        ax2.set_yticks([])
        ax2.set_frame_on(False)
        
        text = "\n".join(str(v) for v in values)
        ax2.text(0.5, 0.5, text, ha="right", va="center", fontsize=24)

        ax2.text(0.5, 0.65, f"Round {self.round_number}", ha="right", va="center", fontsize=24)

        plt.tight_layout()
        plt.show()




        


            
def built_static_node_graph(
        
):
    """
    
    """
    graph = nx.DiGraph()   
    # Hafenstadt
    graph.add_node(0, event_id=6, x=4190, y=6050)
    graph.add_node(1, event_id=6, x=4334, y=6300)
    graph.add_node(2, event_id=6, x=4560, y=6100)

    # Hafenstadt zu Agons Brücke: rechts nach links
    graph.add_node(3, event_id=-1, x=3939, y=6190)
    graph.add_node(4, event_id=-1, x=3630, y=6180)
    graph.add_node(5, event_id=-1, x=3300, y=6180) 
    graph.add_node(6, event_id=4, x=2985, y=6180) # Stop

    graph.add_edges_from([(3, 4), (4, 5), (5, 6)])

    # Agons Brücke zu Racrans Festung
    graph.add_node(7, event_id=-1, x=2690, y=6240) # Arrive: Agons Brücke
    graph.add_node(8, event_id=-1, x=2370, y=6200)
    graph.add_node(9, event_id=-1, x=2100, y=6130)
    graph.add_node(10, event_id=-1, x=1820, y=6080) 
    graph.add_node(11, event_id=-1, x=1560, y=6000)


    graph.add_edges_from([(7, 8), (8, 9), (9, 10), (10, 11)])

    # Racrans Festung
    graph.add_node(12, event_id=5, x=1300, y=5930)
    graph.add_node(13, event_id=5, x=1020, y=5870)
    graph.add_node(14, event_id=5, x=760, y=5830) # Arrive: Racrans Festung
    graph.add_node(15, event_id=5, x=671, y=5590)

    graph.add_edges_from([(11, 12), (12, 13), (13, 14), (14, 15)])

    graph.add_node(16, event_id=-1, x=4070, y=5800)

    # after success we go to virutal field 1000

    # Add event and option information
    with open("cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    for node in graph.nodes:
        event_id = graph.nodes[node]["event_id"]
        if event_id != -1:
                for obj in data:
                    if obj["id"] == event_id:
                        event = obj
                        break
                event_name = event["title"]
                event_description = event["description"]
                event_area = event["area"]
                graph.nodes[node]["event information"] = {"name": event_name, "description": event_description, "area": event_area}
                options = event["options"]
                options_information = []
                for opt in options:
                    text = opt["text"]
                    description = opt["description"]
                    values = opt["values"]
                    cost = opt["cost"]
                    positive = {"result": opt["positive"]["result"], "description": opt["positive"]["description"], "changes": opt["positive"]["changes"], "moneyChange": opt["positive"]["moneyChange"], "new node": opt["positive"]["new_node"]}
                    try:
                        negative = {"result": opt["negative"]["result"], "description": opt["negative"]["description"], "changes": opt["negative"]["changes"], "moneyChange": opt["negative"]["moneyChange"], "new node": opt["negative"]["new_node"]}
                    except:
                        logger.error(f"{event_name}")
                    options_information.append({"text": text, "description": description, "values": values, "cost": cost, "positive": positive, "negative": negative})
                    
                graph.nodes[node]["option information"] = options_information

    return graph

