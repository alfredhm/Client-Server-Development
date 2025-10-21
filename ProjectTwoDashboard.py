#!/usr/bin/env python
# coding: utf-8

# In[17]:


# Setup the Jupyter version of Dash
from jupyter_dash import JupyterDash

# Configure the necessary Python module imports for dashboard components
import dash_leaflet as dl
from dash import dcc, html
import plotly.express as px
from dash import dash_table
from dash.dependencies import Input, Output, State
import base64
JupyterDash.infer_jupyter_proxy_config()

# Configure OS routines
import os

# Configure the plotting routines
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


from CRUD_Python_Module import AnimalShelter

###########################
# Data Manipulation / Model
###########################

username = "aacuser"
password = "watchdogman425"

# Connect to database via CRUD Module
db = AnimalShelter(username, password)

# class read method must support return of list object and accept projection json input
# sending the read method an empty document requests all documents be returned
df = pd.DataFrame.from_records(db.read({}))

# MongoDB v5+ is going to return the '_id' column and that is going to have an 
# invlaid object type of 'ObjectID' - which will cause the data_table to crash - so we remove
# it in the dataframe here. The df.drop command allows us to drop the column. If we do not set
# inplace=True - it will reeturn a new dataframe that does not contain the dropped column(s)
df.drop(columns=['_id'],inplace=True)

# Column-name constants from your dataframe
BREED_COL   = 'breed'
SEX_COL     = 'sex_upon_outcome'
AGE_WK_COL  = 'age_upon_outcome_in_weeks'
LAT_COL     = 'location_lat'
LON_COL     = 'location_long'
NAME_COL    = 'name'

# Optional: make sure these are numeric for filtering
df[AGE_WK_COL] = pd.to_numeric(df[AGE_WK_COL], errors='coerce')
df[LAT_COL]    = pd.to_numeric(df[LAT_COL], errors='coerce')
df[LON_COL]    = pd.to_numeric(df[LON_COL], errors='coerce')

## Debug
print(len(df.to_dict(orient='records')))
print(df.columns)


#########################
# Dashboard Layout / View
#########################
app = JupyterDash(__name__)

encoded_image = base64.b64encode(open('Grazioso Salvare Logo.png', 'rb').read())
UNIQUE_TAG = "Alfred Morgan • 10/19/2025"

app.layout = html.Div([
    html.Div([
        html.A(
            html.Img(
                src='data:image/png;base64,' + encoded_image.decode(),
                style={'height': '60px', 'marginRight': '15px'},
                alt="Grazioso Salvare"
            ),
            href="https://www.snhu.edu",
            target="_blank",
            title="SNHU Home"
        ),
        html.H1(
            'SNHU CS-340 • Grazioso Salvare Dashboard',
            style={'display': 'inline-block', 'marginRight': '15px'}
        ),
        html.Span(UNIQUE_TAG, style={'fontStyle': 'italic'})
    ], style={'display': 'flex', 'alignItems': 'center', 'gap': '12px'}),
    html.Hr(),

    # REQUIRED RADIO FILTERS
    dcc.RadioItems(
        id='filter-type',
        options=[
            {'label': 'Water Rescue', 'value': 'water'},
            {'label': 'Mountain or Wilderness Rescue', 'value': 'mountain'},
            {'label': 'Disaster Rescue or Individual Tracking', 'value': 'disaster'},
            {'label': 'Reset (All)', 'value': 'reset'}
        ],
        value='reset',
        inline=True
    ),
    html.Hr(),

    # TABLE WITH LOADING SPINNER
    dcc.Loading(
        id="loading-table",
        type="circle",
        children=[
            dash_table.DataTable(
                id='datatable-id',
                columns=[{"name": i, "id": i, "deletable": False, "selectable": True} for i in df.columns],
                data=df.to_dict('records'),
                page_size=10,
                filter_action='native',
                sort_action='native',
                row_selectable='single',
                selected_rows=[0],
                selected_columns=[],
                virtualization=True,      # smoother redraws on large sets
                style_table={'overflowX': 'auto'},
                style_cell={'minWidth': '120px', 'width': '120px', 'maxWidth': '320px', 'whiteSpace': 'normal'}
            )
        ]
    ),

    html.Br(), html.Hr(),

    # CHART + MAP WITH LOADING SPINNERS
    html.Div(className='row', style={'display': 'flex', 'gap': '24px'}, children=[
        dcc.Loading(
            id="loading-chart",
            type="circle",
            parent_style={"flex": 1}, 
            children=html.Div(id='graph-id', className='col s12 m6', style={'flex': '1', 'minHeight': '520px'}),
        ),
        dcc.Loading(
            id="loading-map",
            type="circle",
            parent_style={"flex": 1}, 
            children=html.Div(id='map-id', className='col s12 m6', style={'flex': '1', 'minHeight': '520px'}),
        )
    ])
])


