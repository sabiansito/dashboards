# region Import Modules
from dash import register_page,dcc, html, Input, Output, callback, State, no_update, ctx, Dash, redirect, render_template, session, url_for
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from pypika import PostgreSQLQuery, Schema, CustomFunction, Field, Case,DatePart,Interval,Order
from pypika import functions as fn
import httpx
import pandas as pd
import numpy as np
from plotly import graph_objects as go
from matplotlib.pyplot import colormaps, get_cmap
import dash_ag_grid as dag
from .settings import load_settings
# auth0 import modules
from urllib.parse import quote_plus, urlencode
from authlib.integrations.dash_client import OAuth
from dotenv import find_dotenv, load_dotenv


# endregion
# region Global Variables 
#Load Environment Variables
settings = load_settings()

#API URL
api_url = settings['API_URL']

#Database Connection Headers to API
headers = {
    'x-api-key': settings['API_KEY'],
    'customer': settings['API_CUSTOMER'],
    'originator': settings['API_ORIGINATOR'],
    'Content-Type': 'text/plain',
    'Accept': 'application/json;q=1.0,application/json;q=0.9,*/*;q=0.8'
}

#Register Page
register_page(
    __name__,
    path_template='/aqueon/<case_name>',
)
# endregion


# region Utility Functions
#Database Schema
aqueon = Schema('aqueon')

##Custom Function to create Distinct Queries
distinct = CustomFunction('DISTINCT', ['*'])
make_date = CustomFunction('MAKE_DATE', ['year','month','day'])
date_trunc = CustomFunction('DATE_TRUNC', ['interval','date'])

#function to convert hex to rgba
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def hex_to_rgba(hex_color,alpha):
    rgb = hex_to_rgb(hex_color)
    #add alpha
    rgba = rgb + (alpha,)
    return rgba

def hex_to_rgba_str(hex_color,alpha):
    rgba = hex_to_rgba(hex_color,alpha)
    return f'rgba{str(rgba)}'

phases_dict = {
    'oil':{
        'actual_color':'#11690e',
        'db_column':'Qo'
    },
    'gross':{
        'actual_color':'#90900e',
        'db_column':'Ql'
    },
    'water':{
        'actual_color':'#0e4e90',
        'db_column':'Qw'
    },
    'injectant':{
        'actual_color':'#0e9090',
        'db_column':'Qs'
    },
    'gas':{
        'actual_color':'#90110e',
        'db_column':'Qg'
    }
}

# endregion


# region Layout functions
# Bar Buttons layout
bar_buttons_dict = {
    'modeBarButtonsToAdd':
        [
            'hoverClosestCartesian', 
            'hoverCompareCartesian',
            'drawline',
            'drawrect',
            'drawcircle',
            'eraseshape',
            'lasso2d',
            'drawopenpath',
            'drawclosedpath',
        ],
    'displaylogo': False,
    'showAxisDragHandles': True,
    'showAxisRangeEntryBoxes': True,
    'fillFrame':False,
    'autosizable':True,
    'frameMargins': 0,
    'editable': True,
    'showTips': True,
    'edits':{
        'legendPosition':True,
        'legendText':True,
        'colorbarPosition':True,
        'colorbarTitleText':True
    },
    'toImageButtonOptions':{
        'filename':settings['API_CUSTOMER'],
        'format':'png'
    }
}


def create_card(title,id,icon=None):
    return dbc.Card([
        dbc.CardBody([
            html.H6(
                [html.I(className=icon),title], 
                className='card-title text-center mb-0'),
            html.P(id=id, className='card-value text-center mb-0')
        ],className='p-2')    
    ],className='mb-3')
    
def create_etl_aggrid(title):
    return [
        html.H6(f'{title.capitalize()} Top Producers',className='text-center'),
        dag.AgGrid(
            id = f'etl_top_{title}_producers',
            style={"height": "100%", "width": "100%"}
        )
    ]
#example  create_card()

#create layout for plottling optioons to edit
def create_plot_options(phase):
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H6('Actual Data',className='text-center'),
                    dbc.Label('Left axis scale', html_for=f'summary_settings_{phase}_yscale'),
                    dbc.RadioItems(
                        options=[
                            {'label':'Linear','value':'linear'},
                            {'label':'Log','value':'log'}
                        ],
                        value='linear',
                        inline= True,
                        id=f'summary_settings_{phase}_yscale',
                        labelCheckedClassName='text-success',
                        inputCheckedClassName='border border-success bg-success'
                    ),
                    dbc.Label('Units', html_for=f'summary_settings_{phase}_units'),
                    dbc.RadioItems(
                        options=[
                            {'label':'Metric','value':'metric'},
                            {'label':'Field','value':'field'},
                        ],
                        value='field',
                        inline = True,
                        id=f'summary_settings_{phase}_units',
                        labelCheckedClassName="text-success",
                        inputCheckedClassName="border border-success bg-success"
                    ),
                    dbc.Label('Actual Data Linestyle', html_for=f'summary_settings_{phase}_actual_linestyle'),
                    dbc.RadioItems(
                        options = [
                            {'label':'Solid','value':'solid'},
                            {'label':'Dash','value':'dash'},
                            {'label':'Dot','value':'dot'},
                            {'label':'DashDot','value':'dashdot'},
                        ], 
                        value='dot',
                        inline = True,
                        id=f'summary_settings_{phase}_actual_linestyle',
                        labelCheckedClassName="text-success",
                        inputCheckedClassName="border border-success bg-success",
                    ),
                    dbc.Label('Actual Data Line Width', html_for=f'summary_settings_{phase}_actual_width'),
                    dbc.Input(
                        type='number',
                        min=1,
                        step=1,
                        value=5,
                        id=f'summary_settings_{phase}_actual_width'
                    ),
                    dbc.Label('Actual Line Shape', html_for=f'summary_settings_{phase}_actual_shape'),
                    dbc.RadioItems(
                        options = [
                            {'label':i,'value':i} for i in ['hv','vh','hvh','vhv','spline','linear']
                        ], 
                        value='hvh',
                        inline = True,
                        id=f'summary_settings_{phase}_actual_shape',
                        labelCheckedClassName="text-success",
                        inputCheckedClassName="border border-success bg-success",
                    ),
                    dbc.Label('Actual Line Mode', html_for=f'summary_settings_{phase}_actual_mode'),
                    dbc.RadioItems(
                        options = [
                            {'label':i,'value':i} for i in ['lines','lines+markers','markers']
                        ], 
                        value='lines',
                        inline = True,
                        id=f'summary_settings_{phase}_actual_mode',
                        labelCheckedClassName="text-success",
                        inputCheckedClassName="border border-success bg-success",
                    ),
                    dbc.Label('Actual Color', html_for=f'summary_settings_{phase}_actual_color'),
                    dbc.Input(
                        type = 'color',
                        id = f'summary_settings_{phase}_actual_color',
                        value = phases_dict[phase]['actual_color']
                    ),
                    dbc.Label('Color Alpha', html_for=f'summary_settings_{phase}_actual_alpha'),
                    dcc.Slider(
                        id = f'summary_settings_{phase}_actual_alpha',
                        min=0.,
                        max=1.,
                        step = 0.05,
                        value=1.,
                        marks=None,
                        tooltip = {'always_visible':False,'placement':'bottom'}
                    ),
                    dbc.Label('Colormap', html_for=f'summary_settings_{phase}_actual_colormap'),
                    dbc.Select(
                        id = f'summary_settings_{phase}_colormap',
                        options = [
                            {
                                'label':i,
                                'value':i
                            } for i in colormaps()
                        ],
                        value='jet'
                    ),
                    dbc.Label('Colormap Alpha', html_for=f'summary_settings_{phase}_colormap_alpha'),
                    dcc.Slider(
                        id = f'summary_settings_{phase}_colormap_alpha',
                        min=0.,
                        max=1.,
                        step = 0.05,
                        value=1.,
                        marks=None,
                        tooltip = {'always_visible':False,'placement':'bottom'}
                    ),
                    html.Hr(),
                    html.H6('Fit Data',className='text-center'),
                    dbc.Label('Fit Percentile', html_for = f'summary_settings_{phase}_fit_percentiles'),
                    dbc.RadioItems(
                        id = f'summary_settings_{phase}_fit_percentiles',
                        options = [
                            {'label':'P10 - P90','value':'10-90'},
                            {'label':'P25 - P75','value':'25-75'},
                        ],
                        value = '25-75'
                    ),
                    dbc.Label('Fit Training Color', html_for=f'summary_settings_{phase}_fit_training_color'),
                    dbc.Input(
                        type = 'color',
                        id = f'summary_settings_{phase}_fit_training_color',
                        #color salmon
                        value = '#FA8072'
                    ),
                    dbc.Label('Fit Training Alpha', html_for=f'summary_settings_{phase}_fit_training_alpha'),
                    dcc.Slider(
                        id = f'summary_settings_{phase}_fit_training_alpha',
                        min=0.,
                        max=1.,
                        step = 0.05,
                        value=0.2,
                        marks=None,
                        tooltip = {'always_visible':False,'placement':'bottom'}
                    ),
                    dbc.Label('Fit Validation Color', html_for=f'summary_settings_{phase}_fit_validation_color'),
                    dbc.Input(
                        type = 'color',
                        id = f'summary_settings_{phase}_fit_validation_color',
                        value = '#4169E1'
                    ),
                    dbc.Label('Fit Validation Alpha', html_for=f'summary_settings_{phase}_fit_validation_alpha'),
                    dcc.Slider(
                        id = f'summary_settings_{phase}_fit_validation_alpha',
                        min=0.,
                        max=1.,
                        step = 0.05,
                        value=0.5,
                        marks=None,
                        tooltip = {'always_visible':False,'placement':'bottom'}
                    ),
                    dbc.Label('Fit Line Color', html_for=f'summary_settings_{phase}_fit_line_color'),
                    dbc.Input(
                        type = 'color',
                        id = f'summary_settings_{phase}_fit_line_color',
                        value = '#000000'
                    ),
                    dbc.Label('Fit Line Alpha', html_for=f'summary_settings_{phase}_fit_line_alpha'),
                    dcc.Slider(
                        id = f'summary_settings_{phase}_fit_line_alpha',
                        min=0.,
                        max=1.,
                        step = 0.05,
                        value=0.5,
                        marks=None,
                        tooltip = {'always_visible':False,'placement':'bottom'}
                    )
                ])
            ])
        ])
    ])


