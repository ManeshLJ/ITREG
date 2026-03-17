import networkx as nx
import json
from dataclasses import dataclass
from typing import Dict
import random
import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np

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
        self.legal_actions = []


    def prepare_move(self):
        """
        Rolls dice for steps and money and updates the legal actions that can we taken.
        """
        # Rolling Dice
        additional_money = random.randint(1, 6) 
        self.money = self.money + additional_money
        number_of_available_steps = random.randint(1, 6) 

        # Determine legal moves
        reachable_nodes = self.reachable_within_steps(number_of_available_steps)
        legal_actions = []
        if len(reachable_nodes) > 0:
            for node in reachable_nodes:
                event_options = self.determine_event_options(node)
                for event_option in event_options:
                    legal_actions.append((node, event_option))
            self.legal_actions = legal_actions
            
        else:
            node = self.node
            event_options = self.determine_event_options(node)
            for event_option in event_options:
                legal_actions.append((node, event_option))
            self.legal_actions = legal_actions

        for idx, action in enumerate(self.legal_actions):
            print(f"{idx}: {action}")

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
            if d <= steps:
                possible_nodes.append(n)
        return possible_nodes
    
    def take_action(self, legal_action_idx):
        # TODO include trading values (2 strength for 1 charme)

        # Assign local vars
        action = self.legal_actions[legal_action_idx]
        event_node = action[0]
        event_name = action[1]["event name"]
        option_text = action[1]["option text"]

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
        
    def print_current_game_state(self):

        G = self.graph

        xs = [G.nodes[n]["x"] for n in G.nodes]
        ys = [G.nodes[n]["y"] for n in G.nodes]

        # Create two side-by-side plots
        fig, (ax1, ax2) = plt.subplots(
            1, 2,
            figsize=(12, 10),
            gridspec_kw={"width_ratios": [4, 1]}
        )


        # --- LEFT: node scatter plot ---
        ax1.scatter(xs, ys, s=175)
        ax1.set_xlim(0, 4959)
        ax1.set_ylim(0, 7016)
        ax1.set_aspect('equal', adjustable='box')
        ax1.invert_yaxis()
        ax1.set_xticks([])
        ax1.set_yticks([])

        # --- Draw directed edges ---
        for u, v in G.edges:
            x1, y1 = G.nodes[u]["x"], G.nodes[u]["y"]
            x2, y2 = G.nodes[v]["x"], G.nodes[v]["y"]

            ax1.annotate(
                "", 
                xy=(x2, y2), 
                xytext=(x1, y1),
                arrowprops=dict(
                    arrowstyle="->",
                    color="gray",
                    lw=1.5,
                    shrinkA=5,
                    shrinkB=5
                ),
                zorder=1
            )

        # --- GROUP NODES BY event_id ---
        groups = defaultdict(list)
        for n in G.nodes:
            eid = G.nodes[n].get("event_id", -1)
            if eid != -1:
                groups[eid].append(n)

        # --- DRAW BLUE BUBBLES + LABELS ---
        for eid, nodes in groups.items():
            xs_group = [G.nodes[n]["x"] for n in nodes]
            ys_group = [G.nodes[n]["y"] for n in nodes]

            # center of the bubble
            cx = np.mean(xs_group)
            cy = np.mean(ys_group)

            # radius based on max distance from center
            dists = [
                np.sqrt((G.nodes[n]["x"] - cx)**2 + (G.nodes[n]["y"] - cy)**2)
                for n in nodes
            ]
            r = max(dists) + 150   # padding

            # draw bubble
            bubble = plt.Circle(
                (cx, cy),
                r,
                color="blue",
                alpha=0.15,
                zorder=0
            )
            ax1.add_patch(bubble)

            # draw event_id label inside bubble
            ax1.text(
                cx, cy -200,
                f"{eid}",
                ha="center",
                va="top",
                fontsize=16,
                color="blue",
                alpha=0.8,
                zorder=1
            )

        # --- Node labels ---
        for n in G.nodes:
            x = G.nodes[n]["x"]
            y = G.nodes[n]["y"]
            ax1.text(x, y, str(n), fontsize=10, ha="center", va="center", zorder=3)

        # --- Highlight current node ---
        target = self.node
        tx = G.nodes[target]["x"]
        ty = G.nodes[target]["y"]

        ax1.scatter([tx], [ty], s=400, color="red", edgecolors="black", zorder=4)
        ax1.text(tx, ty, str(target), ha="center", va="center",
                fontsize=12, color="white", zorder=5)

        # --- RIGHT: panel with 4 integers ---
        values = (
            f"Strength: {self.strength}",
            f"Knowledge: {self.knowledge}",
            f"Charme: {self.charme}",
            f"Aramik: {self.money}"
        )

        ax2.set_xticks([])
        ax2.set_yticks([])
        ax2.set_frame_on(False)

        # Right-aligned text block
        text = "\n".join(values)
        ax2.text(0.95, 0.5, text, ha="right", va="center", fontsize=24)

        # Round number
        ax2.text(0.95, 0.65, f"Round {self.round_number}",
                ha="right", va="center", fontsize=24)

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
    graph.add_node(7, event_id=4, x=2690, y=6240) # Arrive: Agons Brücke
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

    # Hafenstadt Südestern zu Fährhafen/Zhranorath
    graph.add_node(16, event_id=-1, x=4070, y=5800)
    graph.add_node(17, event_id=2, x=4190, y=5460) # Arrive: Fährhafen
    graph.add_node(18, event_id=-1, x=3790, y=5660)
    graph.add_node(19, event_id=-1, x=3540, y=5470)
    graph.add_node(20, event_id=13, x=3380, y=5260)
    graph.add_node(21, event_id=-1, x=3230, y=4970)

    graph.add_edges_from([(16, 17), (16, 18), (18, 19), (19, 20)])

    # Zhranorath
    graph.add_node(22, event_id=10, x=2060, y=4780)
    graph.add_node(23, event_id=10, x=2370, y=4740) # Arrive: West-Zhranorath
    graph.add_node(24, event_id=-1, x=2700, y=4720)
    graph.add_node(25, event_id=11, x=3060, y=4720)
    graph.add_node(26, event_id=11, x=3440, y=4670) # Arrive Ost-Zhranorath

    graph.add_edges_from([(21, 25), (22, 23), (23, 24), (24, 25), (25, 26)])

    # Zhranorath zu Zwillingsbrücken
    graph.add_node(27, event_id=-1, x=3780, y=4670)
    graph.add_node(28, event_id=-1, x=4070, y=4640) # Arrive: Zwillingsbrücken

    graph.add_edges_from([(26, 27), (27, 28)])

    # Racrans Festung zu Razerath und Ligon Wald und Zhranorath
    graph.add_node(29, event_id=-1, x=750, y=5232)
    graph.add_node(30, event_id=-1, x=700, y=5000)
    graph.add_node(31, event_id=3, x=690, y=4700) # Arrive: Razerath
    graph.add_node(32, event_id=-1, x=960, y=5130)
    graph.add_node(33, event_id=1, x=1310, y=4900) # Arrive: Ligon
    graph.add_node(34, event_id=-1, x=1680, y=4850)

    graph.add_edges_from([(34, 22), (15, 29), (29, 30), (30, 31), (29, 32), (32, 33)])

    # Zwillingsbrücken zu Tempel der Erleuchtung und Lilouth
    graph.add_node(35, event_id=-1, x=4230, y=4350)
    graph.add_node(37, event_id=-1, x=4090, y=4090)
    graph.add_node(38, event_id=-1, x=3930, y=3870) # Arrive: Lettas Einkehr
    graph.add_node(39, event_id=-1, x=3680, y=3710)
    graph.add_node(40, event_id=14, x=3370, y=3630) # Arrive: Lilouth
    graph.add_node(41, event_id=-1, x=3600, y=3500) 
    graph.add_node(42, event_id=-1, x=4350, y=4100)
    graph.add_node(43, event_id=7, x=4590, y=3980) # Arrive: Tempel der Erleuchtung

    graph.add_edges_from([(28, 35), (35, 37), (35, 42), (37, 38), (38, 39), (39, 40), (39, 41), (42, 43)])

    # Lilouth zu Herrenhaus
    graph.add_node(44, event_id=-1, x=3420, y=3300)
    graph.add_node(45, event_id=-1, x=3170, y=3140)
    graph.add_node(46, event_id=8, x=2890, y=3100)
    graph.add_node(47, event_id=8, x=2590, y=3050) # Arrive: Herrenhaus

    graph.add_edges_from([(41, 44), (44, 45), (45, 46), (46, 47)])

    # Herenhaus zu Binouth 
    graph.add_node(48, event_id=-1, x=2320, y=3190)
    graph.add_node(49, event_id=-1, x=2080, y=3330)
    graph.add_node(53, event_id=16, x=1760, y=3450)
    graph.add_node(54, event_id=16, x=1470, y=3390) # Arrive: Binouth

    graph.add_edges_from([(47, 48), (48, 49), (49, 53), (53, 54)])

    # Binouth nach Azelon
    graph.add_node(55, event_id=-1, x=1200, y=3200)

    graph.add_edges_from([(54, 55)])


    # after success we go to virutal field 1000

    # Add event and option information
    with open("cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    for node in graph.nodes:
        print(node)
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
                    logger.info(f"{opt}")
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

