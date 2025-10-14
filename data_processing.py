# data_processing.py
import json
from utils import make_node, make_edge, coalesce

def load_container_data():
    """Load and return the container data from JSON."""
    with open("data/dd.json", "r") as f:
        return json.load(f)

def process_container_data():
    containers = load_container_data()
    
    parent_nodes = []
    parent_names = []
    child_nodes = []
    child_names = []
    edges = []
    edge_ids = []
    for container in containers:
        name = container.get('name')
        parent_name = container.get('stack')
        connections = container.get('connections')
        listen_ports = container.get('listen_ports')

        if(parent_name):
            parent_node = make_node(id=parent_name, label=parent_name, classes='stacks')
        
        child_node = make_node(id=name, label=name, classes='graph-node docker-container', parent=parent_name if parent_name else None)

        if(parent_name and parent_name not in parent_names):
            parent_names.append(parent_name)
            parent_nodes.append(parent_node)
        
        child_nodes.append(child_node)
        child_names.append(name)

        for connection in connections:
            foreign_device = connection.get('foreign_device')
            local_port = int(connection.get('local_port'))
            edge = None

            # Container to ip address node connection processing
            if(foreign_device is None or foreign_device.endswith(" (Gateway)")):
                foreign_ip = connection.get('foreign_ip')
                if(foreign_ip not in child_names):
                    child_names.append(foreign_ip)
                    child_node = make_node(id=foreign_ip, label=coalesce(foreign_device, foreign_ip), classes='graph-node foreign-ip')
                    child_nodes.append(child_node)
                
                if (local_port in listen_ports):
                    edge = make_edge(id=foreign_ip+name, source=foreign_ip, target=name) # Inbound connection (IP -> Container)
                else:
                    edge = make_edge(id=foreign_ip+name, source=name, target=foreign_ip) # Outbound connection (Container -> IP)
        
            # Container to container connection processing
            else:
                if (local_port in listen_ports):
                    edge = make_edge(id=foreign_device+name, source=foreign_device, target=name) # Inbound connection (Container -> Container)
                else:
                    edge = make_edge(id=name+foreign_device, source=name, target=foreign_device) # Outbound connection (Container -> Container)
            
            # Add the edge to the list of edges if it is not already present
            if edge:
                edge_id = edge.get('data').get('id')
                if edge_id not in edge_ids:
                    edge_ids.append(edge_id)
                    edges.append(edge)
    return child_nodes, parent_nodes, edges, containers, parent_names