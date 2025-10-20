"""
layout.py

This module defines the main layout for the Docker Dash application using Dash and Dash Cytoscape.

It provides a single function `create_layout(elements)` that returns the complete app layout
as a Dash HTML tree. See file for layout structure.

Notes:
- `elements` argument must be a list of Cytoscape elements (nodes and edges) to render.
- This module is responsible only for the **structure/layout**; styling is handled via
  CSS in `assets/styles.css` and Cytoscape styles in `styles.py`.
- For dynamic interactions (search, taps, updates), use Dash callbacks in a separate module.
"""

from dash import html, dcc
import dash_cytoscape as cyto
from styles import stylesheet
from datetime import datetime


def create_layout(elements):
    return html.Div(
        [
            # Header
            html.Div(
                [
                    # --- Left side: title ---
                    html.Div("Docker Dash", className="app-header-title"),
                    # --- Right side: legend + controls together ---
                    html.Div(
                        [
                            # Legend section
                            html.Div(
                                [
                                    # html.Span("Legend:", style={'fontWeight': 'bold', 'marginRight': '8px'}),
                                    # Container
                                    html.Span(
                                        [
                                            html.Span(
                                                style={
                                                    "display": "inline-block",
                                                    "width": "12px",
                                                    "height": "12px",
                                                    "backgroundColor": "#F4ABAB",
                                                    "borderRadius": "50%",
                                                    "marginRight": "6px",
                                                }
                                            ),
                                            "CONTAINER",
                                        ],
                                        style={"marginRight": "12px"},
                                    ),
                                    # Process
                                    html.Span(
                                        [
                                            html.Span(
                                                style={
                                                    "display": "inline-block",
                                                    "width": "12px",
                                                    "height": "12px",
                                                    "backgroundColor": "#84B067",
                                                    "borderRadius": "50%",
                                                    "marginRight": "6px",
                                                }
                                            ),
                                            "PROCESS",
                                        ],
                                        style={"marginRight": "12px"},
                                    ),
                                    # Docker Network / Gateway IP
                                    html.Span(
                                        [
                                            html.Span(
                                                style={
                                                    "display": "inline-block",
                                                    "width": "12px",
                                                    "height": "12px",
                                                    "backgroundColor": "#9367B0",
                                                    "borderRadius": "50%",
                                                    "marginRight": "6px",
                                                }
                                            ),
                                            "GATEWAY",
                                        ],
                                        style={"marginRight": "12px"},
                                    ),
                                    # Foreign IP
                                    html.Span(
                                        [
                                            html.Span(
                                                style={
                                                    "display": "inline-block",
                                                    "width": "12px",
                                                    "height": "12px",
                                                    "backgroundColor": "#735050",
                                                    "borderRadius": "50%",
                                                    "marginRight": "6px",
                                                }
                                            ),
                                            "IP",
                                        ],
                                        style={"marginRight": "24px"},
                                    ),
                                ],
                                className="legend-section",
                                style={"display": "flex", "alignItems": "center"},
                            ),
                            # Inputs + buttons
                            html.Label("Snapshots:", style={"marginRight": "8px"}),
                            dcc.Input(
                                id="num-snapshots-input",
                                type="number",
                                min=1,
                                value=100,
                                style={"width": "80px"},
                            ),
                            html.Button(
                                "Load",
                                id="apply-button",
                                style={"marginLeft": "10px", "marginRight": "8px"},
                            ),
                            html.Button(
                                "Export",
                                id="export-button",
                                style={"marginRight": "8px"},
                            ),
                            dcc.Download(id="export-graph"),
                            dcc.Input(
                                id="node-search",
                                type="text",
                                placeholder="Search node...",
                                debounce=False,
                                style={"width": "160px", "marginRight": "8px"},
                            ),
                            dcc.Store(id="base-styles", data=stylesheet),
                        ],
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "flexWrap": "wrap",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    # 'height': '30px'
                },
                className="app-header",
            ),
            # --- Body ---
            html.Div(
                [
                    # Left column: node details
                    html.Div(
                        html.Pre(
                            id="cytoscape-tapNodeData-json",
                            className="app-details-text",
                        ),
                        className="a",
                    ),
                    # Right column: graph
                    html.Div(
                        cyto.Cytoscape(
                            id="cytoscape",
                            elements=elements,
                            layout={"name": "cola"},
                            stylesheet=stylesheet,
                            style={"width": "100%", "height": "100%"},
                            maxZoom=1.8,
                            minZoom=1.1,
                        ),
                        className="b",
                    ),
                ],
                className="app-body",
            ),
        ],
        className="container",
    )
