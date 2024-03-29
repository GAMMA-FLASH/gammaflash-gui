import os
import glob
import json
import dash
import numpy as np
from skimage import io
from pathlib import Path
from app import app
import pandas as pd
from dash import dcc
from dash import html
import pymysql.cursors
from operator import add
import plotly.express as px
import plotly.graph_objects as go
import xml.etree.ElementTree as ET
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta, timezone
from dash.dependencies import Input, Output, State, MATCH, ALL
#from config import get_config


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


def bar_plot(index, extraparam, name, className, y):  #extraparam is the data interval to get data
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
		}
            }
        }
    )

def line_plot(index, extraparam, name, className, y): #extraparam is the data interval to get data
    x=pd.date_range(start='1/1/2018', periods=8)
    return dcc.Graph(
        id={"type":"line","index":str(index)},
        className=className,
        figure= {
            'data': [dict(
                x=x,
                y=np.arange(8),
                error_y=dict(type='data', array=np.arange(8)),
                mode='markers', customdata=extraparam
            )],
            "layout": {"title": {"text": ""}, 'xaxis': {
		'title': "Date"
		},
        'yaxis': {
		'title': "Counts"
		}}
            
        }
        )

def plot_image(index, name, className, extraparam): #extraparam is the directory where the images are stored

    list_of_files = glob.glob(f'{extraparam}/*.jpg') # * means all if need specific format then *.csv
    latest_file = max(list_of_files, key=os.path.getctime)

    print(latest_file)
    
    img = io.imread(latest_file)
    fig = px.imshow(img, title=latest_file)
    
    return dcc.Graph(
        id={"type":"image","index":str(index)},
        figure = fig,
    )


def plot_image_json(index, name, className):

    latest_file = load_image_json()
    
    
    img = io.imread(latest_file)
    fig = px.imshow(img, title=latest_file)
    
    return dcc.Graph(
        id={"type":"image","index":str(index)},
        figure = fig,
    )


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

def load_image_json():
    
    conn = pymysql.connect(host=conf_dict["db_host"], user=conf_dict["db_user"], password=conf_dict["db_pass"], db=conf_dict["db_results"],port=int(conf_dict["db_port"]), cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()

    time_slot = (datetime.now(timezone.utc)).strftime("%Y-%m-%d %H:%M:%S")
    
    query = f"select * from gammaflash_test.images order by insert_time desc limit 1;"
    #print(query)
    #Get line data
    cursor.execute(query)

    results = cursor.fetchall()

    res = json.loads(results[0]["data"])

    image = res["image"]

    return image



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
        #row_plot.append(html.Button(id='123', n_clicks=0))
        for j in i["row_columns"]:
            if j["graph_type"] == "histogram":
                #plot = 0
                plot = bar_plot(index=j["graph_id"], extraparam=j["extraparam"], name=j["graph_name"], className=j["col_class"], y=np.zeros((1000,), dtype=int))
                interval = dcc.Interval(id={"type":"interval","index":j["graph_id"]}, interval=int(j['graph_interval'])*1000, n_intervals=0,)
                intervals.append(interval)

            if j["graph_type"] == "line":
                plot = line_plot(index=j["graph_id"], extraparam=j["extraparam"], name=j["graph_name"], className=j["col_class"], y=0)
                interval = dcc.Interval(id={"type":"interval-line","index":j["graph_id"]}, interval=int(j['graph_interval'])*1000, n_intervals=0,)
                intervals.append(interval)
            
            if j["graph_type"] == "image":
                plot = plot_image(index=j["graph_id"], name=j["graph_name"], className=j["col_class"], extraparam=j["extraparam"])
                interval = dcc.Interval(id={"type":"interval-image","index":j["graph_id"]}, interval=int(j['graph_interval'])*1000, n_intervals=0,)
                intervals.append(interval)

            if j["graph_type"] == "image-json":
                plot = plot_image_json(index=j["graph_id"], name=j["graph_name"], className=j["col_class"])
                interval = dcc.Interval(id={"type":"interval-image-json","index":j["graph_id"]}, interval=int(j['graph_interval'])*1000, n_intervals=0,)
                intervals.append(interval)

            count += 1
            row_plot.append(plot)


        div = html.Div(id="row_"+str(i), className="row", children=row_plot)
        div_children.append(div)
    return div_children

####-----loading views----#####
rows = load_view(mysql=False)
intervals = []


div_children = start_view(rows)
#print(intervals)


layout = html.Div( children=[


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

    html.Div(id="view1", children=div_children),

    html.Div(id="interval_container", children=intervals)


])

################---CALLBACKS---##############

@app.callback(
    Output({"type":"bar", "index": MATCH}, "figure"),
    [Input({"type":"interval",'index': MATCH}, 'n_intervals')],
    [State({'type': 'bar', 'index': MATCH}, 'figure'),
    State({'type': 'bar', 'index': MATCH}, 'id')]
    )
def update_bars(n, figure_bar, barid):
    
    bars= load_bar(barid["index"], pasttime=int(figure_bar["data"][0]["customdata"]))

    figure_bar["data"][0]["x"] = bars["x"]
    figure_bar["data"][0]["y"] = bars["y"]
    figure_bar["layout"]["title"] = bars["title"]
    #print(figure_bar)

    return figure_bar


@app.callback(
    Output({"type":"line", "index": MATCH}, "figure"),
    [Input({"type":"interval-line",'index': MATCH}, 'n_intervals')],
    [State({'type': 'line', 'index': MATCH}, 'figure'),
    State({'type': 'line', 'index': MATCH}, 'id')]
    )
def update_lines(n, figure_line, lineid):

    lines = load_line(lineid["index"], pasttime=int(figure_line["data"][0]["customdata"]))
    figure_line["data"][0]["x"] = lines["x"]
    figure_line["data"][0]["y"] = lines["y"]
    figure_line["data"][0]["error_y"]["array"] = lines["y_err"]
    figure_line["layout"]["title"]["text"] = lines["title"]
    figure_line["layout"]["xaxis"]["title"]["text"] = lines["xlabel"]
    figure_line["layout"]["yaxis"]["title"]["text"] = lines["ylabel"]
    print(figure_line["layout"])
    return figure_line


@app.callback(
    Output({"type":"image", "index": MATCH}, "figure"),
    [Input({"type":"interval-image",'index': MATCH}, 'n_intervals')],
    [State({'type': 'image', 'index': MATCH}, 'figure'),
    State({'type': 'image', 'index': MATCH}, 'id')]
    )
def update_image(n, figure_image, barid):
    
    #get the pathfile
    pathfile = figure_image["layout"]["title"]["text"]
    pathfile = Path(pathfile)
    pathfile = pathfile.parent

    print(pathfile)


    list_of_files = glob.glob(f'{str(pathfile)}/*.jpg')
    latest_file = max(list_of_files, key=os.path.getctime)

    img = io.imread(latest_file)
    fig = px.imshow(img, title=latest_file)


    return fig

@app.callback(
    Output({"type":"image-json", "index": MATCH}, "figure"),
    [Input({"type":"interval-image-json",'index': MATCH}, 'n_intervals')],
    [State({'type': 'image-json', 'index': MATCH}, 'figure'),
    State({'type': 'image-json', 'index': MATCH}, 'id')]
    )
def update_image(n, figure_image, barid):
    
    latest_file = load_image_json()

    img = io.imread(latest_file)
    fig = px.imshow(img)


    return fig