# endregion


#region Layout
# ---------------------------------------------------------------------------- #
#                                Layout Function                               #
# ---------------------------------------------------------------------------- #
#Main Layout Function. This is the function that will be called when the page is loaded.
#It receives the case_name as a parameter
def layout(case_name, **kwargs):
    lay = dbc.Container(
        children=[
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(f'Aqueon Case: {case_name}', id='case_name'),
                        dcc.Store(id='case_name_store', data={'case_name': case_name}),
                        dbc.CardBody([
                            html.P([html.B('Customer: '), settings["API_CUSTOMER"]], className='mb-0'),
                            html.P([html.B('User: '), settings["API_ORIGINATOR"]], className='mb-0'),
                        ], className='p-2')
                    ], className='mb-3')
                    #html.H3(case_name, id='case_name')
                ],width=4),
                dbc.Col([
                    dbc.Row([
                        dbc.Col(create_card('Layers','badge_layers','fa-solid fa-layer-group')),
                        dbc.Col(create_card('FaultBlocks','badge_faultblock','fa-solid fa-table-cells')),
                        dbc.Col(create_card('Compartments','badge_compartment','fa-regular fa-table-cells')),
                    ]),
                    dbc.Row([
                        dbc.Col(create_card('Total Wells','badge_total_wells','fa-solid fa-location-dot')),
                        dbc.Col(create_card('Producer Wells','badge_producer_wells','fa-solid fa-oil-well')),
                        dbc.Col(create_card('Injector Wells','badge_injector_wells','fa-solid fa-droplet')),
                        dbc.Col(create_card('Conversion Wells','badge_conversion_wells','fa-solid fa-right-left')),
                    ])
                ])
            ]),
            dbc.Tabs([
                dbc.Tab(
                    children=[
                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader([
                                        'Production Data ',
                                        dbc.Button(
                                            [html.I(className='fa-solid fa-gear')],
                                            color = 'link',
                                            size='sm',
                                            id = 'aqueon-summary-settings',
                                        ),
                                        dbc.Button(
                                            [html.I(className='fa-solid fa-pencil')],
                                            color = 'link',
                                            size='sm',
                                            id = 'aqueon-summary-edit',
                                        ),
                                        dbc.Modal(
                                            children = [
                                                dbc.ModalHeader(dbc.ModalTitle('Edit Production Data')),
                                                dbc.ModalBody([
                                                    dbc.Tabs([
                                                        dbc.Tab(create_plot_options(p),label=p) for p in phases_dict
                                                    ])
                                                ])
                                            ],
                                            id = 'aqueon-summary-edit-modal',
                                            is_open = False,
                                            centered=True
                                        )
                                    ]),
                                    dbc.CardBody([
                                        dbc.Row([
                                            dbc.Col([create_card('Fit Start Date','aqueon-summary-fit-startdate','fa-solid fa-calendar-day')]),
                                            dbc.Col([create_card('Fit End Date','aqueon-summary-fit-enddate','fa-solid fa-calendar-day')]),
                                            dbc.Col([create_card('Type of Run','aqueon-summary-fit-type','fa-solid fa-running')]),
                                            dbc.Col([create_card('Backtest End Date','aqueon-summary-fit-backtest-enddate','fa-solid fa-calendar-day')])
                                        ]),
                                        html.Hr(),
                                        dbc.Collapse([
                                            dbc.Row([
                                                dbc.Col([
                                                    dcc.Dropdown(
                                                        id='summary_settings_producers_dropdown',
                                                        clearable=True,
                                                        multi=True,
                                                        searchable=True,
                                                        placeholder='Select Producers',
                                                        persistence=False,
                                                        value = []
                                                    ),
                                                    dcc.Dropdown(
                                                        id='summary_settings_injectors_dropdown',
                                                        clearable=True,
                                                        multi=True,
                                                        searchable=True,
                                                        placeholder='Select Injectors',
                                                        persistence=False,
                                                        value = []
                                                    ),
                                                    dbc.Checklist(
                                                        id='summary_settings_aggregation_checklist',
                                                        options = [
                                                            {'label':'Wells','value':'WellAPI'},
                                                            {'label':'Compartment','value':'Compartment'},
                                                            {'label':'Reservoir','value':'Reservoir'},
                                                            {'label':'Fault Block','value':'FaultBlock'},
                                                            {'label':'Type','value':'Type'}
                                                        ],
                                                        value = [],
                                                        inline=True
                                                    ),
                                                    dbc.Checklist(
                                                        id='summary_bhp_or_wellcount_switch',
                                                        options = [
                                                            {'label':'BHP','value':'bhp'},
                                                            {'label':'Well Count','value':'wellcount'}
                                                        ],
                                                        value = ['wellcount'],
                                                        inline=True,
                                                        switch=True
                                                    ),
                                                    dbc.Checkbox(
                                                        id='summary_settings_show_fit',
                                                        value=True,
                                                        label = 'Show Fit'
                                                    )
                                                ]),
                                                dbc.Col([
                                                    dcc.Dropdown(
                                                        id='summary_settings_layers_dropdown',
                                                        clearable=True,
                                                        multi=True,
                                                        searchable=True,
                                                        placeholder='Select Layers',
                                                        persistence=False,
                                                        value=[],
                                                        options=[]
                                                    ),
                                                    dcc.Dropdown(
                                                        id='summary_settings_faultblocks_dropdown',
                                                        clearable=True,
                                                        multi=True,
                                                        searchable=True,
                                                        placeholder='Select FaultBlocks',
                                                        persistence=False,
                                                        value = [],
                                                        options=[]
                                                    ),
                                                    dcc.Dropdown(
                                                        id='summary_settings_compartments_dropdown',
                                                        clearable=True,
                                                        multi=True,
                                                        searchable=True,
                                                        placeholder='Select Compartments',
                                                        persistence=False,
                                                        value = [],
                                                        options=[]
                                                    ),
                                                ]),
                                                # dbc.Col([])
                                            ]),
                                        ],id='aqueon-summary-settings-collapse',is_open=False),
                                        dbc.Row([
                                            dbc.Accordion([
                                                dbc.AccordionItem([
                                                    dbc.Spinner(dcc.Graph(
                                                        id=f'summary_plot_{p}',
                                                        style={'height':'60vh','width': '100%','padding':'0','margin':'0'},
                                                        config = bar_buttons_dict
                                                    )) 
                                                ],title=p.capitalize(),item_id=p) for p in phases_dict
                                            ],flush=True,id='summary_plot_accordion')
                                        ]),
                                    ])
                                ])
                                #],style={'width':'66vw','padding':'0','margin':'0'}) 
                            ],width=7),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader([
                                        'Map',
                                        dbc.Button(
                                            [html.I(className='fa-solid fa-gear')],
                                            color = 'link',
                                            size='sm',
                                            id = 'aqueon-summarymap-settings',
                                        ),
                                    ]),
                                    dbc.CardBody([
                                        dbc.Accordion([
                                            dbc.AccordionItem([
                                                dbc.Collapse([
                                                    dbc.Row([
                                                        dbc.Col([
                                                            dbc.Checklist(
                                                                id='summarymap_settings_aggregation_checklist',
                                                                options = [
                                                                    {'label':'Wells','value':'WellAPI'},
                                                                    {'label':'Compartment','value':'Compartment'},
                                                                    {'label':'Reservoir','value':'Reservoir'},
                                                                    {'label':'Fault Block','value':'FaultBlock'},
                                                                    {'label':'Type','value':'Type'}
                                                                ],
                                                                value = ['Type'],
                                                                inline=True
                                                            ),
                                                            dbc.Checkbox(
                                                                id='summarymap_checkbox_wellpath',
                                                                value=False,
                                                                label='Well Path'
                                                            ),
                                                            dbc.Checkbox(
                                                                id = 'summarymap_checkbox_groupby',
                                                                value=True,
                                                                label='Group By'
                                                            ),
                                                            dbc.Checkbox(
                                                                label = 'hide unselected wells',
                                                                value=False,
                                                                id='summarymap_checkbox_hideunselected'
                                                            ),
                                                            dbc.Select(
                                                                id = f'summary_settings_map_colormap',
                                                                options = [
                                                                    {
                                                                        'label':i,
                                                                        'value':i
                                                                    } for i in colormaps()
                                                                ],
                                                                value='winter'
                                                            ),
                                                            dcc.Slider(
                                                                id = f'summary_settings_map_colormap_alpha',
                                                                min=0.,
                                                                max=1.,
                                                                step = 0.05,
                                                                value=1.0,
                                                                marks=None,
                                                                tooltip = {'always_visible':False,'placement':'bottom'}
                                                            ),
                                                        ]),
                                                        
                                                    ])
                                                ],id='aqueon-summarymap-settings-collapse',is_open=False),
                                                dbc.Spinner(dcc.Graph(
                                                    id='summary_map',
                                                    style={'height':'100%','width': '100%'},
                                                    config = bar_buttons_dict
                                                )),                                                
                                            ],title='Map',item_id='map'),
                                            dbc.AccordionItem([
                                                dbc.Collapse([
                                                    dbc.Row([
                                                        dbc.Col([
                                                            dbc.Label('Columns to Add Crossplot',html_for='summarycrossplot_settings_aggregation_checklist'),
                                                            dbc.Checklist(
                                                                id='summarycrossplot_settings_aggregation_checklist',
                                                                options = [
                                                                    {'label':'Wells','value':'WellAPI'},
                                                                    {'label':'Compartment','value':'Compartment'},
                                                                    {'label':'Reservoir','value':'Reservoir'},
                                                                    {'label':'Fault Block','value':'FaultBlock'},
                                                                    {'label':'Type','value':'Type'}
                                                                ],
                                                                value = [],
                                                                inline=True
                                                            ),
                                                            dbc.Label('Columns to color by Crossplot',html_for='summarycrossplot_settings_hue_checklist'),
                                                            dbc.Checklist(
                                                                id='summarycrossplot_settings_hue_checklist',
                                                                options = [
                                                                    {'label':'Wells','value':'WellAPI'},
                                                                    {'label':'Compartment','value':'Compartment'},
                                                                    {'label':'Reservoir','value':'Reservoir'},
                                                                    {'label':'Fault Block','value':'FaultBlock'},
                                                                    {'label':'Type','value':'Type'}
                                                                ],
                                                                value = ['WellAPI','Reservoir'],
                                                                inline=True
                                                            ),
                                                            dbc.Select(
                                                                id = f'summary_settings_crossplot_colormap',
                                                                options = [
                                                                    {
                                                                        'label':i,
                                                                        'value':i
                                                                    } for i in colormaps()
                                                                ],
                                                                value='winter'
                                                            ),
                                                            dcc.Slider(
                                                                id = f'summary_settings_crossplot_colormap_alpha',
                                                                min=0.,
                                                                max=1.,
                                                                step = 0.05,
                                                                value=1.0,
                                                                marks=None,
                                                                tooltip = {'always_visible':False,'placement':'bottom'}
                                                            ),
                                                            dbc.Checkbox(
                                                                id = 'summarycrossplot_checkbox_include_wells',
                                                                value=True,
                                                                label='Always Include Wells'
                                                            ),
                                                            dbc.Checkbox(
                                                                id = 'summarycrossplot_checkbox_hideunselected',
                                                                value=False,
                                                                label='hide unselected wells'
                                                            )
                                                        ])
                                                    ])
                                                ],id='aqueon-summarycrossplot-settings-collapse',is_open=True),
                                                dbc.Spinner(dcc.Graph(
                                                    id='summary_crossplot',
                                                    style = {'height':'100%','width':'100%'},
                                                    config=bar_buttons_dict
                                                ))
                                            ],title='Cross Plot',item_id='crossplot')
                                        ],flush=True, id='summary_map_accordion',active_item='map',always_open=True)
                                    ])
                                ],style={'padding':'0','margin':'0'})
                            ],width=5)
                        ])
                    ],
                    label='Summary',
                    tab_id='tab_summary'
                ),
                dbc.Tab(
                    children=[
                        dbc.Row([
                            dbc.Col([
                                html.H6('Production Data',className='text-center'),
                                # small text to show the date range
                                html.Small(id='etl_date_range',className='text-center'),
                                create_card('Oil Cum',id='etl_oil_cum',icon='fa-solid fa-oil-can'),
                                create_card('Water Cum',id='etl_water_cum',icon='fa-solid fa-water'),
                                create_card('Gas Cum',id='etl_gas_cum',icon='fa-solid fa-cloud'),
                                create_card('Inj Cum',id='etl_injectant_cum',icon='fa-solid fa-droplet'),
                            ],width=2),
                            *[dbc.Col(create_etl_aggrid(p),width=3) for p in ['wells','layers']]
                        ])
                    ],
                    label='ETL',
                    tab_id='tab_etl'
                ),
                # dbc.Tab(
                #     children=[],
                #     label='Scenarios'
                # ),
                # dbc.Tab(
                #     children=[],
                #     label='Maps'
                # )
            ],active_tab='tab_etl'),
        ],
        fluid=True,
    )
    return [lay]
