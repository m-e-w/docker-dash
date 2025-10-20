# utils.py


def coalesce(*args):
    """Return the first argument that is not None."""
    for arg in args:
        if arg is not None:
            return arg
    return None


def make_node(id, label, classes, parent=None):
    """Create and return a cytoscape node dictionary."""
    # if "foreign-ip" in classes:
    #     parent = '__EXTERNAL__'
    node = {}
    data = {"id": id, "label": label}
    if parent:
        data["parent"] = parent
    node = {"group": "nodes", "data": data, "classes": classes}
    return node


def make_edge(id, source, target):
    """Create and return a cytoscape edge dictionary."""
    edge = {"group": "edges", "data": {"id": id, "source": source, "target": target}}
    return edge

def anonymize_ip(ip):
    """Take a IP as input and return a anonymized one"""
    if '.' in ip:
        octets = ip.split('.')
        if len(octets) != 4:
            return ip
        else:
            octets.pop(3) # Remove last octect
            octets.append('X')
            return '.'.join(str(octet) for octet in octets)
    return ip


