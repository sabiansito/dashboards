from dash import register_page,dcc, html
import dash_bootstrap_components as dbc
from .settings import load_settings

settings = load_settings()
register_page(
    __name__,
    path='/builder',
)

def layout(**kwargs):
    lay = dbc.Container([
        dcc.Store(
            id='memory_charts',
            storage_type='memory',
            data = {
                'list_charts':[]
            }
        ),
        dbc.Row([
            dbc.ButtonGroup([
                dbc.DropdownMenu(
                    [
                        dbc.DropdownMenuItem(
                            'Add Timeline',
                            id='add_chart_button',
                        ),
                    ],
                    label = 'Add Plots'
                ),
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Container(
                    children = [],
                    id='plot_container',
                    fluid=True,
                    style = {
                        'height': '100%',
                        'width': '100%',
                        'padding':'0',
                    }
                )        
            ],width=8),
            dbc.Col([
                dbc.Container(
                    children=[html.P(settings['API_URL'])],
                    id='side_plot',
                    fluid = True,
                    style = {
                        'height': '100%',
                        'width': '100%',
                        'padding':'0',
                    },
                    className='border-bottom '
                )
            ])
        ])
    ])
    
    return [lay]