# endregion

# region Callbacks
# ---------------------------------------------------------------------------- #
#                               Callbacks Section                              #
# ---------------------------------------------------------------------------- #

# region Counting Callbacks
# ---------------------------- Counting Callbacks ---------------------------- #
##Callback to update the total wells
@callback(
    Output('badge_total_wells','children'),
    Input('case_name_store','data'),
)
def update_badge_total_wells(data):
    case_name = data['case_name']
    #Table object
    productiondata = aqueon.productiondata
    
    #001-count_total.sql
    query = PostgreSQLQuery.from_(
        productiondata
    ).select(
        fn.Count(distinct(
            getattr(productiondata, 'WellAPI')
        )).as_('total_wells')
    ).where(getattr(productiondata, 'casename') == case_name)
    
    query_str = query.get_sql()

    with httpx.Client(timeout=30) as client:
        response = client.post(
            f'{api_url}/dataexplorer/query/tachyus',
            headers=headers,
            data=query_str
        )
        
    if response.status_code == 200:
        data = response.json()
        total_wells = data[0]['total_wells']
    return total_wells

## Callback to update the producer wells
@callback(
    Output('badge_producer_wells','children'),
    Input('case_name_store','data')
)
def update_badge_producer_wells(data):
    case_name = data['case_name']
    productiondata = aqueon.productiondata
    
    #002-count_producer.sql
    query = PostgreSQLQuery.from_(
        productiondata
    ).select(
        fn.Count(distinct(
            getattr(productiondata, 'WellAPI')
        )).as_('producer_wells')
    ).where(
        (getattr(productiondata, 'Qo') + getattr(productiondata, 'Qw') + getattr(productiondata, 'Qg')) > 0,
    ).where(
        getattr(productiondata, 'casename') == case_name
    )

    query_str = query.get_sql()

    with httpx.Client(timeout=30) as client:
        response = client.post(
            f'{api_url}/dataexplorer/query/tachyus',
            headers=headers,
            data=query_str
        )
        
    if response.status_code == 200:
        data = response.json()
        producer_wells = data[0]['producer_wells']
    return producer_wells

## Callback to update the injector wells
@callback(
    Output('badge_injector_wells','children'),
    Input('case_name_store','data')
)
def update_badge_injector_wells(data):
    case_name = data['case_name']
    productiondata = aqueon.productiondata
    
    #003-count_injector.sql
    query = PostgreSQLQuery.from_(
        productiondata
    ).select(
        fn.Count(distinct(
            getattr(productiondata, 'WellAPI')
        )).as_('injector_wells')
    ).where(
        getattr(productiondata, 'Qs') > 0
    ).where(
        getattr(productiondata, 'casename') == case_name
    )

    query_str = query.get_sql()

    with httpx.Client(timeout=30) as client:
        response = client.post(
            f'{api_url}/dataexplorer/query/tachyus',
            headers=headers,
            data=query_str
        )
        
    if response.status_code == 200:
        data = response.json()
        injector_wells = data[0]['injector_wells']
    return injector_wells

## Callback to update Conversion Wells
@callback(
    Output('badge_conversion_wells','children'),
    Input('case_name_store','data')
)
def update_badge_conversion_wells(data):
    case_name = data['case_name']
    productiondata = aqueon.productiondata
    
    #004-count_conversion.sql
    inner_query = PostgreSQLQuery.from_(productiondata) \
        .select(
            getattr(productiondata, 'WellAPI'),
            fn.Count(distinct(getattr(productiondata,'Status'))).as_('status_count')
        ).where(
            getattr(productiondata, 'casename') == case_name
        ).groupby(
            getattr(productiondata, 'WellAPI')
        ).having(
            fn.Count(distinct(getattr(productiondata,'Status'))) > 1
        )
        
    query = PostgreSQLQuery.from_(inner_query) \
        .select(
            fn.Count(distinct(Field('WellAPI'))).as_('conversion_wells')
        )
    

    query_str = query.get_sql()

    
    #raise PreventUpdate
    with httpx.Client(timeout=30) as client:
        response = client.post(
            f'{api_url}/dataexplorer/query/tachyus',
            headers=headers,
            data=query_str
        )
        
    if response.status_code == 200:
        data = response.json()
        conversion_wells = data[0]['conversion_wells']
    return conversion_wells

## Callback to update Layers
@callback(
    Output('badge_layers','children'),
    Output('badge_faultblock','children'),
    Output('badge_compartment','children'),
    Input('case_name_store','data')
)
def update_badge_layers_wells(data):
    case_name = data['case_name']
    completiondata = aqueon.completiondata
    
    #005-count_layer_fb_comp
    query = PostgreSQLQuery.from_(
        completiondata
    ).select(
        fn.Count(distinct(
            getattr(completiondata, 'Reservoir')
        )).as_('total_layers'),
        fn.Count(distinct(
            getattr(completiondata, 'FaultBlock')
        )).as_('total_faultblocks'),
        fn.Count(distinct(
            getattr(completiondata, 'Compartment')
        )).as_('total_compartments'),
    ).where(getattr(completiondata, 'casename') == case_name)
    

    query_str = query.get_sql()
    
    #raise PreventUpdate
    with httpx.Client(timeout=30) as client:
        response = client.post(
            f'{api_url}/dataexplorer/query/tachyus',
            headers=headers,
            data=query_str
        )
        
    if response.status_code == 200:
        data = response.json()
        n_layers = data[0]['total_layers']
        n_faultblocks = data[0]['total_faultblocks']
        n_compartments = data[0]['total_compartments']
    else:
        print(response.status_code,response.text)
        raise PreventUpdate
    return n_layers, n_faultblocks, n_compartments
    
# endregion

# region Summary Tab Callbacks

# region Modal Callbacks
@callback(
    Output('aqueon-summary-edit-modal','is_open'),
    Input('aqueon-summary-edit','n_clicks'),
    State('aqueon-summary-edit-modal','is_open')
)
def toggle_edit_modal(n, is_open):
    if n:
        return not is_open
    return is_open
# endregion

# region fit info
# ------------------------------- Fit info data ------------------------------ #
@callback(
    Output('aqueon-summary-fit-startdate','children'),
    Output('aqueon-summary-fit-enddate','children'),
    Output('aqueon-summary-fit-type','children'),
    Output('aqueon-summary-fit-backtest-enddate','children'),
    Input('case_name_store','data')
)
def update_fit_info(data):
    case_name = data['case_name']
    
    #Table object
    fit_info = aqueon.fit_info
    
    #009-fit_info.sql
    query = PostgreSQLQuery.from_(
        fit_info
    ).select(
        getattr(fit_info, 'FitStartDate').as_('fit_startdate'),
        getattr(fit_info, 'FitEndDate').as_('fit_enddate'),
        getattr(fit_info, 'IsBacktest').as_('is_backtest'),
        getattr(fit_info, 'BacktestEndDate').as_('backtest_enddate'),
        getattr(fit_info,'Dt').as_('dt')
    ).where(
        getattr(fit_info, 'casename') == case_name
    ).limit(1)
    
    query_str = query.get_sql()
    with httpx.Client(timeout=30) as client:
        response = client.post(
            f'{api_url}/dataexplorer/query/tachyus',
            headers=headers,
            data=query_str
        )
        
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data).squeeze()
    else:
        print(response.status_code,response.text)
        raise PreventUpdate
    
    list_return = [
        df['fit_startdate'][:10],
        df['fit_enddate'][:10],
        'BT' if df['is_backtest'] else 'FF',
        df['backtest_enddate'][:10] if df['is_backtest'] else 'N/A'
    ]
    return list_return
    
# endregion

# region Dropdown Callbacks
# ---------------------------- Dropdown Callbacks ---------------------------- #