#############################################
# Interaction Between Components / Controller
#############################################

def filter_dataframe(base_df, key):
    d = base_df.copy()

    # Domain rules from the spec
    if key == 'water':
        breeds = {'Labrador Retriever Mix','Chesapeake Bay Retriever','Newfoundland'}
        sex = 'Intact Female'; lo, hi = 26, 156
        mask = d[BREED_COL].isin(breeds) & (d[SEX_COL]==sex) & (d[AGE_WK_COL].between(lo,hi, inclusive='both'))
        return d[mask]

    if key == 'mountain':
        breeds = {'German Shepherd','Alaskan Malamute','Old English Sheepdog','Siberian Husky','Rottweiler'}
        sex = 'Intact Male'; lo, hi = 26, 156
        mask = d[BREED_COL].isin(breeds) & (d[SEX_COL]==sex) & (d[AGE_WK_COL].between(lo,hi, inclusive='both'))
        return d[mask]

    if key == 'disaster':
        breeds = {'Doberman Pinscher','German Shepherd','Golden Retriever','Bloodhound','Rottweiler'}
        sex = 'Intact Male'; lo, hi = 20, 300
        mask = d[BREED_COL].isin(breeds) & (d[SEX_COL]==sex) & (d[AGE_WK_COL].between(lo,hi, inclusive='both'))
        return d[mask]

    return d  # reset

def mongo_filter_for(key):
    if key == 'water':
        breeds = [
            'Labrador Retriever', 'Labrador Retriever Mix',
            'Chesapeake Bay Retriever', 'Newfoundland',
            'Flat-Coated Retriever', 'Golden Retriever'
        ]
        return {
            'animal_type': 'Dog',
            'breed': {'$in': breeds},
            'sex_upon_outcome': 'Intact Female',
            'age_upon_outcome_in_weeks': {'$gte': 26, '$lte': 156}
        }

    if key == 'mountain':
        breeds = [
            'German Shepherd', 'German Shepherd Dog',
            'Alaskan Malamute', 'Siberian Husky',
            'Old English Sheepdog', 'Rottweiler',
            'Bernese Mountain Dog', 'Australian Shepherd',
            'Belgian Malinois'
        ]
        return {
            'animal_type': 'Dog',
            'breed': {'$in': breeds},
            'sex_upon_outcome': 'Intact Male',
            'age_upon_outcome_in_weeks': {'$gte': 26, '$lte': 156}
        }

    if key == 'disaster':
        breeds = [
            'Bloodhound', 'Doberman Pinscher',
            'German Shepherd', 'Golden Retriever',
            'Labrador Retriever', 'Rottweiler',
            'Belgian Malinois'
        ]
        return {
            'animal_type': 'Dog',
            'breed': {'$in': breeds},
            'sex_upon_outcome': 'Intact Male',
            'age_upon_outcome_in_weeks': {'$gte': 20, '$lte': 300}
        }

    return {}   # reset/all


    
@app.callback(Output('datatable-id','data'),
              [Input('filter-type', 'value')])
