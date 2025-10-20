# data_processing.py

import json
import logging
from pymongo import MongoClient
#from bson import json_util
from utils import make_node, make_edge, coalesce, anonymize_ip

class DataProcessor:
    def __init__(self, dev_mode=False, mask_ip_labels=True):
        conn_str = "mongodb://localhost:27017/" if dev_mode else "mongodb://docker_dash_mongo:27017/"
        self.client = MongoClient(conn_str)
        self.db = self.client["dashdb"]
        self.collection = self.db["snapshots"]
        self.mask_ip_labels = mask_ip_labels

    def load_container_data_json(self):
        """Load and return the container data from JSON."""
        containers = []
        with open("data/dd.json", "r") as f:
            containers = json.load(f)
        return containers

    def load_container_data_mongo(self, limit=None):
        """Load and return the container data from MongoDB."""
        containers = {}
        processes = {}

        # Get documents from MongoDB sort by most recent
        # Each document is a "snapshot" of the discovery script output at the time the script was ran, so we want most recent data first
        
        docs = []
        if limit: 
            docs = list(self.collection.find().sort("snapshot_time", -1).limit(limit))
        else:
            docs = list(self.collection.find().sort("snapshot_time", -1))
        
        logging.info("Mongo Documents Found: " + str(len(docs)))
        for doc in docs:
            procs = doc['host'].get("processes", {})
            for k, v in procs.items():
                if k not in processes:
                    processes[k] = v
                else:
                    processes[k]["connections"].extend(v.get("connections", []))


            logging.info(f"Mongo Document ID: {doc['_id']}, Snapshot Time: {doc['snapshot_time']}")
            devices = doc['host']['devices']
            for dev in devices:
                # id = dev['id'] # Use container ID as our identifier (old)
                id = dev['name'] # Use container Name (new) 
                if id not in containers:
                    containers[id] = dev
                else:
                    # Merge connections and ports
                    containers[id]["connections"].extend(dev.get("connections", []))
                    containers[id]["listen_ports"].extend(dev.get("listen_ports", []))
        
        for c in containers.values():
            c["connections"] = [dict(t) for t in {tuple(sorted(d.items())) for d in c["connections"]}]
            c["listen_ports"] = list(set(c["listen_ports"]))

        #print(json.dumps(containers.values(), indent=2, default=json_util.default))
        return list(containers.values()), processes

    def process_container_data(self, limit=None):
        # containers = self.load_container_data_json()
        containers, processes = self.load_container_data_mongo(limit=limit)

        parent_nodes = []
        parent_names = []
        child_nodes = []
        child_names = []
        edges = []
        edge_ids = []
  
        # Process Processes
        for k, v in processes.items():
            node_a = make_node(id=f"p__{k}", label=k, classes='graph-node process')
            
            for c in v.get("connections", []):
                foreign_device = c.get("foreign_device", None)
                foreign_ip = c.get("foreign_ip")
                local_ip = c.get("local_ip")
                
                key = None
                if foreign_device and int(local_ip[-1]) == 1:
                    key = local_ip
                elif foreign_device and int(foreign_ip[-1]) == 1:
                    key = foreign_ip 
               
                if not key:
                    continue
                
                node_b = make_node(id=f"i__{key}", label=foreign_device, classes='graph-node docker-gateway-ip')
                
                if c.get("local_port") in v.get("listen_ports", []):
                    edge = make_edge(id=key+k, source=f"{node_b['data']['id']}", target=f"{node_a['data']['id']}")
                    
                    if edge['data']['id'] not in edge_ids:
                        
                        # Only bother adding any nodes that have an edge
                        if key not in child_names:
                            child_nodes.append(node_a)
                            child_names.append(key)
                        if k not in child_names:
                            child_nodes.append(node_b)
                            child_names.append(key)
                        
                        edges.append(edge)
                        edge_ids.append(edge['data']['id'])
        
        # Process Containers
        for container in containers:
            name = container.get('name')
            parent_name = container.get('stack')
            connections = container.get('connections')
            listen_ports = container.get('listen_ports')

            if(parent_name):
                parent_node = make_node(id=f"s__{parent_name}", label=parent_name, classes='stacks')
            
            child_node = make_node(id=f"c__{name}", label=name, classes='graph-node docker-container', parent=f"s__{parent_name}" if parent_name else None)

            if(parent_name and parent_name not in parent_names):
                parent_names.append(parent_name)
                parent_nodes.append(parent_node)
            
            child_nodes.append(child_node)
            child_names.append(name)

            for connection in connections:
                foreign_device = connection.get('foreign_device')
                local_port = int(connection.get('local_port'))
                edge = None

                is_gateway = True if foreign_device and foreign_device.endswith(" (Gateway)") else False
                node_class = "docker-gateway-ip" if is_gateway else "foreign-ip"
                # Container to ip connection processing
                if(not foreign_device or is_gateway):
                    foreign_ip = connection.get('foreign_ip')
                    if(foreign_ip not in child_names):
                        child_names.append(foreign_ip)
                        child_node = make_node(id=f"i__{foreign_ip}", label=coalesce(foreign_device, anonymize_ip(foreign_ip) if self.mask_ip_labels else foreign_ip), classes=f"graph-node {node_class}")
                        child_nodes.append(child_node)
                    
                    if (local_port in listen_ports):
                        edge = make_edge(id=foreign_ip+name, source=f"i__{foreign_ip}", target=f"c__{name}") # Inbound connection (IP -> Container)
                    else:
                        edge = make_edge(id=foreign_ip+name, source=f"c__{name}", target=f"i__{foreign_ip}") # Outbound connection (Container -> IP)
            
                # Container to container connection processing
                else:
                    if (local_port in listen_ports):
                        edge = make_edge(id=foreign_device+name, source=f"c__{foreign_device}", target=f"c__{name}") # Inbound connection (Container -> Container)
                    else:
                        edge = make_edge(id=name+foreign_device, source=f"c__{name}", target=f"c__{foreign_device}") # Outbound connection (Container -> Container)
                
                # Add the edge to the list of edges if it is not already present
                if edge:
                    edge_id = edge.get('data').get('id')
                    if edge_id not in edge_ids:
                        edge_ids.append(edge_id)
                        edges.append(edge)
        # parent_names.append('EXTERNAL')
        # parent_nodes.append(make_node(id='__EXTERNAL__', label='EXTERNAL', classes='stacks'))
        return child_nodes, parent_nodes, edges, containers, parent_names
