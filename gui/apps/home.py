import dash
from dash import dcc
from dash.dependencies import Input, Output, State, MATCH, ALL
import json
import os
#from config import get_config
import numpy as np
from dash import html
import xml.etree.ElementTree as ET
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
import pymysql.cursors
from app import app


def get_config():

    db_host = '192.168.166.79'
    db_user = 'gammaflash'
    db_pass = os.environ["DB_PASS"]
    db_port = '3306'
    db_results = 'gammaflash_test'
    db_logs = ''

    redis_port = ''

    #xml_config = ""
    xml_config=""

    return {'db_host':db_host,'db_user':db_user,
    'db_pass':db_pass,'db_port':db_port,'db_results':db_results,'db_logs':db_logs,'xml_config':xml_config}

conf_dict = get_config()


#app = dash.Dash(prevent_initial_callbacks=True, external_stylesheets=[dbc.themes.BOOTSTRAP])

#server = app.server

colors = {
    'background': '#111111',
    'navbar': '#4d4d4d',
    'text': '#7FDBFF'
    }


def bar_plot(index, name, className, y):
    x= np.arange(1000)
    return dcc.Graph(
        id={"type":"bar","index":str(index)},
        className=className,
        figure={
            'data': [
                dict(x=x, y=y, type='bar', name=name+" "+str(index)),
            ],
            'layout': {
                'plot_bgcolor': colors['background'],
                 'paper_bgcolor': colors['background'],
                'title': 'bar_chart '+str(index),
                'yaxis': {
                "type": "log"

                },
                'font': {
                    'color': colors['text']
                }
            }
        }
    )

def line_plot(index, name, className, y):
    x=np.arange(300)
    return dcc.Graph(
        id={"type":"line","index":str(index)},
        className=className,
        figure= {
            'data': [dict(
                x=x,
                y=y,
                mode='lines'
            )],
            'layout': {
                #'margin': {'l': 20, 'b': 30, 'r': 10, 't': 10},
                'yaxis': {'type': 'linear'},
                'plot_bgcolor': colors['background'],
                'paper_bgcolor': colors['background'],
                'title': 'time series',
                'xaxis': {'showgrid': False},
                "height" : 300,
                'font': {
                    'color': colors['text']
                }
            }
        })


