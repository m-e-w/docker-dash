from dash import Dash, Input, Output, State
import dash_cytoscape as cyto
from layout import create_layout
from data_processing import DataProcessor
from utils import coalesce
import json
import sys


class DashApp:
    def __init__(self, dev_mode=False):
        cyto.load_extra_layouts() # This is needed to use advanced layouts like cola, spread, etc
        self.limit = 100
        self.dev_mode = dev_mode
        self.app = Dash(__name__)
        self.data_processor = DataProcessor(dev_mode=dev_mode) 
        self.app.layout = self.serve_layout # Dynamically serve the layout to ensure fresh data on each load
        self.register_callbacks()

    def serve_layout(self):
        # Process container data for visualization
        child_nodes, parent_nodes, edges, containers, parent_names = self.data_processor.process_container_data(self.limit)
        
        #print("PARENT NODES")
        #print(json.dumps(parent_nodes, indent=2))

        #print("CHILD NODES")
        #print(json.dumps(child_nodes, indent=2))
        
        self.containers = containers
        self.parent_names = parent_names

        # Set up the app layout with the generated elements
        return create_layout(elements=child_nodes + parent_nodes + edges)

    def register_callbacks(self):
        @self.app.callback(Output('cytoscape-tapNodeData-json', 'children'), Input('cytoscape', 'tapNodeData'))
        def displayTapNodeData(data):
            if(data):
                id = data.get('id')
                if(id in self.parent_names):
                    child_names = [c.get('name') for c in self.containers if c.get('stack') == id]
                    return json.dumps({
                        'Container Stack': id,
                        'Container Count': len(child_names),
                        'Container Names': child_names
                    }, indent=2)
                else:
                    container = next((c for c in self.containers if c.get('name') == data.get('id')), None)
                    return json.dumps(coalesce(container, data), indent=2)
            else:
                return "Click on a node to see additional details"
    
        @self.app.callback(Output('cytoscape', 'elements'), Input('apply-button', 'n_clicks'), State('num-snapshots-input', 'value'), prevent_initial_call=True)
        def update_snapshot_data(n_clicks, limit):
            if not limit or limit < 1:
                limit = DEFAULT_SNAPSHOT_LIMIT
                
            child_nodes, parent_nodes, edges, containers, parent_names = self.data_processor.process_container_data(limit=limit)
            self.containers = containers
            self.parent_names = parent_names
            
            return child_nodes + parent_nodes + edges

    def run(self):
        if self.dev_mode:
            print("Running in development mode")
            self.app.run(host="127.0.0.1", port=8050, debug=False)
        else:
            print("Running in normal mode")
            self.app.run(host="0.0.0.0", port=8050, debug=False)
    
def main():
    dev_mode = False
    
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        dev_mode = True

    dash_app = DashApp(dev_mode=dev_mode)
    dash_app.run()

if __name__ == '__main__':
    main()
    
