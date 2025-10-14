from dash import html
import dash_cytoscape as cyto
from styles import stylesheet

def create_layout(elements):
    return html.Div([
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
                elements=elements, 
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