# Callback to update Wells by status
@callback(
    Output('summary_settings_producers_dropdown','options'),
    Output('summary_settings_injectors_dropdown','options'),
    Input('case_name_store','data')
)
def update_producers_injectors_dropdown(data):
    case_name = data['case_name']
    #table object
    productiondata = aqueon.productiondata
    completiondata = aqueon.completiondata
    
    #007-producers_injectors_dropdown.sql
    query_base = PostgreSQLQuery.from_(
        productiondata
    ).left_join(
        aqueon.completiondata
    ).on(
        (productiondata.WellAPI == completiondata.WellAPI) &
        (productiondata.casename == completiondata.casename)
    ).where(
        getattr(productiondata, 'casename') == case_name
    )
    
    query_producers = query_base.where(
        (getattr(productiondata, 'Qo') + getattr(productiondata, 'Qw') + getattr(productiondata, 'Qg')) > 0,
    ).select(
        getattr(completiondata, 'WellName'),
        getattr(productiondata, 'WellAPI'),
        getattr(productiondata, 'Status'),
    ).distinct()
    
    query_injectors = query_base.where(
        getattr(productiondata, 'Qs') > 0
    ).select(
        getattr(completiondata, 'WellName'),
        getattr(productiondata, 'WellAPI'),
        getattr(productiondata, 'Status')
    ).distinct()
    
    query = query_producers + query_injectors
    
    query_str = query.get_sql()
    with httpx.Client(timeout=30) as client:
        response = client.post(
            f'{api_url}/dataexplorer/query/tachyus',
            headers=headers,
            data=query_str
        )
        
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
    else:
        print(response.status_code,response.text)
        raise PreventUpdate
    
    list_dropdowns = []
    
    for well_type in [1,2]:
        list_dict = df.loc[df['Status']==well_type].apply(lambda x: {'label':x['WellName'],'value':x['WellAPI']},axis=1).tolist()
        list_dropdowns.append(list_dict)
    return list_dropdowns

# Callback to update Layers, FaultBlocks and Compartments
@callback(
    Output('summary_settings_layers_dropdown','options'),
    Output('summary_settings_faultblocks_dropdown','options'),
    Output('summary_settings_compartments_dropdown','options'),
    Input('case_name_store','data')
)
def update_ly_fb_comp_dropdown(data):
    case_name = data['case_name']
    #table object
    completiondata = aqueon.completiondata
    
    #008-ly_fb_comp_dropdown.sql
    query_base = PostgreSQLQuery.from_(
        completiondata
    ).where(
        getattr(completiondata, 'casename') == case_name
    )
    
    query_layer = query_base.select(
        getattr(completiondata, 'Reservoir').as_('name'),
        #add constant column
        fn.LiteralValue("'layer'").as_('type')
    ).distinct()
    
    query_faultblock = query_base.select(
        getattr(completiondata, 'FaultBlock').as_('name'),
        fn.LiteralValue("'faulblock'").as_('type')
    ).distinct()
    
    query_compartment = query_base.select(
        getattr(completiondata, 'Compartment').as_('name'),
        fn.LiteralValue("'compartment'").as_('type')
    ).distinct()
    
    
    query = query_layer + query_faultblock + query_compartment
    query_str = query.get_sql()

    with httpx.Client(timeout=30) as client:
        response = client.post(
            f'{api_url}/dataexplorer/query/tachyus',
            headers=headers,
            data=query_str
        )
        
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
    else:
        print(response.status_code,response.text)
        raise PreventUpdate
    
    
    list_dropdowns = []
    
    for i in ['layer','faultblock','compartment']:
        sr = df.loc[(df['type']==i)&(df['name'].notnull())].apply(lambda x: {'label':x['name'],'value':x['name']},axis=1)
        if sr.empty:
            list_dropdowns.append(no_update)
        else:
            list_dropdowns.append(sr.tolist())
    return list_dropdowns


# endregion

# region Map Callbacks
# ------------------------------- Map Callbacks ------------------------------ #
@callback(
    Output('summary_map','figure'),
    Input('summary_map_accordion','active_item'),
    Input('case_name_store','data'),
    Input('summary_settings_producers_dropdown','value'),
    Input('summary_settings_injectors_dropdown','value'),
    Input('summary_settings_layers_dropdown','value'),
    Input('summary_settings_faultblocks_dropdown','value'),
    Input('summary_settings_compartments_dropdown','value'),
    Input('summarymap_settings_aggregation_checklist','value'),
    Input('summarymap_checkbox_wellpath','value'),
    Input('summarymap_checkbox_groupby','value'),
    Input('summary_settings_map_colormap','value'),
    Input('summary_settings_map_colormap_alpha','value'),
    Input('summarymap_checkbox_hideunselected','value'),
)
def update_map(
    active_item,
    data,
    prods,
    injs,
    layers,
    fbs,
    comps,
    agg,
    path,
    groupby,
    colormap,
    alpha,
    hide_unselected
):
    
    if 'map' not in active_item:
        raise PreventUpdate
    case_name = data['case_name']
    #Table object
    completiondata = aqueon.completiondata
    
    #006-avg_coordinates_wells.sql
    query = PostgreSQLQuery.from_(
        completiondata
    ).where(
        getattr(completiondata, 'casename') == case_name
    )
    #Base selection columns.
    cols_base = [
        getattr(completiondata, 'WellName'),
        getattr(completiondata, 'WellAPI'),
    ]
    
    #check if there are aggregation columns
    if len(agg)>0:
        agg_cols = [getattr(completiondata,i) for i in agg]
    else:
        agg_cols = [fn.LiteralValue("'field'").as_('field')]
        agg.append('field')
    
    #check if groupby is selected
    if groupby:
        # aggregation columns
        func_base_cols = [
            fn.Avg(getattr(completiondata, 'Latitude')).as_('Latitude'),
            fn.Avg(getattr(completiondata, 'Longitude')).as_('Longitude'),
            fn.Avg(getattr(completiondata, 'X')).as_('Easting'),
            fn.Avg(getattr(completiondata, 'Y')).as_('Northing'),
        ]
        select_cols = agg_cols + cols_base + func_base_cols
        groupby_cols = agg_cols + cols_base
        query = query.select(*select_cols).groupby(*groupby_cols)
        
    else:
        # Columns no aggregation
        cols_no_agg = [
            getattr(completiondata, 'Latitude').as_('Latitude'),
            getattr(completiondata, 'Longitude').as_('Longitude'),
            getattr(completiondata, 'X').as_('Easting'),
            getattr(completiondata, 'Y').as_('Northing'),
            getattr(completiondata, 'Type').as_('Type')
        ]
        select_cols = agg_cols + cols_base + cols_no_agg
        query = query.select(*select_cols).orderby(getattr(completiondata,'TD'))
        
    #If there are filters add them to the query
    filters_dict = {
        #'WellAPI':prods+injs,
        'Reservoir':layers,
        'Compartment':comps,
        'FaultBlock':fbs
    }
    
    #iterate over the filters and add them to the query
    for k,f in filters_dict.items():
        #check if the filter is not empty to add filter to the query
        if len(f)>0:
            query = query.where(
                getattr(completiondata,k).isin(f)
            )
            
    #check if wells are selected
    if len(prods+injs)>0:
        case_selected = Case().when(
            getattr(completiondata, 'WellAPI').isin(prods+injs),True
        ).else_(False).as_('is_selected')
    else:
        case_selected = fn.LiteralValue(False).as_('is_selected')
    query = query.select(case_selected)
    
    #if hide unselected wells is checked add filter to the query
    if hide_unselected and len(prods+injs)>0:
        query = query.where(getattr(completiondata, 'WellAPI').isin(prods+injs))
    
    # get the query string and send it to the api
    query_str = query.get_sql()
    with httpx.Client(timeout=30) as client:
        response = client.post(
            f'{api_url}/dataexplorer/query/tachyus',
            headers=headers,
            data=query_str
        )
        
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
    else:
        print(response.status_code,response.text)
        print(query_str)
        raise PreventUpdate
    
    list_traces = []

    # columns to be used to aggregate the data depending
    # on if require to plot the multiple points of a well
    path_bool = all([path, not groupby])
    agg_cols_if = ['WellAPI'] if path_bool else agg
    
    #add the selected column to the aggregation columns
    agg_cols_if.append('is_selected')
    
    #group the data by the aggregation columns
    df_gr = df.groupby(agg_cols_if)
    ngroups = df_gr.ngroups
    
    #get the colormap
    cmap = get_cmap(colormap,ngroups)
    
    # iterate over the groups and create the traces
    for i,(labels, dfi) in enumerate(df_gr):
        is_selected = labels[-1]
        
        trace = go.Scatter(
            x = dfi['Longitude'],
            y = dfi['Latitude'],
            mode = 'lines+markers' if path_bool else 'markers',
            name='-'.join(map(str,labels)),
            text = dfi.loc[:,['WellName']+agg_cols_if[:-1]].apply(lambda x: '<br>'.join([f'{i}: {j}' for i,j in x.items()]),axis=1),
            hovertemplate='<b>%{text}</b><br><br>',
            customdata=dfi['WellAPI'],
            #opacity=alpha if is_selected else 0.4,
            marker={
                'color':f'rgba{cmap(i,alpha)}',
                'size':10 if is_selected else 5,
                'line':{
                    'color':'black' if is_selected else 'white',
                    'width':1 if is_selected else 0.5,
                }
            }
        )
        list_traces.append(trace)
        #print(len(list_traces))
    
    #create the layout
    layout = go.Layout(
        title = 'Wells Selection',
        xaxis = {
            'title':'Easting',
        },
        yaxis = {
            'title':'northing',
            'scaleanchor':'x',
            'scaleratio':1,
        },
        margin={'l': 50, 'b': 50, 'r': 50},
        legend={
            'orientation':'h',
            'yanchor':'bottom',
            'y':-0.3,  
        },
        showlegend=True if ngroups<20 else False,
        clickmode='event+select',
        height=600
        
    )
    return {
        'data': list_traces,
        'layout': layout
    }

