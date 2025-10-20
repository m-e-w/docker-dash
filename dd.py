"""
dd.py

Docker Dash discovery script.

This script gathers container and host process data for visualization in Docker Dash.
It can output data either to stdout as JSON or insert it into a MongoDB collection.

Notes:
- Connections are filtered to exclude local-only traffic (e.g., 127.0.0.1 or "::").
- Each device dictionary contains all metadata and a list of its connections.
- Designed to be run as a standalone script to generate snapshots for Docker Dash.
- Command-line argument "mongo" switches output from stdout to MongoDB insertion.
"""

import docker
import json
import sys
import subprocess
import re
from datetime import datetime, timezone

mongo = False
if len(sys.argv) > 1 and sys.argv[1] == "mongo":
    mongo = True


# Get Host Process Data using ss command
def get_processes():
    ss_cmd = ["sudo", "ss", "-tanp", "state", "established"]
    re_proc_pid_pat = r'\("([^"]+)",pid=(\d+),fd=\d+\)'

    ss_cmd_output = subprocess.check_output(ss_cmd)

    process_set = {}
    ss_split_lines = str(ss_cmd_output).split("\\n")
    for line in ss_split_lines[1:]:
        split_line = line.split()

        if len(split_line) <= 1:
            continue

        local_address = split_line[2]
        foreign_address = split_line[3]

        local_address_split = local_address.split(":")
        foreign_address_split = foreign_address.split(":")

        local_ip = local_address_split[0]
        foreign_ip = foreign_address_split[0]

        local_port = int(local_address_split[1])
        foreign_port = int(foreign_address_split[1])

        connection = {
            "proto": "tcp",
            "local_address": local_address,
            "local_ip": local_ip,
            "local_port": local_port,
            "foreign_address": foreign_address,
            "foreign_ip": foreign_ip,
            "foreign_port": foreign_port,
            "foreign_device": None,
        }

        # Search process info across the full line to avoid wrong index
        matches = re.findall(re_proc_pid_pat, line)
        for proc, pid in matches:
            name = proc

            if name not in process_set:
                process_set[name] = {
                    "listen_ports": [],
                    "connections": [],
                    "_seen_conns": set(),
                }

            key = f"{connection['local_address']}-{connection['foreign_address']}"

            if key not in process_set[name]["_seen_conns"]:
                process_set[name]["_seen_conns"].add(key)
                process_set[name]["connections"].append(connection)

            if (
                local_port not in process_set[name]["listen_ports"]
                and local_port < 32768
            ):  # if its listening in the high ephemeral port range it probably is TCP response traffic
                process_set[name]["listen_ports"].append(local_port)

    # Clean output
    for proc in process_set.values():
        proc.pop("_seen_conns", None)

    return process_set


