import dash
dash.__version__
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output,State
import random

import plotly.graph_objects as go
import plotly


def generate_table(dataframe, max_rows=10):
    '''Given dataframe, return template generated using Dash components
    '''
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )

## list of hex color codes 
color_list = []
for i in range(int((df_confirmed.shape[1]-1)/2)):
    random_color = '#%02x%02x%02x' % (random.randint(0, 255),random.randint(0, 255), random.randint(0, 255))
    color_list.append(random_color)

fig = go.Figure()

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    
    html.H1('SIR Model (Susceptible, Infectious, or Recovered)', style={'text-align': 'center',
                                                                        'color': 'white',
                                                                        'padding': 10,
                                                                        'background-color': '#25383C',}),
    
    dcc.Markdown(''' Simulation can be carried out at different time periods e.g, 7 days, 15 days. 
    Based on that, curve fitting algorithm from scipy calculates beta and gamma values.

    Note: Initially, it is assumed that 5% of total population of selected country is under threat of virus and simulation 
    begins once 0.005% (applicable for all countries) of susceptible population is infected.  ''',
                 style={'text-align': 'center',
                        'padding': 1,
                        'background-color': '#FAFFFF',}),
    
    dcc.Markdown(''' ''',
                 style={'text-align': 'center',
                        'padding': 10,}),
    
    html.Div([
        
        html.Div([  
            
            html.Div([
               dcc.Markdown('''Country:''')
            ],
                style={'width': '45%', 'display': 'inline-block', 'padding-left': 10,}),

            html.Div([
                dcc.Markdown('''Susceptible population out of total population:''')
            ],
                style={'width': '40%', 'float': 'right', 'display': 'inline-block',})
        ],
        style={'width': '60%', 'display': 'inline-block'}
        ),
        
        html.Div([dcc.Markdown('''Period :''', style={'width': '15%', 'float': 'right'})],
                 style={'width': '40%','float': 'right', 'display': 'inline-block',}
        ),
    ]),
    
    html.Div([
        
        html.Div([

            html.Div([
                dcc.Dropdown(
                    id='country_drop_down',
                    options=[{'label': each,'value':each} for each in country_list],
                    value=['Germany'], # Which is pre-selected
                    multi=True,
                    style={'padding-left': 10}
                ),
                dcc.RadioItems(
                    id='yaxis-type',
                    options=[{'label': i, 'value': i} for i in ['Log', 'Linear']],
                    value='Log',
                    labelStyle={'display': 'inline-block'},
                    style={'padding': 10}
                )
            ],
                style={'width': '45%', 'display': 'inline-block'}),

            html.Div([
                dcc.Dropdown(
                    id='susceptible_population_percentage',
                    options=[{'label': str(number)+'%', 'value': number} for number in range(1,6)],
                    value=5, # Which is pre-selected
                    multi=False,
                    
                ),
            ],
                style={'width': '40%', 'float': 'right', 'display': 'inline-block'})
        ],
        style={'width': '60%', 'display': 'inline-block'}

        ),
        
        html.Div([
            dcc.Dropdown(
                id='period-type',
                options=[{'label': str(each)+' days', 'value': each} for each in ['default', 10, 15, 20, 25, 30]],
                value='default', # Which is pre-selected
                multi=False,
                style={'width': '90%', 'float': 'left'}
            ),
        ],
            style={'width': '15%','float': 'right', 'display': 'inline-block'}
        ),
    ]),
    
    html.Div([  
        
        html.Div([
            dcc.Graph(figure=fig, id='SIR',)],
                style={'width': '60%', 'display': 'inline-block', 'padding-left': 10}),

        html.Div([
            dcc.Markdown('''Beta: infection rate | Gamma: recovery rate | R0: beta/gamma 
                      
                    ''', style={'padding-top': 10}),
            
            html.Table(id='result-summary'),
            dcc.Markdown('''Note: Table will show data of lastly selected country only.''', style={'padding-top': 15}),

            ],
                
                style={'width': '37%', 'float': 'right', 'display': 'inline-block'})
    ]),

])


@app.callback(
    [
        Output(component_id='SIR', component_property='figure'),
        Output(component_id='result-summary', component_property='children'),
    ],
    [
        Input(component_id='country_drop_down', component_property='value'),
        Input(component_id='period-type', component_property='value'),
        Input(component_id='susceptible_population_percentage', component_property='value'),
        Input(component_id='yaxis-type', component_property='value')
    ]
)
def update_figure(country_list, period, susceptable_perc, yaxis):
    
    traces = []
    for pos, each in enumerate(country_list):

        traces.append(dict(x=df_confirmed.date,
                                y=df_confirmed[each],
                                mode='lines',
                                opacity=0.9,
                                name=each,
                                line = dict(color = color_list[pos])
                        )
                )
        fit_line, idx, summary = get_optimum_beta_gamma(df_confirmed, each, susceptable_perc=susceptable_perc,
                                                        period=period)
        traces.append(dict(x=df_confirmed.date[idx:],
                                    y=fit_line,
                                    mode='markers+lines',
                                    opacity=0.9,
                                    name=each+'_simulated',
                                    line = dict(color = color_list[pos])
                            )
                    )
        
    return {
            'data': traces,
            'layout': dict (
                autosize=True,
                #width=900,
                #height=700,
                xaxis={'title':'Timeline',
                        'tickangle':-25,
                        'nticks':20,
                        'tickfont': 18,
                        'titlefont': 20 
                      },

                yaxis={'type': 'linear' if yaxis == 'Linear' else 'log', 
                       'title':'Number of infected people',
                       'tickfont': 18, 
                       'titlefont': 22 
                      },
                legend=dict(orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1)

            )
            
}, generate_table(summary)

if __name__ == '__main__':
    app.run_server(debug=True, 
                   use_reloader=False,
                   host='127.0.0.2',
                   port=8050)