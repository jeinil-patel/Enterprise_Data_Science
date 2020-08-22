import pandas as pd
import numpy as np

import dash
dash.__version__
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output,State

import plotly.graph_objects as go

import os
print(os.getcwd())
df_input_large=pd.read_csv('data/processed/COVID_final_set.csv',sep=';')


fig = go.Figure()

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    
    html.H1('Applied Data Science on COVID-19 data', style={'text-align': 'center',
                                                                        'color': 'white',
                                                                        'padding': 10,
                                                                        'background-color': '#25383C',}),
    dcc.Markdown('''Goal of the project is to analyse and learn patterns in COVID-19 dataset from different 
    open sources. It covers the full walkthrough of: automated data gathering, data transformations, filtering and machine learning to approximating the doubling time, and
    (static) deployment of responsive dashboard.''',
                 style={'text-align': 'center',
                        'padding': 1,
                        'background-color': '#FAFFFF',}),
    
    dcc.Markdown(''' ''',
                 style={'text-align': 'center',
                        'padding': 10,}),
    
    html.Div([  
        
        html.Div([
            
            dcc.Markdown('''Multi-Select Country for visualization:''')
            ],
                style={'width': '45%', 'display': 'inline-block', 'padding-left': 10, 'font-size':18}),

            html.Div([
                dcc.Markdown('''Select Timeline or doubling time:''')
            ],
                style={'width': '45%', 'float': 'right', 'display': 'inline-block', 'font-size':18})
    ]),
    

    
    html.Div([  
        
        html.Div([
            dcc.Dropdown(
            id='country_drop_down',
            options=[ {'label': each,'value':each} for each in df_input_large['country'].unique()],
            value=['Spain', 'Germany','Italy'], # which are pre-selected
            multi=True
            )],
                style={'width': '45%', 'display': 'inline-block', 'padding-left': 10}),

            html.Div([
                dcc.Dropdown(
                id='doubling_time',
                options=[
                    {'label': 'Timeline Confirmed ', 'value': 'confirmed'},
                    {'label': 'Timeline Confirmed Filtered', 'value': 'confirmed_filtered'},
                    {'label': 'Timeline Doubling Rate', 'value': 'confirmed_DR'},
                    {'label': 'Timeline Doubling Rate Filtered', 'value': 'confirmed_filtered_DR'},
                ],
                    value='confirmed',
                    multi=False
                )],
                
                style={'width': '45%', 'float': 'right', 'display': 'inline-block'})
    ]),
    
     html.Div([ 
                    dcc.RadioItems(
                    id='yaxis-type',
                    options=[{'label': i, 'value': i} for i in ['Log', 'Linear']],
                    value='Log',
                    labelStyle={'display': 'inline-block'},
                    style={'padding': 10})
                        ]),


    dcc.Graph(figure=fig, id='main_window_slope')
])



@app.callback(
    Output('main_window_slope', 'figure'),
    [Input('country_drop_down', 'value'),
    Input('doubling_time', 'value'),
    Input(component_id='yaxis-type', component_property='value')])
def update_figure(country_list,show_doubling, yaxis):


    if 'doubling_rate' in show_doubling:
        my_yaxis={'type':"log",
               'title':'Approximated doubling rate over 3 days (larger numbers are better #stayathome)'
              }
    else:
        my_yaxis={'type': 'linear' if yaxis == 'Linear' else 'log', 
                  'title':'Confirmed infected people (source johns hopkins csse)'
              }


    traces = []
    for each in country_list:

        df_plot=df_input_large[df_input_large['country']==each]

        if show_doubling=='doubling_rate_filtered':
            df_plot=df_plot[['state','country','confirmed','confirmed_filtered','confirmed_DR','confirmed_filtered_DR','date']].groupby(['country','date']).agg(np.mean).reset_index()
        else:
            df_plot=df_plot[['state','country','confirmed','confirmed_filtered','confirmed_DR','confirmed_filtered_DR','date']].groupby(['country','date']).agg(np.sum).reset_index()


        traces.append(dict(x=df_plot.date,
                                y=df_plot[show_doubling],
                                mode='markers+lines',
                                opacity=0.9,
                                name=each
                        )
                )

    return {
            'data': traces,
            'layout': dict (

                xaxis={'title':'Timeline',
                        'tickangle':-45,
                        'nticks':20,
                        'tickfont':dict(size=14,color="#7f7f7f"),
                      },

                yaxis=my_yaxis,
                legend=dict(orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1),
                autosize=True,
                #height=768,
                #width=1360,
                hovermode='closest'
        )
    }

if __name__ == '__main__':

    app.run_server(debug=True, use_reloader=False)
