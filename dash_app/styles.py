# Styling for nodes/edges is done here
stylesheet = [
    # Main Node class that all non-compound graph nodes will inherit
    {
        "selector": ".graph-node",
        "style": {
            "shape": "circle",
            "content": "data(label)",
            "text-halign": "right",
            "text-valign": "center",
            "font-family": "sans-serif",
            "font-weight": "normal",
            "font-size": 8,
            "width": 10,
            "height": 10,
            "color": "#735050",
            "text-margin-x": 2,
        },
    },
    # Docker container node style
    {"selector": ".docker-container", "style": {"background-color": "#F4ABAB"}},
    {"selector": ".process", "style": {"background-color": "#84B067"}},
    # Foreign IP node style
    {"selector": ".foreign-ip", "style": {"background-color": "#735050"}},
    {"selector": ".docker-gateway-ip", "style": {"background-color": "#9367B0"}},
    {
        "selector": "edge",
        "style": {
            "target-arrow-color": "#735050",
            "target-arrow-shape": "triangle-backcurve",
            "target-arrow-fill": "fill",
            "line-style": "solid",
            "arrow-scale": 0.5,
            "curve-style": "straight",
            "line-color": "#735050",
            "width": 0.5,
            "target-distance-from-node": "2px",
        },
    },
    {
        "selector": ":selected",
        "style": {
            "background-color": "#04A1D2",
            "line-color": "#04A1D2",
            "target-arrow-color": "#04A1D2",
        },
    },
    {
        "selector": ".stacks",
        "style": {
            "background-color": "#F2F2F2",
            "content": "data(label)",
            "text-valign": "top",
            "color": "#735050",
            "font-size": 12,
            "min-width": 100,
            "min-height": 100,
            "shape": "roundrectangle",
            "text-margin-y": -3,
            "weight": "normal",
        },
    },
]
