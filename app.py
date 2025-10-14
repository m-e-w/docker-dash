from dash import Dash, Input, Output
import dash_cytoscape as cyto
from layout import create_layout
from data_processing import process_container_data
from utils import coalesce
import json
import sys

# This is needed to use advanced layouts like cola, spread, etc
cyto.load_extra_layouts()

app = Dash(__name__)

def serve_layout():
    # Process container data for visualization
    child_nodes, parent_nodes, edges, containers, parent_names = process_container_data()

    # Store these in the app’s server context
    app.containers = containers
    app.parent_names = parent_names

    # Set up the app layout with the generated elements
    return create_layout(elements=child_nodes + parent_nodes + edges)

# Dynamically serve the layout to ensure fresh data on each load
app.layout = serve_layout

@ app.callback(Output('cytoscape-tapNodeData-json', 'children'), Input('cytoscape', 'tapNodeData'))
def displayTapNodeData(data):
    if(data):
        id = data.get('id')
        if(id in app.parent_names):
            child_names = [c.get('name') for c in app.containers if c.get('stack') == id]
            return json.dumps({
                'Container Stack': id,
                'Container Count': len(child_names),
                'Container Names': child_names
            }, indent=2)
        else:
            container = next((c for c in app.containers if c.get('name') == data.get('id')), None)
            return json.dumps(coalesce(container, data), indent=2)
    else:
        return "Click on a node to see additional details"

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        print("Running in development mode")
        app.run(host="127.0.0.1", port=8050, debug=False)
    else:
        print("Running in normal mode")
        app.run(host="0.0.0.0", port=8050, debug=False)
    