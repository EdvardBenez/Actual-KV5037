#Author: Marcel Majtyka (24005777), Harvey Tinkler (23017915)
#Used https://realpython.com/python-dash/ , https://dash.plotly.com/live-updates , https://dash.plotly.com/basic-callbacks  as a reference.
#Libraries
from dash import Dash, dcc, html, Input, Output  #Dash used for dashboard
import sqlite3  #For DB reading
import pandas as pd  #For data analysis
import numpy as np #For rounding
import plotly.express as px  #For plotting
import os
from login import app as server, create_users_table
from checkDB import createDB
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'detections.db')

#Colour platate changer
COLOUR_HEADER_BG = "#444441"
COLOUR_HEADER_TEXT = "#D3D1C7"
COLOUR_CARD_BG = "#F1EFE8"
COLOUR_CARD_LABEL = "#5F5E5A"
COLOUR_CARD_VALUE = "#444441"
COLOUR_PAGE_BG = "#f5f4f0"
COLOUR_CHART = "#888780"
COLOUR_BORDER = "#D3D1C7"

#Function Files
from liveCount import calc_live_count
from todayCount import calc_today_count
from peakHour import calc_peak_hour

#Funct to plot the hourly entries scatter graph
def plot_graph(days):
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM Detections", con)
    con.close()

    #Converting TimeStamp, removing 'unknown' direction, and only getting entries
    df['Time'] = pd.to_datetime(df["timeStamp"])

    #Calculating cutoff date using selected days
    cutoff_date = datetime.now() - timedelta(days=days)
    df = df[df['Time'] >= cutoff_date]
    
    df = df[df['direction'].isin(['in', 'out'])]
    dfIn = df[df['direction'] == 'in']

    #Grouping entries by hour (with full time range so graph isn't blank)

    if dfIn.empty:
        return px.line(title="No data available for selected period")

    # Round timestamps to hour boundaries
    start = dfIn['Time'].min().floor('h')
    end = dfIn['Time'].max().ceil('h')

    time_range = pd.date_range(start=start, end=end, freq='h')

    dfGroupped = dfIn.groupby(
        pd.Grouper(key='Time', freq='h')
    ).size().reindex(time_range, fill_value=0).reset_index()

    dfGroupped.columns = ['Time', 'Entries']

    print(dfGroupped)
    fig = px.line(
        dfGroupped,
        x='Time',
        y='Entries',
        title='Hourly Entries',
        color_discrete_sequence=[COLOUR_CHART]
    )
    fig.update_traces(marker=dict(size=8))
    fig.update_layout(
        plot_bgcolor=COLOUR_PAGE_BG,
        paper_bgcolor="#ffffff",
        font_color=COLOUR_CARD_VALUE,
        margin=dict(l=30, r=10, t=40, b=30),
        autosize=True
    )
    return fig


#Funct to plot the average busyness graph across all days in the database
def plot_avg_busyness():
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM Detections", con)
    con.close()

    #Converting TimeStamp and filtering to entries only
    df['Time'] = pd.to_datetime(df['timeStamp'])
    df = df[df['direction'] == 'in']

    #Extracting the hour and the date from each record
    df['Hour'] = df['Time'].dt.hour
    df['Date'] = df['Time'].dt.date

    #Create a reference of all possible Date/Hour combinations
    all_dates = df['Date'].unique()
    all_hours = range(6, 18)
    full_index = pd.MultiIndex.from_product([all_dates, all_hours], names=['Date', 'Hour'])

    #Counting entries per hour per day, then averaging across all days
    perDayPerHour = df.groupby(['Date', 'Hour']).size().reindex(full_index, fill_value=0).reset_index(name='Entries')
    avgByHour = perDayPerHour.groupby('Hour')['Entries'].mean().reset_index(name='AvgEntries')
    avgByHour['HourLabel'] = avgByHour['Hour'].apply(lambda h: f"{h:02d}:00 - {h + 1:02d}:00")
    #Rounding avgByHour up, to include whole people
    avgByHour['AvgEntries'] = np.ceil(avgByHour['AvgEntries']).astype(int)

    fig2 = px.line(
        avgByHour,
        x='Hour',
        y='AvgEntries',
        title='Average Occupancy by Hour of Day (All Days)',
        labels={'Hour': 'Hour of Day', 'AvgEntries': 'Avg Entries'},
        color_discrete_sequence=[COLOUR_CHART]
    )
    fig2.update_traces(marker=dict(size=10))
    fig2.update_layout(
        plot_bgcolor=COLOUR_PAGE_BG,
        paper_bgcolor="#ffffff",
        font_color=COLOUR_CARD_VALUE,
        xaxis=dict(
            tickmode='array',
            tickvals=avgByHour['Hour'].tolist(),
            ticktext=avgByHour['HourLabel'].tolist(),
            tickangle=45
        ),
        margin=dict(l=30, r=10, t=40, b=60),
        autosize=True
    )
    return fig2