# Map selection callback
@callback(
    Output('summary_settings_producers_dropdown','value'),
    Output('summary_settings_injectors_dropdown','value'),
    Input('summary_map','selectedData'),
    Input('summary_map','clickData'),
    State('summary_settings_producers_dropdown','options'),
    State('summary_settings_injectors_dropdown','options'),
    State('summary_settings_producers_dropdown','value'),
    State('summary_settings_injectors_dropdown','value'),
    prevent_initial_call=True
)
def update_dropdown_map_select(selected,clicked,prods_options,injs_options,prods,injs):
    if selected is not None:
        points_selected = selected['points']
    else:
        points_selected = []
    
    if clicked is not None:
        points_clicked = clicked['points']
    else:
        points_clicked = []
        
    selected_click = points_selected + points_clicked
    if len(selected_click)>0:
        prod_selected = []
        inj_selected = []
        list_prods = [i['value'] for i in prods_options]
        list_injs = [i['value'] for i in injs_options]
        for p in selected_click:
            if p['customdata'] in list_prods:
                prod_selected.append(p['customdata'])
            elif p['customdata'] in list_injs:
                inj_selected.append(p['customdata'])
            else:
                pass
            
        return np.unique(prod_selected + prods).tolist(), np.unique(inj_selected + injs).tolist()
    raise PreventUpdate
    
    
#endregion

# region Production Callbacks

# ---------------------------- Production Callbacks ---------------------------- #
@callback(
    Output('aqueon-summary-settings-collapse','is_open'),
    Input('aqueon-summary-settings','n_clicks'),
    State('aqueon-summary-settings-collapse','is_open')
)
def toggle_settings_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@callback(
    Output('aqueon-summarycrossplot-settings-collapse','is_open'),
    Input('aqueon-summarymap-settings','n_clicks'),
    State('aqueon-summarycrossplot-settings-collapse','is_open')
)
def toggle_settings_map_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@callback(
    Output('aqueon-summarymap-settings-collapse','is_open'),
    Input('aqueon-summarymap-settings','n_clicks'),
    State('aqueon-summarymap-settings-collapse','is_open')
)
def toggle_settings_cross_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


#function to make plotting actual and fit setings

def func_plot_data_fit(phase):
    def func(
        active_phase,
        data,
        prods,
        injs,
        layers,
        fbs,
        comps,
        agg,
        second_props,
        show_fit,
        y_scale,
        units,
        actual_linestyle,
        actual_width,
        actual_shape,
        actual_mode,
        actual_color,
        actual_alpha,
        fit_percentiles,
        fit_training_color,
        fit_training_alpha,
        fit_validation_color,
        fit_validation_alpha,
        fit_line_color,
        fit_line_alpha,
        colormap,
        colormap_alpha
    ):
        
        if active_phase != phase:
            raise PreventUpdate
        
        case_name = data['case_name']
        #Table object
        productiondata = aqueon.productiondata
        completiondata = aqueon.completiondata
        producer_timestep = aqueon.producer_timestep
        injector_timestep = aqueon.injector_timestep
        fit_info = aqueon.fit_info
        
        #make the date column
        date_col = make_date(
            getattr(productiondata, 'Year'),
            getattr(productiondata, 'Month'),
            1
        ).as_('date')
        
        #010-real_production_data_base.sql    
        status = 1 if phase != 'injectant' else 2
        query_real_base = PostgreSQLQuery.from_(
            productiondata     
        ).where(
            getattr(productiondata, 'casename') == case_name
        ).where(
            getattr(productiondata,'Status') == status
        ).left_join(
            completiondata
        ).on(
            (productiondata.WellAPI == completiondata.WellAPI) &
            (productiondata.casename == completiondata.casename) &
            (productiondata.CompSubId == completiondata.CompSubId)
        )
        
        # If there's no aggregation just group by date
        if len(agg)==0:
            gr_cols_real = ['field']
            if phase == 'gross':
                query_real = query_real_base.select(
                    date_col,
                    fn.LiteralValue("'field'").as_('field'),
                    fn.Sum(getattr(productiondata, phases_dict['oil']['db_column']) + getattr(productiondata, phases_dict['water']['db_column'])).as_(phase),
                    fn.Count(distinct(getattr(productiondata, 'WellAPI'))).as_('wellcount'),
                    fn.Avg(getattr(productiondata,'BHP')).as_('bhp')
                ).groupby(
                    date_col
                ).orderby(
                    date_col
                )
            else:
                query_real = query_real_base.select(
                    date_col,
                    fn.LiteralValue("'field'").as_('field'),
                    fn.Sum(getattr(productiondata, phases_dict[phase]['db_column'])).as_(phase),
                    fn.Count(distinct(getattr(productiondata, 'WellAPI'))).as_('wellcount'),
                    fn.Avg(getattr(productiondata,'BHP')).as_('bhp')
                ).groupby(
                    date_col
                ).orderby(
                    date_col
                )
        #if there's aggregation like reservoir, wells, etc, group by date and aggregation
        else:
            agg_cols = [getattr(completiondata,i) for i in agg]
            gr_cols_real = agg
            if phase == 'gross':
                query_real = query_real_base.select(
                    date_col,
                    *agg_cols,
                    fn.Sum(getattr(productiondata, phases_dict['oil']['db_column']) + getattr(productiondata, phases_dict['water']['db_column'])).as_(phase),
                    #fn.Count(distinct(getattr(productiondata, 'WellAPI'))).as_('wellcount'),
                    #fn.Avg(getattr(productiondata,'BHP')).as_('bhp')
                ).groupby(
                    date_col,
                    *agg_cols
                ).orderby(
                    *agg_cols,
                    date_col
                )
            else:
                query_real = query_real_base.select(
                    date_col,
                    *agg_cols,
                    fn.Sum(getattr(productiondata, phases_dict[phase]['db_column'])).as_(phase),
                    #fn.Count(distinct(getattr(productiondata, 'WellAPI'))).as_('wellcount'),
                    #fn.Avg(getattr(productiondata,'BHP')).as_('bhp')
                ).groupby(
                    date_col,
                    *agg_cols
                ).orderby(
                    *agg_cols,
                    date_col
                )
            
        #fit query base
        
        if show_fit:
            p_lower, p_upper = fit_percentiles.split('-')
            fit_timestep = injector_timestep if phase=='injectant' else producer_timestep
            query_fit_base = PostgreSQLQuery.from_(
                fit_timestep    
            ).where(
                getattr(fit_timestep, 'casename') == case_name
            ).left_join(
                completiondata
            ).on(
                (fit_timestep.WellId == completiondata.WellAPI) &
                (fit_timestep.casename == completiondata.casename) &
                (fn.Cast(fit_timestep.CompletionId,'INTEGER') == fn.Cast(completiondata.CompSubId,'INTEGER'))
            ).left_join(
                fit_info
            ).on(
                fit_timestep.casename == fit_info.casename
            )
            
            # If there's no aggregation just group by date
            
            case_clause = Case().when(
                getattr(fit_info,'IsBacktest') == True,
                Case()
                    .when(getattr(fit_info,'BacktestEndDate') >= getattr(fit_timestep, 'Date'),'training')
                    .else_('validation')
                ).else_('training').as_('type_of_fit')
            
            if len(agg)==0:
                gr_cols_fit = ['field']
                
                # make the query if the phase is water
                if phase=='water':
                    query_fit = query_fit_base.select(
                        getattr(producer_timestep, 'Date').as_('date'),
                        fn.LiteralValue("'field'").as_('field'),
                        case_clause,
                        fn.Sum(
                            getattr(producer_timestep, f'GrossRateP50') - getattr(producer_timestep, f'OilRateP50')
                        ).as_(f'{phase}_rate_p50'),
                        fn.Sum(
                            getattr(producer_timestep, f'GrossRateP{p_lower}') - getattr(producer_timestep, f'OilRateP{p_lower}')
                        ).as_(f'{phase}_rate_p{p_lower}'),
                        fn.Sum(
                            getattr(producer_timestep, f'GrossRateP{p_upper}')-getattr(producer_timestep, f'OilRateP{p_upper}')
                        ).as_(f'{phase}_rate_p{p_upper}'),
                    ).groupby(
                        getattr(producer_timestep, 'Date').as_('date'),case_clause
                    ).orderby(
                        getattr(producer_timestep, 'Date').as_('date'),
                    )
                elif phase=='injectant':
                    query_fit = query_fit_base.select(
                        getattr(injector_timestep, 'Date').as_('date'),
                        fn.LiteralValue("'field'").as_('field'),
                        case_clause,
                        fn.Sum(getattr(injector_timestep, f'{phase.capitalize()}RateP50')).as_(f'{phase}_rate_p50'),
                        fn.Sum(getattr(injector_timestep, f'{phase.capitalize()}RateP{p_lower}')).as_(f'{phase}_rate_p{p_lower}'),
                        fn.Sum(getattr(injector_timestep, f'{phase.capitalize()}RateP{p_upper}')).as_(f'{phase}_rate_p{p_upper}'),
                    ).groupby(
                        getattr(injector_timestep, 'Date').as_('date'),case_clause
                    ).orderby(
                        getattr(injector_timestep, 'Date').as_('date'),
                    )
                else:
                    query_fit = query_fit_base.select(
                        getattr(producer_timestep, 'Date').as_('date'),
                        fn.LiteralValue("'field'").as_('field'),
                        case_clause,
                        fn.Sum(getattr(producer_timestep, f'{phase.capitalize()}RateP50')).as_(f'{phase}_rate_p50'),
                        fn.Sum(getattr(producer_timestep, f'{phase.capitalize()}RateP{p_lower}')).as_(f'{phase}_rate_p{p_lower}'),
                        fn.Sum(getattr(producer_timestep, f'{phase.capitalize()}RateP{p_upper}')).as_(f'{phase}_rate_p{p_upper}'),
                    ).groupby(
                        getattr(producer_timestep, 'Date').as_('date'),case_clause
                    ).orderby(
                        getattr(producer_timestep, 'Date').as_('date'),
                    )
            #if there's aggregation like reservoir, wells, etc, group by date and aggregation
            else:
                agg_cols = [getattr(completiondata,i) for i in agg]
                #gr_cols_fit = [*agg,'type_of_fit']
                gr_cols_fit = agg
                
                if phase=='water':
                    query_fit = query_fit_base.select(
                        getattr(producer_timestep, 'Date').as_('date'),
                        *agg_cols,
                        case_clause,
                        fn.Sum(
                            getattr(producer_timestep, f'GrossRateP50') - getattr(producer_timestep, f'OilRateP50')
                        ).as_(f'{phase}_rate_p50'),
                        fn.Sum(
                            getattr(producer_timestep, f'GrossRateP{p_lower}') - getattr(producer_timestep, f'OilRateP{p_lower}')
                        ).as_(f'{phase}_rate_p{p_lower}'),
                        fn.Sum(
                            getattr(producer_timestep, f'GrossRateP{p_upper}')-getattr(producer_timestep, f'OilRateP{p_upper}')
                        ).as_(f'{phase}_rate_p{p_upper}'),
                    ).groupby(
                        getattr(producer_timestep, 'Date').as_('date'),
                        *agg_cols,
                        case_clause
                    ).orderby(
                        *agg_cols,
                        getattr(producer_timestep, 'Date').as_('date'),
                    )
                elif phase=='injectant':
                    query_fit = query_fit_base.select(
                        getattr(injector_timestep, 'Date').as_('date'),
                        *agg_cols,
                        case_clause,
                        fn.Sum(getattr(injector_timestep, f'{phase.capitalize()}RateP50')).as_(f'{phase}_rate_p50'),
                        fn.Sum(getattr(injector_timestep, f'{phase.capitalize()}RateP{p_lower}')).as_(f'{phase}_rate_p{p_lower}'),
                        fn.Sum(getattr(injector_timestep, f'{phase.capitalize()}RateP{p_upper}')).as_(f'{phase}_rate_p{p_upper}'),
                    ).groupby(
                        getattr(injector_timestep, 'Date').as_('date'),
                        *agg_cols,
                        case_clause
                    ).orderby(
                        *agg_cols,
                        getattr(injector_timestep, 'Date').as_('date'),
                    )                    
                else:
                    query_fit = query_fit_base.select(
                        getattr(producer_timestep, 'Date').as_('date'),
                        *agg_cols,
                        case_clause,
                        fn.Sum(getattr(producer_timestep, f'{phase.capitalize()}RateP50')).as_(f'{phase}_rate_p50'),
                        fn.Sum(getattr(producer_timestep, f'{phase.capitalize()}RateP{p_lower}')).as_(f'{phase}_rate_p{p_lower}'),
                        fn.Sum(getattr(producer_timestep, f'{phase.capitalize()}RateP{p_upper}')).as_(f'{phase}_rate_p{p_upper}'),
                    ).groupby(
                        getattr(producer_timestep, 'Date').as_('date'),
                        *agg_cols,
                        case_clause
                    ).orderby(
                        *agg_cols,
                        getattr(producer_timestep, 'Date').as_('date'),
                    )
                
        #If there are filters add them to the query
        filters_dict = {
            'WellAPI':prods+injs,
            'Reservoir':layers,
            'Compartment':comps,
            'FaultBlock':fbs
        }
        #iterate over the filters and add them to the query
        for k,f in filters_dict.items():
            #check if the filter is not empty to add filter to the query
            if len(f)>0:
                query_real = query_real.where(
                    getattr(completiondata,k).isin(f)
                )
                if show_fit:
                    query_fit = query_fit.where(
                        getattr(completiondata,k).isin(f)
                    )
                    
        # Call to the API    
        with httpx.Client(timeout=30) as client:
            query_real_str = query_real.get_sql()
            response_real = client.post(
                f'{api_url}/dataexplorer/query/tachyus',
                headers=headers,
                data=query_real_str
            )
            
            #If show fit is true, call the fit query
            if show_fit:
                query_fit_str = query_fit.get_sql()

                response_fit = client.post(
                    f'{api_url}/dataexplorer/query/tachyus',
                    headers=headers,
                    data=query_fit_str
                )
        #If the response is 200 of real data, create the dataframe
        if response_real.status_code == 200:
            data_real = response_real.json()
            df_real = pd.DataFrame(data_real)
            df_real = df_real.fillna('NA')
            df_real['date'] = pd.to_datetime(df_real['date'],format='%Y-%m-%d',exact=False)
        else:
            print(response_real.status_code)
            print(response_real.text)
        
        #If the response is 200 of fit data, create the dataframe
        if show_fit:
            if response_fit.status_code == 200:
                data_fit = response_fit.json()
                df_fit = pd.DataFrame(data_fit)
                df_fit = df_fit.fillna('NA')
                df_fit['date'] = pd.to_datetime(df_fit['date'],format='%Y-%m-%d',exact=False)
            else:
                print(response_fit.status_code)
                print(response_fit.text)
                raise PreventUpdate

        # Create the Traces of the plot
        list_traces = []
        list_rgba = []
        
        gr_group = df_real.groupby(gr_cols_real)
        gr_ngroups = gr_group.ngroups
        if gr_ngroups==1:
            actual_rgba = hex_to_rgba_str(actual_color,actual_alpha)
            list_rgba.append(actual_rgba)
        else:
            cmap = get_cmap(colormap,gr_ngroups)
            rgba_colors = ["rgba({},{},{},{})".format(*cmap(i,alpha=colormap_alpha)) for i in range(gr_ngroups)]
            list_rgba.extend(rgba_colors)
                            
        for i,(labels, dfi) in enumerate(gr_group):
            trace = go.Scatter(
                x = dfi['date'],
                y = dfi[phase],
                mode=actual_mode,
                name='-'.join(labels),
                hoverinfo='x+y+text',
                text = '-'.join(labels),
                line = {
                    'width':actual_width,
                    'dash':actual_linestyle,
                    'color':list_rgba[i],
                    'shape':actual_shape
                }
            )
            list_traces.append(trace)
            
            if len(second_props)>0:
                for prop in second_props:
                    trace_p = go.Scatter(
                        x = dfi['date'],
                        y = dfi[prop],
                        mode = 'lines',
                        name = '-'.join(labels) + f' {prop}',
                        hoverinfo= 'x+y',
                        yaxis = 'y2',
                        line = {
                            'width':1,
                            'dash':'solid',
                            'color':list_rgba[i],
                            'shape':'linear'
                        }
                    )
                    list_traces.append(trace_p)
            
            
        if show_fit:
            dict_color_type_fit = {
                'training':{
                    'color':fit_training_color,
                    'alpha':fit_training_alpha
                },
                'validation':{
                    'color':fit_validation_color,
                    'alpha':fit_validation_alpha
                }
            }
            gr_group_fit = df_fit.groupby(gr_cols_fit)
            gr_ngroups_fit = gr_group_fit.ngroups

            cmap_fit = get_cmap(colormap,gr_ngroups_fit)
                        
            for i,(labels, dfi_agg_fit) in enumerate(gr_group_fit):
                color_type_fit_dict = {
                    'training': f'rgba{cmap_fit(i,alpha=fit_training_alpha)}',
                    'validation': f'rgba{cmap_fit(i,alpha=fit_validation_alpha)}'
                }
                for type_fit, dfi_fit in dfi_agg_fit.groupby('type_of_fit'):
                    x_fit = np.concatenate([
                            dfi_fit['date'].values,
                            dfi_fit['date'].values[::-1]
                        ])
                        
                    y_fit = np.concatenate([
                        dfi_fit[f'{phase}_rate_p{p_lower}'].values,
                        dfi_fit[f'{phase}_rate_p{p_upper}'].values[::-1]
                    ])

                    fit_color = dict_color_type_fit[type_fit]['color']
                    fit_alpha = dict_color_type_fit[type_fit]['alpha']
                    
                    fit_rgba = hex_to_rgba_str(fit_color,fit_alpha)
                    fit_linecolor_rgba = hex_to_rgba_str(fit_line_color,fit_line_alpha)

                    trace_shadow = go.Scatter(
                        x = x_fit,
                        y = y_fit,
                        fill = 'toself',
                        fillcolor=fit_rgba if gr_ngroups_fit==1 else color_type_fit_dict[type_fit],
                        line_color=fit_linecolor_rgba,
                        showlegend=False,
                    )
                    list_traces.append(trace_shadow)
                
        
        layout = go.Layout(
            title = f'{phase.capitalize()} Fit',
            xaxis = {
                'title':'Date',
                'rangeslider':{
                    'visible':True
                },
                'rangeselector': dict(
                    buttons=list([
                        dict(count=1,
                            label="1y",
                            step="year",
                            stepmode="backward"),
                        dict(count=5,
                            label="5y",
                            step="year",
                            stepmode="backward"),
                        dict(count=10,
                            label="10y",
                            step="year",
                            stepmode="backward"),
                        dict(count=15,
                            label="15y",
                            step="year",
                            stepmode="backward"),
                        dict(count=10,
                            label="10YTD",
                            step="year",
                            stepmode="todate"),
                        dict(count=15,
                            label="15YTD",
                            step="year",
                            stepmode="todate"),
                        dict(step="all")
                    ])
                ),
            },
            yaxis = {
                'title':f'{phase.capitalize()} Rate',
                'type':y_scale
            },
            yaxis2 = {
                'title':'-'.join(second_props),
                'anchor':'x',
                'overlaying':'y',
                'side':'right',
            },
            margin={'l': 50, 'b': 50, 't': 50, 'r': 50},
            showlegend=True if gr_ngroups<20 else False,
            legend={'orientation':'h','yanchor':'bottom','y':-0.3, 'xanchor':'right','x':1},
        )
        return {
            'data': list_traces,
            'layout': layout
        }

    return func

for p in phases_dict:
    callback(
        Output(f'summary_plot_{p}','figure'),
        Input('summary_plot_accordion','active_item'),
        Input('case_name_store','data'),
        Input('summary_settings_producers_dropdown','value'),
        Input('summary_settings_injectors_dropdown','value'),
        Input('summary_settings_layers_dropdown','value'),
        Input('summary_settings_faultblocks_dropdown','value'),
        Input('summary_settings_compartments_dropdown','value'),
        Input('summary_settings_aggregation_checklist','value'),
        Input('summary_bhp_or_wellcount_switch','value'),
        Input('summary_settings_show_fit','value'),
        Input(f'summary_settings_{p}_yscale','value'),
        Input(f'summary_settings_{p}_units','value'),
        Input(f'summary_settings_{p}_actual_linestyle','value'),
        Input(f'summary_settings_{p}_actual_width','value'),
        Input(f'summary_settings_{p}_actual_shape','value'),
        Input(f'summary_settings_{p}_actual_mode','value'),
        Input(f'summary_settings_{p}_actual_color','value'),
        Input(f'summary_settings_{p}_actual_alpha','value'),
        Input(f'summary_settings_{p}_fit_percentiles','value'),
        Input(f'summary_settings_{p}_fit_training_color','value'),
        Input(f'summary_settings_{p}_fit_training_alpha','value'),
        Input(f'summary_settings_{p}_fit_validation_color','value'),
        Input(f'summary_settings_{p}_fit_validation_alpha','value'),
        Input(f'summary_settings_{p}_fit_line_color','value'),
        Input(f'summary_settings_{p}_fit_line_alpha','value'),
        Input(f'summary_settings_{p}_colormap','value'),
        Input(f'summary_settings_{p}_colormap_alpha','value')
    )(func_plot_data_fit(p))
