from dash import Dash, html, Input, Output
import dash_cytoscape as cyto
import json

# Load our data (Dump of output from dd.py)
with open('data/dd.json', 'r') as f:
    containers = json.load(f)

# This is needed to use advanced layouts like cola, spread, etc
cyto.load_extra_layouts()

# Styling for nodes/edges is done here
stylesheet=[
    # Main Node class that all non-compound graph nodes will inherit
    {
        'selector': '.graph-node',
        'style': {
            'shape': 'circle',
            'content': 'data(label)',
            'text-halign': 'right',
            'text-valign': 'center',
            'font-family': 'sans-serif',
            'font-weight': 'normal',
            'font-size': 8,
            'width': 10,
            'height': 10,
            'color': '#735050',
            'text-margin-x': 2
        }
    },
    # Docker container node style
    {
        'selector': '.docker-container',
        'style': {
            'background-color': '#F4ABAB'
        }
    },
    # Foreign IP node style
    {
    'selector': '.foreign-ip',
    'style': {
        'background-color': '#735050'
    }
    },
    {
        'selector': 'edge',
        'style': {
            'target-arrow-color': '#735050',
            'target-arrow-shape': 'triangle-backcurve',
            'target-arrow-fill': 'fill',
            'line-style': 'solid',
            'arrow-scale': .5,
            'curve-style': 'straight',
            'line-color': '#735050',
            'width': .5,
            'target-distance-from-node': '2px'
        }
    },
    {
        'selector': ':selected',
        'style': {
            'background-color': '#04A1D2',
            'line-color':  '#04A1D2',
            'target-arrow-color': '#04A1D2'
        }
    },
    {
        'selector': '.stacks',
        'style':{
            'background-color': '#F2F2F2',
            'content': 'data(label)',
            'text-valign': 'top',
            'color': '#735050',
            'font-size': 12,
            'min-width': 100,
            'min-height': 100,
            'shape': 'roundrectangle',
            'text-margin-y': -3,
            'weight': 'normal'
        }
    }
]

def coalesce(*args):
    """Return the first argument that is not None."""
    for arg in args:
        if arg is not None:
            return arg
    return None

app = Dash(__name__)

parent_nodes = []
parent_names = []
child_nodes = []
child_names = []
edges = []
for container in containers:
    name = container.get('name')
    parent_name = container.get('stack')

    if(parent_name):
        parent_node = {
            'group': 'nodes',
            'data': {
                'id': parent_name,
                'label': parent_name
            },
            'classes': 'stacks'
        }
    child_node = {
        'group': 'nodes',
        'data': {
            'id': name,
            'label': name,
            'parent': parent_name if parent_name else None
        },
        'classes': 'graph-node docker-container'
    }
    if(parent_name and parent_name not in parent_names):
        parent_names.append(parent_name)
        parent_nodes.append(parent_node)
    
    connections = container.get('connections')
    listen_ports = container.get('listen_ports')

    # Dont add any containers without connections
    #if(len(connections) > 0):
    child_nodes.append(child_node)
    child_names.append(name)

    for connection in connections:
        foreign_device = connection.get('foreign_device')

        if(foreign_device is None or foreign_device.endswith(" (Gateway)")):
            foreign_ip = connection.get('foreign_ip')
            if(foreign_ip not in child_names):
                child_names.append(foreign_ip)
                child_node = {
                    'group': 'nodes',
                    'data': {
                        'id': foreign_ip,
                        'label': coalesce(foreign_device, foreign_ip)
                    },
                    'classes': 'graph-node foreign-ip'
                }
                child_nodes.append(child_node)
            if (int(connection.get('local_port')) in listen_ports):
                edge = {
                    'group': 'edges',
                    'data': {
                        'id': foreign_ip+name,
                        'source': foreign_ip,
                        'target': name
                    }
                }
                edges.append(edge)
            else:
                edge = {
                'group': 'edges',
                'data': {
                    'id': foreign_ip+name,
                    'source': name,
                    'target': foreign_ip
                }
            }
            edges.append(edge)
    
        else:
            # Search for the container record that matches foeign_device
            foreign_container = next(dict for dict in containers if dict.get('name') == foreign_device)
            if (int(connection.get('local_port')) in listen_ports):
                edge = {
                    'group': 'edges',
                    'data': {
                        'id': foreign_device+name,
                        'source': foreign_device,
                        'target': name
                    }
                }
                edges.append(edge)
            elif (int(connection.get('foreign_port')) in foreign_container.get('listen_ports')):
                edge = {
                    'data': {
                        'id': name+foreign_device,
                        'source': name,
                        'target': foreign_device
                    }
                }
                edges.append(edge)

app.layout = html.Div([
    html.Div(html.Div('Docker Topology',className="app-header-title"),className="app-header"),
    html.Div([
        html.Div(
            html.Pre(
                id='cytoscape-tapNodeData-json', 
                style={'border': 'thin lightgrey solid','overflowX': 'scroll','height': '98%'},
                className='app-details-text'
            ), 
            className="a"
        ),
        html.Div(
            cyto.Cytoscape(
                id='cytoscape', 
                elements=child_nodes + parent_nodes + edges, 
                layout={'name': 'cola'}, 
                stylesheet=stylesheet, 
                style={'width': '100%', 'height': '98%'},
                maxZoom=1.8,
                minZoom=1.1
            ), 
            className="b"
        )],
        className="app-body"
    )
    ],
    className="container"
)

@ app.callback(Output('cytoscape-tapNodeData-json', 'children'), Input('cytoscape', 'tapNodeData'))
def displayTapNodeData(data):
    container = None
    if(data):
        id = data.get('id')
        if(id in parent_names):
            child_names = [container.get('name') for container in containers if container.get('stack') == id]
            stack_blob = {
                'Container Stack': id,
                'Container Count': len(child_names),
                'Container Names': child_names
            }
            return json.dumps(stack_blob, indent=2)
        else:
            container = next((dict for dict in containers if dict.get('name') == data.get('id')), None)
            if(container):
                return json.dumps(container, indent=2)
            else:
                return json.dumps(data, indent=2)
    else:
        return "Click on a node to see additional details"

if __name__ == '__main__':
    # Default
    app.run(host="0.0.0.0", port=8050, debug=False)
    
    # Local Development
    # app.run(host="127.0.0.1", port=8050, debug=False)