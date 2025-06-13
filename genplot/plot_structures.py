import plotly.graph_objects as go

'''
In this module, we define our plot structure:
- the map settings, font, etc.
- the color scales
'''

'''
THEME LAYOUT
'''
THEME_LAYOUT = go.Layout(
    # FONT/TEXT
    font={
        'color': '#1e4a4a',
        'family': 'Helvetica'
    },
    title={
        'font': {
            'family': 'Georgia, serif',
            'size': 24,
            'weight': 'bold'
        },
        'x': .2
    },
    #MAPS
    geo={
        'scope': 'usa',
        'bgcolor': "#ffffff",
        'landcolor': "#ffffff",
        'subunitcolor': '#1e4a4a'
    },
    #NON-GEO PLOTS
    plot_bgcolor="#ffffff",
    paper_bgcolor="#ffffff",
    scattermode='overlay',
    #GENERAL
    showlegend=True

)
THEME = go.layout.Template(layout=THEME_LAYOUT)

'''
COLORS
'''
GENDER_SPLIT_SCALE = [
        [0.0, '#30003B'], 
        [0.1, '#6c307b'],
        [0.3, '#9657A5'], 
        [0.4, '#CFBCD0'],
        [0.45, '#fbecfc'], 
        [.5, '#F3F4F3'],
        [0.55, '#d8f7e7'],
        [0.6, '#AAC9B8'], 
        [0.7, '#0B8569'],
        [0.9, '#00573e'], 
        [1.0, '#06474D']
]

ACCEPTANCE_RATE_SCALE = [
    [0.0, "#000004"],
    [0.1, "#1b0c41"],
    [0.2, "#4f0a6d"],
    [0.3, "#781c6d"],
    [0.4, "#a42c60"],
    [0.5, "#cc444c"],
    [0.6, "#ed6925"],
    [0.7, "#fb9a06"],
    [0.8, "#f7d13d"],
    [0.9, "#fcfdbf"],
    [1.0, "#ffffff"]
]

GRADUATION_RATE_SCALE = [
    [0.0, "#fd7f25"],
    [0.2, "#fdae25"],
    [0.35, "#fddd25"],
    [0.5, "#dede2b"],
    [0.55, "#c3de2b"],
    [0.6, "#b5de2b"],
    [0.65, "#6ece58"],
    [0.7, "#58ce7d"],
    [0.75, "#1f9e89"],
    [0.85, "#26748e"],
    [1.0, "#2c4682"]
]

EARNINGS_SCALE = [
    [0.0, "#320404"],
    [0.15, "#750C0C"],
    [0.25, "#8E3D3D"],
    [0.35, "#A75A5A"],
    [0.45, "#CF878E"],
    [0.5, "#CF87A9"],
    [0.55, "#DF9BD3"],
    [0.6, "#DFB8D8"],
    [0.75, "#AAA6F4"],
    [0.80, "#A8BCFE"],
    [1.0, "#CDEAF5"]
]