def load_data():

    conn = pymysql.connect(host=conf_dict["db_host"], user=conf_dict["db_user"], password=conf_dict["db_pass"], db=conf_dict["db_results"],port=int(conf_dict["db_port"]), cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    cursor.execute("select * from gftable")
    results = cursor.fetchall()

    cursor.execute(f"SELECT waveform FROM gammaflash_test.waveform_dl1 where RedpitayaID=1;")
    resultswf = cursor.fetchall()

    cursor.close()
    conn.close()

    data_json = json.loads(resultswf[0]["waveform"])


    d = {}
    for r in results:
        key = r["RedpitayaID"]
        r["Bars"] = json.loads(r["Bars"])

        d[key] = r["Bars"]

    return d, data_json
"""
def load_data_wf():

    conn = pymysql.connect(host=conf_dict["db_host"], user=conf_dict["db_user"], password=conf_dict["db_pass"], db=conf_dict["db_results"],port=int(conf_dict["db_port"]), cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()
    query = f"SELECT waveform FROM gammaflash_test.waveform_dl1 where RedpitayaID=1;"
    cursor.execute(query)
    results = cursor.fetchall()

    cursor.close()
    conn.close()
    data_json = json.loads(results[0]["waveform"])

    return(data_json)
"""

def load_view(mysql=True):

    if mysql:
        conn = pymysql.connect(host=conf_dict["db_host"], user=conf_dict["db_user"], password=conf_dict["db_pass"], db=conf_dict["db_results"],port=int(conf_dict["db_port"]), cursorclass=pymysql.cursors.DictCursor)
        cursor = conn.cursor()

        cursor.execute("select content from xml where name = 'views' ")
        views_xml = cursor.fetchone()['content']

        cursor.execute("select content from xml where name = 'graphs' ")
        graphs_xml = cursor.fetchone()['content']

        cursor.execute("select content from xml where name = 'graph_types' ")
        graph_types_xml = cursor.fetchone()['content']

        cursor.close()
        conn.close()

        #parse views_xml
        views_xml_root = ET.fromstring(views_xml)
        #parse graphs_xml
        graphs_xml_root = ET.fromstring(graphs_xml)
        #parse graph_types_xml
        graph_types_xml_root = ET.fromstring(graph_types_xml)
    else:
        #search local files in a folder
        graphs_tree = ET.parse('xmls/graphs.xml')
        graphs_xml_root = graphs_tree.getroot()
        
        views_tree = ET.parse("xmls/views.xml")
        views_xml_root = views_tree.getroot()

        graph_types_tree = ET.parse("xmls/views.xml")
        graph_types_root = graph_types_tree.getroot()


    row_list = []

    for view in views_xml_root.iter('view'):
        if(view.attrib['name']=="view1"):
            for row in view.iter('row'):
                row_id = row.attrib['id']
                cols = []
                for col in row.iter('col'):
                    graph = col.find('graph')
                    graph_name = graph.attrib['name']
                    col_class = col.attrib['class']
                    col_id = col.attrib['id']
                    interval = graph.attrib['interval']
                    graphID = graph.attrib["id"]
                    redpitayaID = graph.attrib["redpitayaID"]

                    #get info from other xml
                    for graph_object in graphs_xml_root.iter('graph'):
                        if(graph_object.attrib['name']==graph_name):
                            #print(graph_object.attrib)
                            graph_type = graph_object.attrib['type']
                            graph_field = graph_object.attrib['field']
                            graph_datatype = graph_object.attrib['datatype']

                    #for graph_type_object in graph_types_xml_root.iter('graphtype'):
                    #    if(graph_type_object.attrib['name']==graph_type):
                    #        print(graph_type_object.attrib)

                    cols.append({'col_id':col_id,'col_class':col_class,'graph_name':graph_name,'graph_type':graph_type,'graph_field':graph_field,'graph_datatype':graph_datatype,'graph_interval':interval, "graph_id":graphID, "redpitayaID":redpitayaID})
                row_list.append({'row_id':row_id,'row_columns':cols})
    return row_list

def start_view(rows, data):
    ####------ preparing plots----######
    div_children = []
    count = 0
    for i in rows:
        row_plot = []
        #row_plot.append(html.Button(id='123', n_clicks=0))
        for j in i["row_columns"]:
            if j["graph_type"] == "histogram":
                #plot = 0
                plot = bar_plot(index=j["redpitayaID"], name=j["graph_name"], className=j["col_class"], y=np.zeros((1000,), dtype=int))
                interval = dcc.Interval(id={"type":"interval","index":j["redpitayaID"]}, interval=int(j['graph_interval'])*1000, n_intervals=0,)
                intervals.append(interval)

            if j["graph_type"] == "line":
                plot = line_plot(index=j["redpitayaID"], name=j["graph_name"], className=j["col_class"], y=0)
                #interval = dcc.Interval(id={"type":"interval-line","index":j["redpitayaID"]+"_line"}, interval=int(j['graph_interval'])*1000, n_intervals=0,)
                #intervals.append(interval)
            count += 1
            row_plot.append(plot)


        div = html.Div(id="row_"+str(i), className="row", children=row_plot)
        div_children.append(div)
    return div_children

#fig = px.bar(load_data(), x="Amplitude [mV]", y="Counts", barmode="group", log_y=True)
"""
fig.update_layout(
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    font_color=colors['text']
)
"""

####-----loading views----#####
rows = load_view(mysql=False)
####-----loading data-----#####
data = load_data()
intervals = []


div_children = start_view(rows, data)
print(intervals)


layout = html.Div(style={'backgroundColor': colors['background']}, children=[


    html.Div(children=[

    html.Nav(id="navbar", className="navbar fixed-top navbar-expand-lg", children=[
        html.A("Home", className="nav-link", href="/apps/home"),
        html.A("Housekeeping", className="nav-link", href="/apps/housekeeping"),
        ], style={
                'backgroundColor': colors['navbar']
            }),
    ], style={
            "margin-bottom": "50px"
        }),

    html.Div(id="view1", children=div_children),

    html.Div(id="interval_container", children=intervals)


])

"""
    html.Div(id="buttons", className="btn-toolbar justify-content-center", children=[
        html.Button('START', className="btn btn-success mr-3", id='btn-nclicks-1', n_clicks=0),
        dcc.Input(id='input-on-submit', type='text', className="mr-3", size="5"),
        html.Button('STOP', className="btn btn-danger ", id='btn-nclicks-2', n_clicks=0)
    ]),
"""

################---CALLBACKS---##############
@app.callback(
    Output({"type":"bar", "index": MATCH}, "figure"),
    Output({"type":"line", "index": MATCH}, "figure"),
    [Input({"type":"interval",'index': MATCH}, 'n_intervals')],
    [State({'type': 'bar', 'index': MATCH}, 'figure'),
    State({'type': 'line', 'index': MATCH}, 'figure')]
    )
def update_bars(n, figure_bar, figure_line):
    data, datawf = load_data()

    figure_line["data"][0]["x"] = datawf["x"]
    figure_line["data"][0]["y"] = datawf["y"]

    y_distribution = data[0]["y_distribution"]
    figure_bar["data"][0]["y"] = y_distribution
    return figure_bar, figure_line