# endregion
    
# region Crossplot Callbacks

@callback(
    Output('summary_crossplot','figure'),
    Input('summary_map_accordion','active_item'),
    Input('case_name_store','data'),
    Input('summary_settings_producers_dropdown','value'),
    Input('summary_settings_injectors_dropdown','value'),
    Input('summary_settings_layers_dropdown','value'),
    Input('summary_settings_faultblocks_dropdown','value'),
    Input('summary_settings_compartments_dropdown','value'),
    Input('summarycrossplot_settings_aggregation_checklist','value'),
    Input('summarycrossplot_settings_hue_checklist','value'),
    Input('summary_plot_accordion','active_item'),
    Input('summary_settings_crossplot_colormap','value'),
    Input('summary_settings_crossplot_colormap_alpha','value'),
    Input('summarycrossplot_checkbox_include_wells','value'),
    Input('summarycrossplot_checkbox_hideunselected','value')
)
def update_summary_cross_plot(
    active_item,
    data,
    prods,
    injs,
    layers,
    fbs,
    comps,
    agg,
    hue,
    phase,
    colormap,
    alpha,
    include_wells,
    hide_unselected
):
    if 'crossplot' not in active_item:
        raise PreventUpdate
    
    if phase is None:
        raise PreventUpdate
    
    hue = [h for h in hue if h in agg]
    
    case_name = data['case_name']
    #table objects
    productiondata = aqueon.productiondata
    completiondata = aqueon.completiondata
    fit_info = aqueon.fit_info
    producer_timestep = aqueon.producer_timestep
    injector_timestep = aqueon.injector_timestep
    
    #make the date column
    date_col = make_date(
        getattr(productiondata, 'Year'),
        getattr(productiondata, 'Month'),
        1
    ).as_('date')
    
    #actual query
    query_actual_base = PostgreSQLQuery.from_(
        productiondata
    ).left_join(
        completiondata
    ).on(
        (productiondata.WellAPI == completiondata.WellAPI) &
        (productiondata.casename == completiondata.casename) &
        (productiondata.CompSubId == completiondata.CompSubId)
    ).left_join(
        fit_info
    ).on(
        fit_info.casename == productiondata.casename
    ).where(
        getattr(productiondata, 'casename') == case_name
    ).where(
        getattr(fit_info,'BacktestEndDate') < date_col
    )
    
    # if actual query has no aggregation
    if len(agg)==0:
        agg_cols = [getattr(completiondata,i) for i in ['WellAPI','WellName','Reservoir']]
        join_agg = ['WellAPI','WellName','Reservoir']
    else:
        if include_wells:
            agg_cols = [getattr(completiondata,i) for i in agg+['WellAPI','WellName']]
            join_agg = agg+['WellAPI','WellName']
        else:
            agg_cols = [getattr(completiondata,i) for i in agg]
            join_agg = agg.copy()
    
    join_agg = list(set(join_agg))
    agg_cols = list(set(agg_cols))
    
    if phase == 'gross':
        query_actual = query_actual_base.select(
            *agg_cols,
            fn.Sum(
                (getattr(productiondata, phases_dict['oil']['db_column']) + getattr(productiondata, phases_dict['water']['db_column'])) * \
                #fn.Extract(DatePart.day,date_trunc(DatePart.month,date_col) + Interval(months=1) - Interval(days=1)) * 1e-3
                30.42 * 1e-3
            ).as_(f'actual_{phase}'),
            fn.Avg(getattr(completiondata,'Netpay')).as_('netpay')
        ).groupby(
            *agg_cols
        )
    else:
        query_actual = query_actual_base.select(
            *agg_cols,
            fn.Sum(
                getattr(productiondata, phases_dict[phase]['db_column']) * \
                #fn.Extract(DatePart.day,date_trunc(DatePart.month,date_col) + Interval(months=1) - Interval(days=1)) * 1e-3
                30.42 * 1e-3
            ).as_(f'actual_{phase}'),
            fn.Avg(getattr(completiondata,'Netpay')).as_('netpay')
        ).groupby(
            *agg_cols
        )
    
    #fit query
    fit_timestep = injector_timestep if phase=='injectant' else producer_timestep
    query_fit_base = PostgreSQLQuery.from_(
        fit_timestep
    ).where(
        getattr(fit_timestep, 'casename') == case_name
    ).left_join(
        completiondata
    ).on(
        (fit_timestep.WellId == completiondata.WellAPI) &
        (fit_timestep.casename == completiondata.casename) &
        (fn.Cast(fit_timestep.CompletionId,'INTEGER') == fn.Cast(completiondata.CompSubId,'INTEGER'))
    ).left_join(
        fit_info
    ).on(
        fit_timestep.casename == fit_info.casename
    ).where(
        getattr(fit_info,'BacktestEndDate') < getattr(fit_timestep, 'Date')
    )
    
    if phase=='water':
        query_fit = query_fit_base.select(
            *agg_cols,
            fn.Sum(
                (getattr(fit_timestep, 'GrossRateP50') - getattr(fit_timestep, 'OilRateP50')) * \
                #fn.Extract(DatePart.day,date_trunc(DatePart.month,getattr(fit_timestep,'Date')) + Interval(months=1) - Interval(days=1)) * 1e-3
                30.42 * 1e-3
            ).as_(f'fit_{phase}')
        ).groupby(
            *agg_cols
        )
    else:
        query_fit = query_fit_base.select(
            *agg_cols,
            fn.Sum(
                getattr(fit_timestep, f'{phase.capitalize()}RateP50') * \
                #fn.Extract(DatePart.day,date_trunc(DatePart.month,getattr(fit_timestep,'Date')) + Interval(months=1) - Interval(days=1)) * 1e-3
                30.42 * 1e-3
            ).as_(f'fit_{phase}')
        ).groupby(
            *agg_cols
        )
        
    filters_dict = {
        'WellAPI':prods+injs,
        'Reservoir':layers,
        'Compartment':comps,
        'FaultBlock':fbs
    }
    #iterate over the filters and add them to the query
    for k,f in filters_dict.items():
        #check if the filter is not empty to add filter to the query
        if len(f)>0:
            if hide_unselected:
                query_actual = query_actual.where(
                    getattr(completiondata,k).isin(f)
                )
        if len(f)>0:
            if hide_unselected:
                query_fit = query_fit.where(
                    getattr(completiondata,k).isin(f)
                )
                
    for k,f in filters_dict.items():
        #print(f'k: {k} f: {f}')
        if len(f)>0 and k in join_agg:
            case_selected = Case().when(
                getattr(completiondata,k).isin(f),True
            ).else_(False).as_(f'{k}_selected') 
            #print(f)
        else:
            case_selected = fn.LiteralValue(False).as_(f'{k}_selected')
        
        query_actual = query_actual.select(case_selected)
            
    query_join = PostgreSQLQuery.from_(
        query_actual.as_('actual')
    ).select(
        *[getattr(query_actual.as_('actual'),i) for i in join_agg],
        getattr(query_actual.as_('actual'),'WellAPI_selected'),
        getattr(query_actual.as_('actual'),'Reservoir_selected'),
        getattr(query_actual.as_('actual'),'FaultBlock_selected'),
        getattr(query_actual.as_('actual'),'Compartment_selected'),
        getattr(query_actual.as_('actual'),f'actual_{phase}'),
        getattr(query_fit.as_('fit'),f'fit_{phase}'),
        getattr(query_actual.as_('actual'),'netpay')
    ).inner_join(
        query_fit.as_('fit')
    ).using(
        *join_agg
    )
    #print(query_join.get_sql())
    with httpx.Client(timeout=30) as client:
        query_join_str = query_join.get_sql()
        response_actual = client.post(
            f'{api_url}/dataexplorer/query/tachyus',
            headers=headers,
            data=query_join_str
        )
        
    #If the response is 200 of real data, create the dataframe
    if response_actual.status_code == 200:
        data = response_actual.json()
        df = pd.DataFrame(data)
        df['netpay'] = df['netpay'].astype(str)
        #print(df.head())
    else:
        print(response_actual.status_code)
        print(response_actual.text)
        raise PreventUpdate
    
    #extract columns with selected filters
    selected_columns = [i for i in df.columns if i.endswith('_selected')]
    
    #check if there are selected filters
    sum_sel = df.loc[:,selected_columns].sum(axis=0)
    
    #extract the columns with selected filters
    list_selected_cols = sum_sel[sum_sel>0].index.tolist()
    
    if len(list_selected_cols)==0:
        df['is_selected'] = False
    else:
        df.loc[:,'is_selected'] = df.loc[:,list_selected_cols].all(axis=1)
    hue.append('is_selected')
    
    list_traces = []
    
    #group by the aggregation
    gr_df = df.groupby(hue)
    ngroups = gr_df.ngroups

    if ngroups==1:
        list_rgba_colors = [hex_to_rgba_str(phases_dict[phase]['actual_color'],alpha)]
    else:
        list_rgba_colors = [f'rgba{get_cmap(colormap,ngroups)(i,alpha)}' for i in range(ngroups)]
    
    cols_to_hover = join_agg+['netpay']
    
    #iterate over the groups
    for i,(labels,dfi) in enumerate(gr_df):
        is_selected = labels[-1]       
        rgba_color = list_rgba_colors[i]
        trace = go.Scatter(
            x = dfi[f'actual_{phase}'],
            y = dfi[f'fit_{phase}'],
            mode = 'markers',
            name = str(labels),
            text = dfi.loc[:,cols_to_hover].apply(lambda x: '<br>'.join(f"{col}: {val}" for col, val in x.items()), axis=1),
            hovertemplate='%{text}<br>Actual Cum: %{x:.2f}<br>Fit Cum: %{y:.2f}<extra></extra>',
            customdata = dfi[join_agg].to_dict('records'),
            marker = {
                'color':rgba_color,
                'size':10 if is_selected else 5,
                'symbol':'circle' if is_selected else 'circle-open',
                'line':{
                    #'color': 'orange' if is_selected else rgba_color,
                    'width': 2 if is_selected else 1
                }
            }
        )
        list_traces.append(trace)

    #add a trace with the 1:1 line
    trace_unit_slope = go.Scatter(
        x = [0,df[f'actual_{phase}'].max()],
        y = [0,df[f'actual_{phase}'].max()],
        mode = 'lines',
        showlegend=False,
        line = {
            'color':'black',
        }
    )
    list_traces.append(trace_unit_slope)
            
    #create the layout
    layout = go.Layout(
        title = f'{phase.capitalize()} Crossplot',
        xaxis = {
            'title':'Actual',
            'range': [0,df[f'actual_{phase}'].max()*1.2],
            'fixedrange':True
        },
        yaxis = {
            'title':'Predicted',
            #'scaleanchor':'x',
            #'scaleratio':1,
            'range': [0,df[f'fit_{phase}'].max()*1.2],
            'fixedrange':True
        },
        margin={'l': 50, 'b': 50, 'r': 50},
        legend={
            'orientation':'h',
            'yanchor':'bottom',
            'y':-0.3,  
        },
        showlegend= True if ngroups<11 else False,
        clickmode='event+select',
        height=600
        
    )
    return {
        'data': list_traces,
        'layout': layout
    }