def update_dashboard(filter_type):
    query = mongo_filter_for(filter_type)
    proj  = {'_id': 0}  
    docs  = db.read(query, proj)
    dff   = pd.DataFrame.from_records(docs)

    # normalize numeric (defensive)
    for col in ('age_upon_outcome_in_weeks', 'location_lat', 'location_long'):
        if col in dff.columns:
            dff[col] = pd.to_numeric(dff[col], errors='coerce')

    return dff.to_dict('records')

def pie_for_breeds(dframe, breed_col='breed', top_n=8):
    counts = dframe[breed_col].dropna().value_counts()
    if counts.empty:
        return px.pie(names=['No data'], values=[1], hole=.35)

    if len(counts) > top_n:
        other = counts.iloc[top_n:].sum()
        counts = counts.iloc[:top_n]
        counts.loc['Other'] = other

    fig = px.pie(
        names=counts.index,
        values=counts.values,
        hole=.35,
        title='Breed distribution (current filter)'
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        legend_orientation='h', legend_y=-0.1
    )
    return fig

def make_breed_chart(dff, col='breed', max_slices=10, title='Breed distribution (current filter)'):
    if dff.empty or col not in dff.columns:
        return dcc.Graph(figure=px.pie(values=[1], names=['No data'], hole=0.4, title=title))

    counts = (dff[col]
              .dropna()
              .replace('', np.nan)
              .dropna()
              .value_counts())

    if len(counts) > max_slices:
        top = counts.iloc[:max_slices-1]
        other = pd.Series({'Other': counts.iloc[max_slices-1:].sum()})
        counts = pd.concat([top, other])

    fig = px.pie(values=counts.values, names=counts.index, hole=0.4, title=title)
    fig.update_traces(textinfo='percent+label', hovertemplate='%{label}: %{value} (%{percent})')
    fig.update_layout(
        margin=dict(l=30, r=30, t=60, b=10),
        legend=dict(orientation='h', y=-0.15, x=0, title=None),
        height=380
    )
    return dcc.Graph(figure=fig)


# Display the breeds of animal based on quantity represented in
# the data table
@app.callback(Output('graph-id',"children"),
            [Input('datatable-id',"derived_virtual_data")])
def update_graphs(viewData):
    dff = pd.DataFrame(viewData) if viewData is not None else df
    fig = pie_for_breeds(dff, breed_col=BREED_COL, top_n=8)
    return dcc.Graph(figure=fig)
    
#This callback will highlight a cell on the data table when the user selects it
@app.callback(Output('datatable-id', 'style_data_conditional'),
              [Input('datatable-id', 'selected_columns')])
def update_styles(selected_columns):
    if not selected_columns:          
        return []
    return [{'if': {'column_id': c}, 'background_color': '#D2F3FF'}
            for c in selected_columns]


# This callback will update the geo-location chart for the selected data entry
# derived_virtual_data will be the set of data available from the datatable in the form of 
# a dictionary.
# derived_virtual_selected_rows will be the selected row(s) in the table in the form of
# a list. For this application, we are only permitting single row selection so there is only
# one value in the list.
# The iloc method allows for a row, column notation to pull data from the datatable
@app.callback(Output('map-id',"children"),
              [Input('datatable-id',"derived_virtual_data"),
               Input('datatable-id',"derived_virtual_selected_rows")])
def update_map(viewData, rows):
    dff = pd.DataFrame(viewData) if viewData is not None else df
    if dff.empty or LAT_COL not in dff.columns or LON_COL not in dff.columns:
        return html.Div("No location data.")
    row = rows[0] if rows else 0
    lat = float(dff.iloc[row][LAT_COL]); lon = float(dff.iloc[row][LON_COL])
    name = str(dff.iloc[row][NAME_COL]); breed = str(dff.iloc[row][BREED_COL])

    return dl.Map(style={'width':'100%','height':'500px'}, center=[lat,lon], zoom=11, children=[
        dl.TileLayer(id="base-layer-id"),
        dl.Marker(position=[lat,lon], children=[
            dl.Tooltip(breed),
            dl.Popup([html.H4("Animal"), html.P(name)])
        ])
    ])


app.run_server() 


# In[ ]:





# In[ ]:




