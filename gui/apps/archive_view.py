import dash
from dash import dcc
from dash.dependencies import Input, Output, State, MATCH, ALL
import json
import os
from datetime import datetime, timedelta, timezone
#from config import get_config
import numpy as np
from dash import html
import xml.etree.ElementTree as ET
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
import pymysql.cursors
from app import app
from datetime import date
from operator import add


def get_config():

    db_host = '127.0.0.1'
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


def bar_plot(index, extraparam, name, className, y):
    x= np.arange(1000)
    return dcc.Graph(
        id={"type":"bar","index":str(index)},
        className=className,
        figure={
            'data': [
                dict(x=x, y=y, type='bar', name=name+" "+str(index), customdata=extraparam),
            ],
            'layout': {
                'title': 'bar_chart '+str(index),
                'yaxis': {
                "type": "log",
		'title': "counts"

                },
		'xaxis': {
		'title': "channels"
		},
                'font': {
                    'color': colors['text']
                }
            }
        }
    )

def line_plot(index, extraparam, name, className, y):
    x=np.arange(300)
    return dcc.Graph(
        id={"type":"line","index":str(index)},
        className=className,
        figure= {
            'data': [dict(
                x=x,
                y=y,
                error_y=dict(type='data', array=np.arange(300)),
                mode='markers', customdata=extraparam
            )]
        })


def load_bar(instrument_barid, pasttime=30):
    #print(f"instrument ids are {instrument_barid} and {instrument_lineid}")

    conn = pymysql.connect(host=conf_dict["db_host"], user=conf_dict["db_user"], password=conf_dict["db_pass"], db=conf_dict["db_results"],port=int(conf_dict["db_port"]), cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()

    #gettimeslot
    time_slot = (datetime.now(timezone.utc) - timedelta(minutes = pasttime)).strftime("%Y-%m-%d %H:%M:%S")

    query = f"SELECT insert_time, `type`, `data`, tstart, tend FROM gammaflash_test.gui_spectra where type='{instrument_barid}' and tstart > '{time_slot}';"
    #print(query)
    #Get bar data
    cursor.execute(query)
    results = cursor.fetchall()
    #print(f"results_row: {len(results)}")

    #process x and y, get the first element to initialize the arrays
    res = json.loads(results[0]["data"])
    title = res["title"]
    xlabel = res["xlabel"]
    ylabel = res["ylabel"]

    x_results = res["x"]
    y_results = res["y"]
    for result in results[1:]:
        res = json.loads(result["data"])
        if x_results[-1] == res["x"][-1]: #check if the last bin is equal
            y_results = list(map(add, y_results, res["y"]) )
    
    results_bar = {"title" : title, "xlabel": xlabel, "ylabel": ylabel, 
            "x": x_results,
            "y": y_results,
            "tstart":f"{results[0]['tstart']}",
            "tend": f"{results[-1]['tend']}"
            }
    return results_bar

def load_line(instrument_lineid, pasttime=30):

    conn = pymysql.connect(host=conf_dict["db_host"], user=conf_dict["db_user"], password=conf_dict["db_pass"], db=conf_dict["db_results"],port=int(conf_dict["db_port"]), cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()

    #gettimeslot
    time_slot = (datetime.now(timezone.utc) - timedelta(minutes = pasttime)).strftime("%Y-%m-%d %H:%M:%S")
    
    query = f"SELECT insert_time, `type`, `data`, tstart, tend FROM gammaflash_test.gui_lc where type='{instrument_lineid}' and tstart > '{time_slot}';"
    #print(query)
    #Get line data
    cursor.execute(query)

    results = cursor.fetchall()
    #print(f"results_row: {len(results)}")

    res = json.loads(results[0]["data"])
    title = res["title"]
    xlabel = res["xlabel"]
    ylabel = res["ylabel"]
    mode = res["mode"]

    y_merged = res["y"]
    y_err_merged = res["y_err"]
    x_merged = res["x"]
    
    for result in results[1:]:
        res = json.loads(result["data"])

        if x_merged[-1] == res["x"][0]:
            _ = x_merged.pop()
            x_merged += res["x"]

            res["y"][0] += y_merged[-1]
            res["y_err"][0] = np.sqrt(res["y"][0])
            _ = y_merged.pop()
            _ = y_err_merged.pop()
            y_merged += res["y"]
            y_err_merged += res["y_err"]

    results_line = {"title" : title, "xlabel": xlabel, "ylabel": ylabel, "mode": mode,
            "x": x_merged,
            "y": y_merged,
            "y_err": y_err_merged,
            "tstart":f"{results[0]['tstart']}",
            "tend": f"{results[-1]['tend']}"
            }

    return results_line

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
        if(view.attrib['name']=="archive_view"):
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
                    extraparam = graph.attrib["extraparam"]

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

                    cols.append({'col_id':col_id,'col_class':col_class,'graph_name':graph_name,'graph_type':graph_type,'graph_field':graph_field,'graph_datatype':graph_datatype,'graph_interval':interval, "graph_id":graphID, "extraparam":extraparam})
                row_list.append({'row_id':row_id,'row_columns':cols})
    return row_list

def start_view(rows):
    ####------ preparing plots----######
    div_children = []
    count = 0

    for i in rows:
        row_plot = []
        for j in i["row_columns"]:
            if j["graph_type"] == "histogram":
                #plot = 0
                plot = bar_plot(index=j["graph_id"], extraparam=j["extraparam"], name=j["graph_name"], className=j["col_class"], y=np.zeros((1000,), dtype=int))
                #interval = dcc.Interval(id={"type":"interval","index":j["graph_id"]}, interval=int(j['graph_interval'])*1000, n_intervals=0,)
                #intervals.append(interval)

            if j["graph_type"] == "line":
                plot = line_plot(index=j["graph_id"], extraparam=j["extraparam"], name=j["graph_name"], className=j["col_class"], y=0)
                #interval = dcc.Interval(id={"type":"interval-line","index":j["graph_id"]}, interval=int(j['graph_interval'])*1000, n_intervals=0,)
                #intervals.append(interval)
            count += 1
            row_plot.append(plot)


        div = html.Div(id="row_"+str(i), className="row", children=row_plot)
        div_children.append(div)
    return div_children

####-----loading views----#####
rows = load_view(mysql=False)
intervals = []

datepicker = dcc.DatePickerRange(id='my-date-picker-range', initial_visible_month=date(2022, 6, 1))


div_children = start_view(rows)
#print(intervals)


layout = html.Div(style={'backgroundColor': colors['background']}, children=[


    html.Div(children=[

    html.Nav(id="navbar", className="navbar fixed-top navbar-expand-lg", children=[
        html.A("Home", className="nav-link", href="/apps/home"),
        html.A("Archive View", className="nav-link", href="/apps/archive_view"),
        ], style={
                'backgroundColor': colors['navbar']
            }),
    ], style={
            "margin-bottom": "50px"
        }),
    

    html.Div(id="datepicker", children=datepicker),

    html.Div(id="view1", children=div_children)



])



"""
################---CALLBACKS---##############
@app.callback(
    [Output({"type":"bar", "index": ALL}, "figure"),
    Output({"type":"line", "index": ALL}, "figure")],
    [Input('my-date-picker-range', 'start_date'),
    Input('my-date-picker-range', 'end_date')]
    )
def update_bars(start_date, end_date, bar_figure, barid, line_figure, lineid):

    if start_date and end_date is not None:
        print(f"callback! {start_date} {end_date} {barid} {lineid}")

    return bar_figure, line_figure



@app.callback(
    Output({"type":"bar", "index": MATCH}, "figure"),
    [Input('my-date-picker-range', 'start_date'),
    Input('my-date-picker-range', 'end_date'))],
    [State({'type': 'bar', 'index': MATCH}, 'figure'),
    State({'type': 'bar', 'index': MATCH}, 'id')]
    )
def update_bars(n, figure_bar, barid):
    
    bars= load_bar(barid["index"], pasttime=int(figure_bar["data"][0]["customdata"]))

    figure_bar["data"][0]["x"] = bars["x"]
    figure_bar["data"][0]["y"] = bars["y"]
    #print(figure_bar)

    return figure_bar


@app.callback(
    Output({"type":"line", "index": MATCH}, "figure"),
    [Input({"type":"interval-line",'index': MATCH}, 'n_intervals')],
    [State({'type': 'line', 'index': MATCH}, 'figure'),
    State({'type': 'line', 'index': MATCH}, 'id')]
    )
def update_lines(n, figure_line, lineid):


    #print(figure_line, lineid)
    
    lines = load_line(lineid["index"], pasttime=int(figure_line["data"][0]["customdata"]))
    figure_line["data"][0]["x"] = lines["x"]
    figure_line["data"][0]["y"] = lines["y"]
    figure_line["data"][0]["error_y"]["array"] = lines["y_err"]
    print(figure_line["data"][0]["customdata"])
    #print(figure_line)
    return figure_line

"""