#mobile device changes so everything is displayed optimally
app = Dash(
    __name__,
    server=server,
    url_base_pathname="/dashboard/",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)
app.title = 'ELC FootFall Dashboard'

app.layout = html.Div(
    style={"fontFamily": "sans-serif", "backgroundColor": COLOUR_PAGE_BG, "minHeight": "100vh"},
    children=[
        dcc.Interval(
            id='interval-component',
            interval=60 * 5 * 1000,  #5 minute refresh
            n_intervals=0
        ),

        #Header.
        html.Div(
            [
                html.Img(
                    src=r"assets/northumbriaUniLogo.png",
                    style={"maxHeight": "60px", "width": "auto"}
                ),
                html.H1(
                    "Equipment Loans Centre footfall dashboard",
                    style={
                        "textAlign": "center",
                        "flex": "1",
                        "fontSize": "clamp(14px, 3vw, 22px)",
                        "margin": "0 8px",
                        "color": COLOUR_HEADER_TEXT
                    }
                ),
                html.Img(
                    src=r"assets/northumbriaUniLogo.png",
                    style={"maxHeight": "60px", "width": "auto"}

                ),
                html.A(
                    "logout",
                    href="/logout",
                    style={
                        "marginLeft": "20px",
                        "color": "white",
                        "backgroundColor": "#c0392b",
                        "padding": "10px 15px",
                        "borderRadius": "6px",
                        "textDecoration": "none"

                    }
                )
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "padding": "12px 16px",
                "backgroundColor": COLOUR_HEADER_BG,
                "borderBottom": f"1px solid {COLOUR_BORDER}"
            }
        ),

        #Content 
        html.Div(
            [
                #Stats
                html.Div(
                    [
                        html.Div(
                            [
                                html.P("Live count",
                                       style={"fontSize": "13px", "color": COLOUR_CARD_LABEL, "margin": "0 0 6px"}),
                                html.P(id="liveCount",
                                       style={"fontSize": "28px", "fontWeight": "500", "margin": "0 0 3px",
                                              "color": COLOUR_CARD_VALUE}),
                                html.P("currently inside",
                                       style={"fontSize": "11px", "color": COLOUR_CARD_LABEL, "margin": "0"})
                            ],
                            style={"background": COLOUR_CARD_BG, "borderRadius": "8px", "padding": "14px 16px",
                                   "border": f"0.5px solid {COLOUR_BORDER}"}
                        ),
                        html.Div(
                            [
                                html.P("Today's count",
                                       style={"fontSize": "13px", "color": COLOUR_CARD_LABEL, "margin": "0 0 6px"}),
                                html.P(id="todayCount",
                                       style={"fontSize": "28px", "fontWeight": "500", "margin": "0 0 3px",
                                              "color": COLOUR_CARD_VALUE}),
                                html.P("entries so far today",
                                       style={"fontSize": "11px", "color": COLOUR_CARD_LABEL, "margin": "0"})
                            ],
                            style={"background": COLOUR_CARD_BG, "borderRadius": "8px", "padding": "14px 16px",
                                   "border": f"0.5px solid {COLOUR_BORDER}"}
                        ),
                        html.Div(
                            [
                                html.P("Peak hour",
                                       style={"fontSize": "13px", "color": COLOUR_CARD_LABEL, "margin": "0 0 6px"}),
                                html.P(id="peakHour",
                                       style={"fontSize": "20px", "fontWeight": "500", "margin": "0 0 3px",
                                              "color": COLOUR_CARD_VALUE}),
                                html.P("busiest hour today",
                                       style={"fontSize": "11px", "color": COLOUR_CARD_LABEL, "margin": "0"})
                            ],
                            style={"background": COLOUR_CARD_BG, "borderRadius": "8px", "padding": "14px 16px",
                                   "border": f"0.5px solid {COLOUR_BORDER}"}
                        ),
                    ],
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "repeat(auto-fit, minmax(160px, 1fr))",
                        "gap": "10px",
                        "marginBottom": "16px"
                    }
                ),

                #Drop down to show graph options.
                dcc.Dropdown(
                    id='timeRange',
                    options=[
                        {'label': 'Last 7 Days', 'value': 7},
                        {'label': 'Last 30 Days', 'value': 30},
                        {'label': 'Last 90 Days', 'value': 90}
                    ],
                    value=90, #default value of 90days.
                    clearable=False,
                    style={
                        "width": "200px",
                        "marginBottom": "15px"
                    }
                ),

                #Graphs
                dcc.Graph(
                    id='graph',
                    config={"displayModeBar": False},
                    style={"marginBottom": "12px"}
                ),

                html.Button(
                    "Download as CSV",
                    id="downloadBtn",
                    style={
                        "marginBottom": "10px",
                        "padding": "10px 15px",
                        "backgroundColor": "#2c3650",
                        "color": "white",
                        "border": "none",
                        "borderRadius": "6px",
                        "cursor": "pointer"
                    }
                ),
                dcc.Download(id="downloadCSV"),

                dcc.Graph(
                    id='avgBusynessGraph',
                    config={"displayModeBar": False}
                ),
            ],
            style={
                "padding": "16px",
                "maxWidth": "1200px",
                "margin": "0 auto"
            }
        )
    ]
)


