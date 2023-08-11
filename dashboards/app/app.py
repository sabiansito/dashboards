import dash
import dash_bootstrap_components as dbc

app = dash.Dash(
    __name__,
    use_pages=True,
	external_stylesheets=[dbc.themes.BOOTSTRAP,dbc.icons.FONT_AWESOME],
)

server = app.server
app.config.suppress_callback_exceptions = True
