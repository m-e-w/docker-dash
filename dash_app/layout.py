from dash import html, dcc
import dash_cytoscape as cyto
from styles import stylesheet
from datetime import datetime

def create_layout(elements):
    return html.Div([
        # Header
        html.Div([
            html.Div('Docker Topology', className="app-header-title"),
            html.Div([
                html.Label("Load last N # of Snapshots:", style={'marginRight': '8px'}),
                dcc.Input(
                    id='num-snapshots-input',
                    type='number',
                    min=1,
                    value=100,  # default
                    style={'width': '80px'}
                ),
                html.Button("Load", id='apply-button', style={'marginLeft': '10px', 'marginRight': '8px'}),
                html.Button("Export", id='export-button', style={'marginRight': '8px'}),
            ], style={'display': 'flex', 'alignItems': 'center'}),
            dcc.Download(id="export-graph")
        ],
        style={
            'display': 'flex',
            'justifyContent': 'space-between',  # pushes title left, control right
            'alignItems': 'center',
            #'padding': '10px 20px',
            #'marginRight': '200px'
        },
        className="app-header"),
        # Controls + Body
        html.Div([
            # Left column: node details
            html.Div(
                html.Pre(
                    id='cytoscape-tapNodeData-json',
                    style={'border': 'thin lightgrey solid', 'overflowX': 'scroll', 'height': '98%'},
                    className='app-details-text'
                ),
                className="a"
            ),

            # Right column: graph + controls
            html.Div(
                # Cytoscape Graph
                cyto.Cytoscape(
                    id='cytoscape',
                    elements=elements,
                    layout={'name': 'cola'},
                    stylesheet=stylesheet,
                    style={'width': '100%', 'height': '98%'},
                    maxZoom=1.8,
                    minZoom=1.1
                ), 
                className="b")
        ], className="app-body")
    ], className="container")

