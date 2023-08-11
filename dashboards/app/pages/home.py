import dash
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(
    __name__, 
    path='/',
    redirect_from=['/home']
)

def layout():
    return html.Div(
    dbc.Container(
        [
            html.H1("Tachyus Visualization Dashboard", className="display-3"),
            html.P(
                children = """
                    The dashboard is a web-based tool that offers a 
                    clear and organized view of Aqueon Results. Users can examine 
                    historical data, examine data fits and compare different "what-if" scenarios. 
                    Developed using Dash technology, the dashboard is regularly updated with 
                    new features. The main goal of the dashboard is to provide a user-friendly 
                    interface for reviewing and analyzing Aqueon Results, making it an invaluable 
                    resource for those working with this data.
                    """,
                className='lead'
            ),
            html.Hr(className="my-2"),
            html.P(
                "It supports Aqueon & Strateon Inputs and Outputs"
            )
        ],
        fluid=True,
        className="py-3",
    ),
    className="p-3 bg-light rounded-3",
)