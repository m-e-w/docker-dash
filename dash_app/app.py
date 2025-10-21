"""
app.py

Main module for the Docker Dash application.

This module defines the DashApp class, which encapsulates the entire Dash application,
including layout serving, data processing, and interactive callbacks.

Notes:
- Cytoscape styling comes from styles.py; general page layout from layout.py and assets/styles.css.
"""

from dash import Dash, Input, Output, State, no_update
from styles import stylesheet as base_stylesheet
import dash_cytoscape as cyto
from layout import create_layout
from data_processing import DataProcessor
from utils import coalesce
import json
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class DashApp:
    def __init__(self, dev_mode=False, mask_ip_labels=True, hide_procs_with_no_inbound=True):
        cyto.load_extra_layouts()  # This is needed to use advanced layouts like cola, spread, etc
        self.limit = 100
        self.dev_mode = dev_mode
        self.app = Dash(__name__)
        self.data_processor = DataProcessor(
            dev_mode=dev_mode,
            mask_ip_labels=mask_ip_labels,
            hide_procs_with_no_inbound=hide_procs_with_no_inbound,
        )
        self.layout_serve_count = 0  # Kind of a hacky workaround to avoid loading data from mongo on start. Need to find a better solution
        self.app.layout = (
            self.serve_layout
        )  # Dynamically serve the layout to ensure fresh data on each load
        self.elements = []
        self.register_callbacks()

    def serve_layout(self):
        # Process container data for visualization

        elements = None
        if (
            self.layout_serve_count > 1
        ):  # Avoid calling process_container_data on the first layout serves dash performs (only load data once the user navigates to page)
            child_nodes, parent_nodes, edges, containers, parent_names = (
                self.data_processor.process_container_data(self.limit)
            )
            self.containers = containers
            self.parent_names = parent_names
            elements = child_nodes + parent_nodes + edges
            # print("PARENT NODES")
            # print(json.dumps(parent_nodes, indent=2))
            # print("CHILD NODES")
            # print(json.dumps(child_nodes, indent=2))

        self.layout_serve_count += (
            1  # Increment out layout serve counter so that we actually do get data
        )
        # Set up the app layout with the generated elements
        self.elements = elements
        return create_layout(elements=elements)

    def register_callbacks(self):
        @self.app.callback(
            Output("cytoscape-tapNodeData-json", "children"),
            Input("cytoscape", "tapNodeData"),
            prevent_initial_call=True,
        )
        def displayTapNodeData(data):
            if data:
                id = data.get("id")
                id = id[3:]  # Remove prefix id
                if id in self.parent_names:
                    child_names = [c.get("name") for c in self.containers if c.get("stack") == id]
                    return json.dumps(
                        {
                            "Container Stack": id,
                            "Container Count": len(child_names),
                            "Container Names": child_names,
                        },
                        indent=2,
                    )
                else:
                    container = next((c for c in self.containers if c.get("name") == id), None)
                    return json.dumps(coalesce(container, data), indent=2)
            else:
                return "Click on a node to see additional details"

        @self.app.callback(
            Output("cytoscape", "elements"),
            Input("apply-button", "n_clicks"),
            State("num-snapshots-input", "value"),
            prevent_initial_call=True,
        )
        def update_snapshot_data(n_clicks, limit):
            # If user supplied limit is invalid, return special signal to dash to not change output
            if not limit or not isinstance(limit, int) or limit < 1:
                return no_update
            else:
                child_nodes, parent_nodes, edges, containers, parent_names = (
                    self.data_processor.process_container_data(limit=limit)
                )
                self.containers = containers
                self.parent_names = parent_names
                elements = child_nodes + parent_nodes + edges
                self.elements = elements
                return elements

        @self.app.callback(
            Output("export-graph", "data"),
            Input("export-button", "n_clicks"),
            prevent_initial_call=True,
        )
        def export_snapshots(n_clicks):
            if self.elements:
                export_data = json.dumps(self.elements, indent=2)
                return dict(content=export_data, filename="snapshots.json")
            else:
                return None

        # Client side callback for search/highlight so we don't send a POST request on every keystroke
        self.app.clientside_callback(
            """
        function(searchValue, baseStyles) {
            const styles = JSON.parse(JSON.stringify(baseStyles));  // clone so we don’t mutate it
            if (!searchValue) return styles;

            styles.push({
                selector: `node[label *= "${searchValue}"]`,
                style: {
                'background-color': '#04A1D2'
                }
            });
            return styles;
        }
        """,
            Output("cytoscape", "stylesheet"),
            Input("node-search", "value"),
            Input("base-styles", "data"),
        )

    def run(self):
        if self.dev_mode:
            print("Running in development mode")
            self.app.run(host="127.0.0.1", port=8050, debug=False)
        else:
            print("Running in normal mode")
            self.app.run(host="0.0.0.0", port=8050, debug=False)


def main():
    dev_mode = False
    mask_ip_labels = False
    hide_procs_with_no_inbound = False

    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        dev_mode = True

    dash_app = DashApp(
        dev_mode=dev_mode,
        mask_ip_labels=mask_ip_labels,
        hide_procs_with_no_inbound=hide_procs_with_no_inbound,
    )
    dash_app.run()


if __name__ == "__main__":
    main()