#Callback to update all counters and both graphs
@app.callback(
    [
        Output('liveCount', 'children'),
        Output('todayCount', 'children'),
        Output('peakHour', 'children'),
        Output('graph', 'figure'),
        Output('avgBusynessGraph', 'figure')
    ],
    Input('interval-component', 'n_intervals'),
    Input('timeRange', 'value')
)
#Funct to recalculate 'live' values.
def updateData(n, days):
    liveCountData = calc_live_count()
    todayCount = calc_today_count()
    peakHour = calc_peak_hour()
    fig = plot_graph(days)
    avgBusy = plot_avg_busyness()

    return (
        str(liveCountData),
        str(todayCount),
        peakHour,
        fig,
        avgBusy
    )

#Callback to check for 'downloadCSV' button clicks.
@app.callback(
    Output("downloadCSV", "data"),
    Input("downloadBtn", "n_clicks"),
    prevent_initial_call=True
)
#Funct to download whole df as CSV to machine.
def download_csv(n_clicks):
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM Detections", con)
    con.close()
    return dcc.send_data_frame(df.to_csv, "footfall_data.csv", index=False)


#Making dashboard accessible to other machines on the network
if __name__ == "__main__":
    createDB()
    app.run(debug=False, host='0.0.0.0', port=8050)

    #Ensure the users table exists before starting the app
    create_users_table()

    #Run the Flask server (which also serves the Dash dashboard)
    server.run(debug=False, host="0.0.0.0", port=8050)