# Get docker container data using docker client / netstat
def get_containers():
    NETSTAT_STATES = [
        "CLOSE_WAIT",
        "CLOSED",
        "ESTABLISHED",
        "FIN_WAIT_1",
        "FIN_WAIT_2",
        "LAST_ACK",
        "LISTEN",
        "SYN_RECEIVED",
        "SYN_SEND",
        "TIME_WAIT",
    ]

    client = docker.from_env()
    info = client.info()
    containers = client.containers.list()
    networks = client.networks.list()
    client.close()

    host = {
        "name": info["Name"],
        "os": info["OperatingSystem"],
        "cpu": info["NCPU"],
        "ram": round(info["MemTotal"] / 1024 / 1024 / 1024, 2),
    }

    network_name_set = {}
    for network in networks:
        network_config = network.attrs.get("IPAM").get("Config")
        if network_config:
            gateway = network_config[0].get("Gateway")
            if gateway:
                name = network.name
                network_name_set[gateway] = name + " (Gateway)"

    ip_device_set = {}
    devices = []
    for container in containers:
        name = container.name
        id = container.short_id
        image = container.attrs.get("Config").get("Image")
        pid = container.attrs.get("State").get("Pid")
        stack = (
            container.attrs.get("Config")
            .get("Labels")
            .get("com.docker.compose.project")
        )
        ip_addresses = []
        connections = []
        listen_ports = []

        network_settings = container.attrs.get("NetworkSettings")
        ports = network_settings.get("Ports").keys()
        for port in ports:
            listen_port = int(port[:-4])
            listen_ports.append(listen_port)

        networks = network_settings.get("Networks").values()
        for network in networks:
            ip_address = network["IPAddress"]
            ip_device_set[ip_address] = container.name
            ip_addresses.append(ip_address)

        nsenter_netstat_cmd = [
            "sudo",
            "nsenter",
            "-t",
            str(pid),
            "-n",
            "netstat",
            "-anp",
        ]
        # print(" ".join(nsenter_netstat_cmd)) # Print line for writing the raw command out
        nsenter_netstat_cmd_output = subprocess.check_output(nsenter_netstat_cmd)
        netstat_split_lines = str(nsenter_netstat_cmd_output).split("\\n")
        for line in netstat_split_lines:
            if line.find("tcp") != -1 or line.find("udp") != -1:
                connection = {}
                split_line = line.split()
                split_line_length = len(split_line)

                proto = split_line[0] if split_line_length >= 1 else None
                local_address = split_line[3] if split_line_length >= 4 else None
                foreign_address = split_line[4] if split_line_length >= 5 else None
                state = split_line[5] if split_line_length >= 6 else None
                pid_program_name = split_line[6] if split_line_length >= 7 else None

                local_address_split = local_address.split(":")
                local_ip = (
                    "::" if local_address[0:2] == "::" else local_address_split[0]
                )
                local_port = local_address_split[len(local_address_split) - 1]

                foreign_address_split = foreign_address.split(":")
                foreign_ip = (
                    "::" if foreign_address[0:2] == "::" else foreign_address_split[0]
                )
                foreign_port = foreign_address_split[len(foreign_address_split) - 1]

                if pid_program_name is None and state not in NETSTAT_STATES:
                    pid_program_name = state
                    state = None
                if pid_program_name == "-":
                    pid_program_name = None

                connection.update(
                    {
                        "proto": proto,
                        "local_address": local_address,
                        "local_ip": local_ip,
                        "local_port": local_port,
                        "foreign_address": foreign_address,
                        "foreign_ip": foreign_ip,
                        "foreign_port": foreign_port,
                        "state": state,
                        "pid_program_name": pid_program_name,
                    }
                )

                # Ommit local connections
                if local_ip != foreign_ip and foreign_ip != "0.0.0.0":
                    connections.append(connection)

        # Craft the device dictionary
        device = {}
        device.update(
            {
                "name": name,
                "id": id,
                "image": image,
                "stack": stack,
                "pid": pid,
                "ip_addresses": ip_addresses,
                "listen_ports": listen_ports,
                "connections": connections,
            }
        )
        devices.append(device)

    # Loop through all the connections and update them to include the name of the container matching the foreign ip
    for device in devices:
        connections = device.get("connections")
        for connection in connections:
            foreign_ip = connection.get("foreign_ip")
            foreign_device = None
            if (
                foreign_ip != "::"
                and foreign_ip != "0.0.0.0"
                and foreign_ip != "127.0.0.1"
            ):
                if foreign_ip in network_name_set:
                    foreign_device = network_name_set.get(foreign_ip)
                else:
                    foreign_device = ip_device_set.get(foreign_ip)
            connection.update({"foreign_device": foreign_device})
    return devices, network_name_set


def main():
    processes = None
    devices = None
    network_name_set = None

    discover_processes = True
    discover_containers = True

    if not (discover_processes or discover_containers):
        print("No discover options enabled. Aborting.")
        exit()

    host = {}
    if discover_processes:
        processes = get_processes()
        host["processes"] = processes
    if discover_containers:
        devices, network_name_set = get_containers()
        host["devices"] = devices

    if processes and network_name_set:
        for v in processes.values():
            for c in v["connections"]:
                if c["local_ip"] in network_name_set:
                    c["foreign_device"] = network_name_set[c["local_ip"]]

    snapshot_time = datetime.now(timezone.utc).isoformat()
    payload = {"snapshot_time": snapshot_time, "host": host}

    if mongo:
        from pymongo import MongoClient

        conn_str = "mongodb://localhost:27017/"
        client = MongoClient(conn_str)
        db = client["dashdb"]
        collection = db["snapshots"]
        result = collection.insert_one(payload)
        print("Inserted document ID:", result.inserted_id)

    else:
        print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
