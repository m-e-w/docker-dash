"""
data_processing.py

This module defines the DataProcessor class, which handles loading, processing,
and transforming container and process data for visualization in Docker Dash.

Notes:
- All nodes and edges returned are compatible with Dash Cytoscape.
- Node IDs are prefixed to distinguish types:
    - 'c__' for containers, 'p__' for processes, 'i__' for IPs, 's__' for stacks.
- This module is independent of the Dash layout; it only prepares data for visualization.
"""

import json
import logging
from pymongo import MongoClient
from utils import make_node, make_edge, coalesce, anonymize_ip


class DataProcessor:
    def __init__(self, dev_mode=False, mask_ip_labels=True):
        conn_str = (
            "mongodb://localhost:27017/"
            if dev_mode
            else "mongodb://docker_dash_mongo:27017/"
        )
        self.client = MongoClient(conn_str)
        self.db = self.client["dashdb"]
        self.collection = self.db["snapshots"]
        self.mask_ip_labels = mask_ip_labels

    def is_gateway(self, name):
        """Check to see if a foreign_device name is a gateway"""
        return True if name and name.endswith(" (Gateway)") else False

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
            procs = doc["host"].get("processes", {})
            for k, v in procs.items():
                if k not in processes:
                    processes[k] = v
                else:
                    processes[k]["connections"].extend(v.get("connections", []))

            logging.info(
                f"Mongo Document ID: {doc['_id']}, Snapshot Time: {doc['snapshot_time']}"
            )
            devices = doc["host"]["devices"]
            for dev in devices:
                # id = dev['id'] # Use container ID as our identifier (old)
                id = dev["name"]  # Use container Name (new)
                if id not in containers:
                    containers[id] = dev
                else:
                    # Merge connections and ports
                    containers[id]["connections"].extend(dev.get("connections", []))
                    containers[id]["listen_ports"].extend(dev.get("listen_ports", []))

        for c in containers.values():
            c["connections"] = [
                dict(t) for t in {tuple(sorted(d.items())) for d in c["connections"]}
            ]
            c["listen_ports"] = list(set(c["listen_ports"]))

        # print(json.dumps(containers.values(), indent=2, default=json_util.default))
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

            # Node A will always be a process
            node_a = make_node(id=f"p__{k}", label=k, classes="graph-node process")

            for c in v.get("connections", []):
                foreign_device = c.get("foreign_device", None)
                foreign_ip = c.get("foreign_ip")
                local_ip = c.get("local_ip")

            # Node B may reflect a docker container, gateway ip, or foreignip
                id = ""
                classes_string = "graph-node "
                label = ""

                # If we have a value for foreign_device it is either a container or docker gateway
                if foreign_device:
                    label = foreign_device
                    key = None

                    # We do a check to see which IP is the one that actually corresponds with the gateway
                    if int(local_ip[-1]) == 1:
                        key = local_ip
                    elif int(foreign_ip[-1]) == 1:
                        key = foreign_ip
                    
                    # Check if it the device is a gateway or not
                    if self.is_gateway(foreign_device):
                        classes_string+="docker-gateway-ip"
                        id=f"i__{key}"
                    # If its not a gateway then it must be a container since we have any value at all for foreign_device
                    else:
                        classes_string+="docker-container"
                        id=f"c__{foreign_device}"
                        key = foreign_device
                # If we are here it means process is talking to a foreign ip and not a docker gateway ip or container
                # For now just take foreign ip but we could ingest local ip as well possibly
                else:
                    id=f"i__{foreign_ip}"
                    classes_string+="foreign-ip"
                    label = foreign_ip
                    key = foreign_ip

                node_b = make_node(
                    id=id,
                    label=label,
                    classes=classes_string,
                )

                # Determine edge direction
                if c.get("local_port") in v.get("listen_ports", []):
                    # inbound
                    source_node = node_b
                    target_node = node_a
                    edge_id = key + target_node['data']['label']
                else:
                    # outbound
                    source_node = node_a
                    target_node = node_b
                    edge_id = source_node['data']['label'] + key
                if edge_id not in edge_ids:
                    edge = make_edge(
                        id=edge_id,
                        source=source_node["data"]["id"],
                        target=target_node["data"]["id"],
                    )

                # Add nodes if they haven't been added yet
                for node_key, node in [(k, node_a), (key, node_b)]:
                    if node_key not in child_names:
                        child_nodes.append(node)
                        child_names.append(node_key)

                # Append edge
                edges.append(edge)
                edge_ids.append(edge_id)

        # Process Containers
        for container in containers:
            name = container.get("name")
            parent_name = container.get("stack")
            connections = container.get("connections")
            listen_ports = container.get("listen_ports")

            if parent_name:
                parent_node = make_node(
                    id=f"s__{parent_name}", label=parent_name, classes="stacks"
                )

            child_node = make_node(
                id=f"c__{name}",
                label=name,
                classes="graph-node docker-container",
                parent=f"s__{parent_name}" if parent_name else None,
            )

            if parent_name and parent_name not in parent_names:
                parent_names.append(parent_name)
                parent_nodes.append(parent_node)

            child_nodes.append(child_node)
            child_names.append(name)

            for connection in connections:
                foreign_device = connection.get("foreign_device")
                local_port = int(connection.get("local_port"))
                edge = None

                is_gateway = self.is_gateway(foreign_device)
                node_class = "docker-gateway-ip" if is_gateway else "foreign-ip"
                # Container to ip connection processing
                if not foreign_device or is_gateway:
                    foreign_ip = connection.get("foreign_ip")
                    if foreign_ip not in child_names:
                        child_names.append(foreign_ip)
                        child_node = make_node(
                            id=f"i__{foreign_ip}",
                            label=coalesce(
                                foreign_device,
                                (
                                    anonymize_ip(foreign_ip)
                                    if self.mask_ip_labels
                                    else foreign_ip
                                ),
                            ),
                            classes=f"graph-node {node_class}",
                        )
                        child_nodes.append(child_node)

                    if local_port in listen_ports:
                        edge = make_edge(
                            id=foreign_ip + name,
                            source=f"i__{foreign_ip}",
                            target=f"c__{name}",
                        )  # Inbound connection (IP -> Container)
                    else:
                        edge = make_edge(
                            id=foreign_ip + name,
                            source=f"c__{name}",
                            target=f"i__{foreign_ip}",
                        )  # Outbound connection (Container -> IP)

                # Container to container connection processing
                else:
                    if local_port in listen_ports:
                        edge = make_edge(
                            id=foreign_device + name,
                            source=f"c__{foreign_device}",
                            target=f"c__{name}",
                        )  # Inbound connection (Container -> Container)
                    else:
                        edge = make_edge(
                            id=name + foreign_device,
                            source=f"c__{name}",
                            target=f"c__{foreign_device}",
                        )  # Outbound connection (Container -> Container)

                # Add the edge to the list of edges if it is not already present
                if edge:
                    edge_id = edge.get("data").get("id")
                    if edge_id not in edge_ids:
                        edge_ids.append(edge_id)
                        edges.append(edge)
        # parent_names.append('EXTERNAL')
        # parent_nodes.append(make_node(id='__EXTERNAL__', label='EXTERNAL', classes='stacks'))
        return child_nodes, parent_nodes, edges, containers, parent_names
