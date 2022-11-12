import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app import app
from apps import home, archive_view


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])
app.config.suppress_callback_exceptions = True


@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/apps/home':
        return home.layout
    elif pathname == '/apps/archive_view':
        return archive_view.layout
    else:
        return '404'

if __name__ == '__main__':
    app.run_server(debug=True)