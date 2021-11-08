import dash
import dash_bootstrap_components as dbc

app = dash.Dash(__name__,prevent_initial_callbacks=True,external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
