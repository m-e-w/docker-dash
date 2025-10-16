import docker
import json
import sys
import subprocess
from datetime import datetime, timezone

mongo = False
if len(sys.argv) > 1 and sys.argv[1] == "mongo":
    mongo = True

NETSTAT_STATES = ["CLOSE_WAIT", "CLOSED", "ESTABLISHED", "FIN_WAIT_1", "FIN_WAIT_2", "LAST_ACK", "LISTEN", "SYN_RECEIVED", "SYN_SEND", "TIME_WAIT"]

client = docker.from_env()
info = client.info()
containers = client.containers.list()
networks = client.networks.list()
client.close()

host = {"name": info['Name'], "os": info['OperatingSystem'], "cpu": info['NCPU'], "ram": round(info['MemTotal'] / 1024 / 1024 / 1024, 2)}

network_name_set = {}
for network in networks:
    network_config = network.attrs.get('IPAM').get('Config')
    if network_config:
        gateway = network_config[0].get('Gateway')
        if gateway:
            name = network.name
            network_name_set[gateway] = name + " (Gateway)"

ip_device_set = {}
devices = []
for container in containers:
    name = container.name
    id = container.short_id
    image = container.attrs.get('Config').get('Image')
    pid = container.attrs.get('State').get('Pid')
    stack = container.attrs.get('Config').get('Labels').get('com.docker.compose.project')
    ip_addresses = []
    connections = []
    listen_ports = []

    network_settings = container.attrs.get('NetworkSettings')
    ports = network_settings.get('Ports').keys()
    for port in ports:
        listen_port = int(port[:-4])
        listen_ports.append(listen_port)

    networks = network_settings.get('Networks').values()
    for network in networks:
        ip_address = network['IPAddress']
        ip_device_set[ip_address] = container.name
        ip_addresses.append(ip_address)
    
    nsenter_netstat_cmd = ["sudo", "nsenter", "-t", str(pid), "-n", "netstat", "-anp"]
    nsenter_netstat_cmd_output = subprocess.check_output(nsenter_netstat_cmd)
    netstat_split_lines = str(nsenter_netstat_cmd_output).split('\\n')
    for line in netstat_split_lines:
        if (line.find("tcp") != -1 or line.find("udp") != -1):
            connection = {}
            split_line = line.split()
            split_line_length = len(split_line)

            proto = split_line[0] if split_line_length >= 1 else None
            local_address = split_line[3] if split_line_length >= 4 else None
            foreign_address = split_line[4] if split_line_length >= 5 else None
            state = split_line[5] if split_line_length >= 6 else None
            pid_program_name = split_line[6] if split_line_length >= 7 else None

            local_address_split = local_address.split(':')
            local_ip = '::' if local_address[0: 2] == '::' else local_address_split[0]
            local_port = local_address_split[len(local_address_split) - 1]

            foreign_address_split = foreign_address.split(':')
            foreign_ip = '::' if foreign_address[0:2] == '::' else foreign_address_split[0]
            foreign_port = foreign_address_split[len(foreign_address_split) - 1]

            if (pid_program_name is None and state not in NETSTAT_STATES):
                pid_program_name = state
                state = None
            if (pid_program_name == '-'):
                pid_program_name = None

            connection.update({
                "proto": proto,
                "local_address": local_address,
                "local_ip": local_ip,
                "local_port": local_port,
                "foreign_address": foreign_address,
                "foreign_ip": foreign_ip,
                "foreign_port": foreign_port,
                "state": state,
                "pid_program_name": pid_program_name
            })

            # Ommit local connections
            if(local_ip != foreign_ip and foreign_ip != '0.0.0.0'):
                connections.append(connection)

    # Craft the device dictionary
    device = {}
    device.update({
        "name": name,
        "id": id,
        "image": image,
        "stack": stack,
        "pid": pid,
        "ip_addresses": ip_addresses,
        "listen_ports": listen_ports,
        "connections": connections
    })
    devices.append(device)

# Loop through all the connections and update them to include the name of the container matching the foreign ip
for device in devices:
    connections = device.get('connections')
    for connection in connections:
        foreign_ip = connection.get('foreign_ip')
        foreign_device = None
        if(foreign_ip != '::' and foreign_ip != '0.0.0.0' and foreign_ip != '127.0.0.1'):
            if foreign_ip in network_name_set:
                foreign_device = network_name_set.get(foreign_ip)
            else:
                foreign_device = ip_device_set.get(foreign_ip)
        connection.update({"foreign_device": foreign_device})

# Dump the data out

host['devices'] = devices
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
