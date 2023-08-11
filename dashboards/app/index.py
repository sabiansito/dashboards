
from app import app, server
from dash import page_container, page_registry
import dash_bootstrap_components as dbc
app.title = 'Tachyus Dashboards'

app.layout = dbc.Container(
    children=[
        dbc.NavbarSimple(
            children=[
                dbc.NavItem(
                    dbc.NavLink(
                        f'{page["name"]}',
                        href=f'{page["relative_path"]}'
                    )
                ) for page in page_registry.values()
            ],
            brand='Tachyus Dashboards',
            color='primary',
            dark=True,
            sticky='top',
            fluid=True
        ),
        page_container
    ],
    fluid=True
)

if __name__ == '__main__':
    app.run_server(debug=True, port=8080, host='0.0.0.0')