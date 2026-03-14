import networkx as nx
import json

class GameState:
    def __init__(self, start_node = 0, money = 0):
        self.node = start_node
        self.strength = 0
        self.knowledge = 0
        self.charme = 0
        self.money = money
        self.graph = built_static_node_graph()

    def determine_event_options(self, node):
        legal_options = []
        if self.graph.nodes[node]["event_id"] != -1:
            event_name = self.graph.nodes[node]["event information"]["name"]
            options = self.graph.nodes[node]["option information"]
            for opt in options:
                if opt["cost"] <= self.money: # cost
                    option_name = opt["text"]
                    legal_options.append((event_name, option_name))
            return legal_options
        else:
            return [("No-event node", "No event options")]
        
    def reachable_within_steps(self, steps):
        lengths = nx.single_source_shortest_path_length(self.graph, self.node)
        possible_nodes = []
        for n, d in lengths.items():
            if 0 < d <= steps:
                possible_nodes.append(n)
        return possible_nodes


            
def built_static_node_graph(
        
):
    """
    
    """
    graph = nx.DiGraph()   
    # Hafenstadt
    graph.add_node(0, event_id=6) # x=4190, y=6050)
    graph.add_node(1, event_id=6) # x=4334, y=6300)
    graph.add_node(2, event_id=6) # x=4560, y=6100)

    # Hafenstadt zu Agons Brücke: rechts nach links
    graph.add_node(3, event_id=-1)
    graph.add_node(4, event_id=-1)
    graph.add_node(5, event_id=-1) 
    graph.add_node(6, event_id=4) # Stop

    graph.add_edges_from([(3, 4), (4, 5), (5, 6)])

    # Agons Brücke zu Racrans Festung
    graph.add_node(7, event_id=-1) # Arrive: Agons Brücke
    graph.add_node(8, event_id=-1)
    graph.add_node(9, event_id=-1)
    graph.add_node(10, event_id=-1) 
    graph.add_node(11, event_id=-1)


    graph.add_edges_from([(7, 8), (8, 9), (9, 10), (10, 11)])

    # Racrans Festung
    graph.add_node(12, event_id=5)
    graph.add_node(13, event_id=5)
    graph.add_node(14, event_id=5) # Arrive: Racrans Festung
    graph.add_node(15, event_id=5)

    graph.add_edges_from([(11, 12), (12, 13), (13, 14), (14, 15)])


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
                graph.nodes[node]["event information"] = {"name": event_name, "description": event_description}
                options = event["options"]
                options_information = []
                for opt in options:
                    text = opt["text"]
                    description = opt["description"]
                    values = opt["values"]
                    cost = opt["cost"]
                    options_information.append({"text": text, "description": description, "values": values, "cost": cost})
                    
                graph.nodes[node]["option information"] = options_information

    return graph