@callback(
    Output('summary_settings_producers_dropdown','value',allow_duplicate=True),
    Output('summary_settings_injectors_dropdown','value',allow_duplicate=True),
    Output('summary_settings_layers_dropdown','value',allow_duplicate=True),
    Output('summary_settings_faultblocks_dropdown','value',allow_duplicate=True),
    Output('summary_settings_compartments_dropdown','value',allow_duplicate=True),
    Input('summary_crossplot','selectedData'),
    Input('summary_crossplot','clickData'),
    State('summary_settings_producers_dropdown','options'),
    State('summary_settings_injectors_dropdown','options'),
    State('summary_settings_producers_dropdown','value'),
    State('summary_settings_injectors_dropdown','value'),
    State('summary_settings_layers_dropdown','options'),
    State('summary_settings_faultblocks_dropdown','options'),
    State('summary_settings_compartments_dropdown','options'),
    State('summary_settings_layers_dropdown','value'),
    State('summary_settings_faultblocks_dropdown','value'),
    State('summary_settings_compartments_dropdown','value'),
    prevent_initial_call=True
)
def update_selection_from_crossplot(
    selected,
    clicked,
    prods_options,
    injs_options,
    prods,
    injs,
    layers_options,
    fbs_options,
    comps_options,
    layers,
    fbs,
    comps
):
    if selected is not None:
        points_selected = selected['points']
    else:
        points_selected = []
    
    if clicked is not None:
        points_clicked = clicked['points']
    else:
        points_clicked = []
        
    selected_click = points_selected + points_clicked
    if len(selected_click)>0:
        prod_selected = []
        inj_selected = []
        layers_selected = []
        fb_selected = []
        comp_selected = []
                
        list_prods = [i['value'] for i in prods_options]
        list_injs = [i['value'] for i in injs_options]
        list_layers = [i['value'] for i in layers_options]
        list_fbs = [i['value'] for i in fbs_options]
        list_comps = [i['value'] for i in comps_options]

        for p in selected_click:
            if 'WellAPI' in p['customdata']:
                if p['customdata']['WellAPI'] in list_prods:
                    prod_selected.append(p['customdata']['WellAPI'])
                elif p['customdata']['WellAPI'] in list_injs:
                    inj_selected.append(p['customdata']['WellAPI'])
                else:
                    pass
            if 'Reservoir' in p['customdata']:
                if p['customdata']['Reservoir'] in list_layers:
                    layers_selected.append(p['customdata']['Reservoir'])
            if 'FaultBlock' in p['customdata']:
                if p['customdata']['FaultBlock'] in list_fbs:
                    fb_selected.append(p['customdata']['FaultBlock'])
            if 'Compartment' in p['customdata']:
                if p['customdata']['Compartment'] in list_comps:
                    comp_selected.append(p['customdata']['Compartment'])
            else:
                pass
        

        return (
            np.unique(prod_selected + prods), 
            np.unique(inj_selected + injs),
            np.unique(layers_selected + layers),
            np.unique(fb_selected + fbs),
            np.unique(comp_selected + comps)
        )
    raise PreventUpdate
    
# endregion

# region ETL Callbacks
@callback(
    Output('etl_oil_cum','children'),
    Output('etl_water_cum','children'),
    Output('etl_gas_cum','children'),
    Output('etl_injectant_cum','children'),
    Output('etl_date_range','children'),
    Input('case_name_store','data')
)
def update_etl_oil_cum(data):
    case_name = data['case_name']
    
    #table objects
    productiondata = aqueon.productiondata

    date_col = make_date(
        getattr(productiondata, 'Year'),
        getattr(productiondata, 'Month'),
        1
    ).as_('date')

    query = PostgreSQLQuery.from_(
        productiondata
    ).select(
        fn.Min(date_col).as_('min_date'),
        fn.Max(date_col).as_('max_date'),
        fn.Sum(
            getattr(productiondata, phases_dict['oil']['db_column']) * \
            fn.Extract(DatePart.day,date_trunc(DatePart.month,date_col) + Interval(months=1) - Interval(days=1)) * \
            1e-6
        ).as_('oil_cum'),
        fn.Sum(
            getattr(productiondata, phases_dict['water']['db_column']) * \
            fn.Extract(DatePart.day,date_trunc(DatePart.month,date_col) + Interval(months=1) - Interval(days=1)) * \
            1e-6
        ).as_('water_cum'),
        fn.Sum(
            getattr(productiondata, phases_dict['gas']['db_column']) * \
            fn.Extract(DatePart.day,date_trunc(DatePart.month,date_col) + Interval(months=1) - Interval(days=1)) * \
            1e-6
        ).as_('gas_cum'),
        fn.Sum(
            getattr(productiondata, phases_dict['injectant']['db_column']) * \
            fn.Extract(DatePart.day,date_trunc(DatePart.month,date_col) + Interval(months=1) - Interval(days=1)) * \
            1e-6
        ).as_('injectant_cum')
    ).where(
        getattr(productiondata, 'casename') == case_name
    ).limit(1)
    
    query_str = query.get_sql()
    with httpx.Client(timeout=30) as client:
        response = client.post(
            f'{api_url}/dataexplorer/query/tachyus',
            headers=headers,
            data=query_str
        )
        
    if response.status_code == 200:
        data = response.json()
        sr = pd.DataFrame(data)
    else:
        print(response.status_code)
        print(response.text)
        raise PreventUpdate
    
    # Date Range Cumulative
    date_ranges = sr.at[0,'min_date'][:10] + ' to ' + sr.at[0,'max_date'][:10]
    
    #Cumulative values rounded to 2 decimals
    cum_list = sr[['oil_cum','water_cum','gas_cum','injectant_cum']].round(2).squeeze().values.tolist()
    return *cum_list,date_ranges

@callback(
    Output('etl_top_wells_producers','rowData'),
    Output('etl_top_wells_producers','columnDefs'),
    Input('case_name_store','data')
)
def update_etl_oil_cum(data):
    case_name = data['case_name']
    
    #table objects
    productiondata = aqueon.productiondata
    completiondata = aqueon.completiondata

    date_col = make_date(
        getattr(productiondata, 'Year'),
        getattr(productiondata, 'Month'),
        1
    ).as_('date')

    sum_oil = fn.Sum(
            getattr(productiondata, phases_dict['oil']['db_column']) * \
            fn.Extract(DatePart.day,date_trunc(DatePart.month,date_col) + Interval(months=1) - Interval(days=1)) * \
            1e-3
    ).as_('oil_cum')
    query = PostgreSQLQuery.from_(
        productiondata
    ).select(
        getattr(completiondata,'WellName'),
        sum_oil
    ).where(
        getattr(productiondata, 'casename') == case_name
    ).left_join(
        completiondata
    ).on(
        (productiondata.WellAPI == completiondata.WellAPI) &
        (productiondata.casename == completiondata.casename) &
        (productiondata.CompSubId == completiondata.CompSubId)
    ).groupby(
        getattr(completiondata,'WellName')
    ).orderby(
        sum_oil, order=Order.desc
    ).limit(10)
    
    query_str = query.get_sql()
    with httpx.Client(timeout=30) as client:
        response = client.post(
            f'{api_url}/dataexplorer/query/tachyus',
            headers=headers,
            data=query_str
        )
        
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data).round(2)
    else:
        print(response.status_code)
        print(response.text)
        raise PreventUpdate

    return df.to_dict('records'),[{'field':i,'headerName':i} for i in df.columns]

@callback(
    Output('etl_top_layers_producers','rowData'),
    Output('etl_top_layers_producers','columnDefs'),
    Input('case_name_store','data')
)
def update_etl_oil_cum(data):
    case_name = data['case_name']
    
    #table objects
    productiondata = aqueon.productiondata
    completiondata = aqueon.completiondata

    date_col = make_date(
        getattr(productiondata, 'Year'),
        getattr(productiondata, 'Month'),
        1
    ).as_('date')

    sum_oil = fn.Sum(
            getattr(productiondata, phases_dict['oil']['db_column']) * \
            fn.Extract(DatePart.day,date_trunc(DatePart.month,date_col) + Interval(months=1) - Interval(days=1)) * \
            1e-3
    ).as_('oil_cum')
    
    query = PostgreSQLQuery.from_(
        productiondata
    ).select(
        getattr(completiondata,'Reservoir'),
        sum_oil
    ).where(
        getattr(productiondata, 'casename') == case_name
    ).left_join(
        completiondata
    ).on(
        (productiondata.WellAPI == completiondata.WellAPI) &
        (productiondata.casename == completiondata.casename) &
        (productiondata.CompSubId == completiondata.CompSubId)
    ).groupby(
        getattr(completiondata,'Reservoir')
    ).orderby(
        sum_oil, order=Order.desc
    ).limit(10)
    
    query_str = query.get_sql()
    with httpx.Client(timeout=30) as client:
        response = client.post(
            f'{api_url}/dataexplorer/query/tachyus',
            headers=headers,
            data=query_str
        )
        
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data).round(2)
    else:
        print(response.status_code)
        print(response.text)
        raise PreventUpdate

    return df.to_dict('records'),[{'field':i,'headerName':i} for i in df.columns]
# endregion

# endregion



# endregion

