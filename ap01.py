import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import dash_table

df = pd.read_csv('aggr.csv', parse_dates=['Entry time'])
df['YearMonth'] = pd.to_datetime(df['Entry time'].map(lambda x: "{}-{}".format(x.year, x.month)))

############################## Start filter_df function ##############################
def filter_df(df,Exchange=None,Margin=None,start_date=None,end_date=None):
    dff = df[(df['Exchange'] == Exchange) & 
             (df['Margin'] == int(Margin)) & 
             (df['Entry time'] >= start_date) & 
             (df['Entry time'] <= end_date)]
    return(dff)
############################## End filter_df function ##############################

app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/uditagarwal/pen/oNvwKNP.css', 'https://codepen.io/uditagarwal/pen/YzKbqyV.css'])

app.layout = html.Div(children=[
    html.Div(
            children=[
                html.H2(children="Bitcoin Leveraged Trading Backtest Analysis", className='h2-title'),
            ],
            className='study-browser-banner row'
    ),
    html.Div(
        className="row app-body",
        children=[html.P(children="Group 7 : Fabio Nelson Salinas Moreno - Bogotá", id="p-tag"),
            html.Div(
                className="twelve columns card",
                children=[
                    html.Div(
                        className="padding row",
                        children=[
                            html.Div(
                                className="two columns card",
                                children=[
                                    html.H6("Select Exchange",),
                                    dcc.RadioItems(
                                        id="exchange-select",
                                        options=[
                                            {'label': label, 'value': label} for label in df['Exchange'].unique()
                                        ],
                                        value='Bitmex',
                                        labelStyle={'display': 'inline-block'}
                                    )
                                ]
                            ),
                            # Leverage Selector
                            html.Div(
                                className="two columns card",
                                children=[
                                    html.H6("Select Leverage"),
                                    dcc.RadioItems(
                                        id="leverage-select",
                                        options=[
                                            {'label': str(label), 'value': str(label)} for label in df['Margin'].unique()
                                        ],
                                        value='1',
                                        labelStyle={'display': 'inline-block'}
                                    ),
                                ]
                            ),
                            html.Div(
                                className="three columns card",
                                children=[
                                    html.H6("Select a Date Range"),
                                    dcc.DatePickerRange(
                                        id="date-range",
                                        display_format="MMM YY",
                                        start_date=df['Entry time'].min(),
                                        end_date=df['Entry time'].max()
                                    ),
                                ]
                            ),
                            html.Div(
                                id="strat-returns-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="strat-returns", className="indicator_value"),
                                    html.P('Strategy Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                            html.Div(
                                id="market-returns-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="market-returns", className="indicator_value"),
                                    html.P('Market Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                            html.Div(
                                id="strat-vs-market-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="strat-vs-market", className="indicator_value"),
                                    html.P('Strategy vs. Market Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                        ]
                )
        ]),
        html.Div(
            className="twelve columns card",
            children=[
                dcc.Graph(
                    id="monthly-chart",
                    figure={
                        'data': []
                    }
                )
            ]
        ),
        html.Div(
                className="padding row",
                children=[
                    html.Div(
                        className="six columns card",
                        children=[
                            dash_table.DataTable(
                                id='table',
                                columns=[
                                    {'name': 'Number', 'id': 'Number'},
                                    {'name': 'Trade type', 'id': 'Trade type'},
                                    {'name': 'Exposure', 'id': 'Exposure'},
                                    {'name': 'Entry balance', 'id': 'Entry balance'},
                                    {'name': 'Exit balance', 'id': 'Exit balance'},
                                    {'name': 'Pnl (incl fees)', 'id': 'Pnl (incl fees)'},
                                ],
                                style_cell={'width': '50px'},
                                style_table={
                                    'maxHeight': '450px',
                                    'overflowY': 'scroll'
                                },
                            )
                        ]
                    ),
                    dcc.Graph(
                        id="pnl-types",
                        className="six columns card",
                        figure={}
                    )
                ]
            ),
            html.Div(
                className="padding row",
                children=[
                    dcc.Graph(
                        id="daily-btc",
                        className="six columns card",
                        figure={}
                    ),
                    dcc.Graph(
                        id="balance",
                        className="six columns card",
                        figure={}
                    )
                ]
            )
        ]
    )        
])

############################## Start update_range_date function and callback ##############################
@app.callback(
    dash.dependencies.Output('date-range', 'start_date'),# component with id out will be changed, the '2nd arg' argument is updated
    [
        dash.dependencies.Input('exchange-select', 'value')# input with id in and the second arg parameter
    ]
)
def update_range_date(value):
    dff = df[df['Exchange']==value] # We filter our dataset for the daterange

    return pd.to_datetime(dff['Entry time'].min())

@app.callback(
    dash.dependencies.Output('date-range', 'end_date'),# component with id out will be changed, the '2nd arg' argument is updated
    [
        dash.dependencies.Input('exchange-select', 'value')# input with id in and the second arg parameter
    ]
)
def update_range_date(value):
    dff = df[df['Exchange']==value] # We filter our dataset for the daterange

    return pd.to_datetime(dff['Entry time'].max())
############################## End update_range_date function and callback ##############################

############################## Start calc_returns_over_month function and callback ##############################
def calc_returns_over_month(dff):
    out = []
    for name, group in dff.groupby('YearMonth'):
        exit_balance = group.head(1)['Exit balance'].values[0]
        entry_balance = group.tail(1)['Entry balance'].values[0]
        monthly_return = (exit_balance*100 / entry_balance)-100
        out.append({
            'month': name,
            'entry': entry_balance,
            'exit': exit_balance,
            'monthly_return': monthly_return
        })
    return out

def calc_btc_returns(dff):
    btc_start_value = dff.tail(1)['BTC Price'].values[0]
    btc_end_value = dff.head(1)['BTC Price'].values[0]
    btc_returns = (btc_end_value * 100/ btc_start_value)-100
    return btc_returns

def calc_strat_returns(dff):
    start_value = dff.tail(1)['Exit balance'].values[0]
    end_value = dff.head(1)['Entry balance'].values[0]
    returns = (end_value * 100/ start_value)-100
    return returns

@app.callback(
    [
        dash.dependencies.Output('monthly-chart', 'figure'),
        dash.dependencies.Output('market-returns', 'children'),
        dash.dependencies.Output('strat-returns', 'children'),
        dash.dependencies.Output('strat-vs-market', 'children'),
    ],
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),

    )
)
############################## End calc_returns_over_month function and callback ##############################

############################## Start update_monthly function and callback ##############################
def update_monthly(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    data = calc_returns_over_month(dff)
    btc_returns = calc_btc_returns(dff)
    strat_returns = calc_strat_returns(dff)
    strat_vs_market = strat_returns - btc_returns
    return {
        'data': [
            go.Candlestick(
                open=[each['entry'] for each in data],
                close=[each['exit'] for each in data],
                x=[each['month'] for each in data],
                low=[each['entry'] for each in data],
                high=[each['exit'] for each in data]
            )
        ],
        'layout': {
            'title': 'Overview of Monthly performance'
        }
    }, f'{btc_returns:0.2f}%', f'{strat_returns:0.2f}%', f'{strat_vs_market:0.2f}%'

@app.callback(
    dash.dependencies.Output('table', 'data'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),
    )
)
############################## End update_monthly function and callback ##############################

############################## Start update_table function and callback ##############################
def update_table(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    return dff.to_dict('records')

@app.callback(
    dash.dependencies.Output('pnl-types', 'figure'),
    [
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),
    ]
)
############################## End update_table function and callback ##############################

############################## Start update_bar function and callback ##############################
def update_bar(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    dff_l=dff[dff['Trade type']=='Long']
    dff_s=dff[dff['Trade type']=='Short']
    return { 
       'data': [go.Bar(y=dff_l['Pnl (incl fees)'],x=dff_l['Entry time'], name='Long'),
                go.Bar(y=dff_s['Pnl (incl fees)'],x=dff_s['Entry time'],name='Short') ],
       'layout':  go.Layout(height=400,width=600,title= 'Pnl (inch fees) by date',
                            margin={'l':40, 'b':40, 't':60,'r':10})
        
    }

@app.callback(
    dash.dependencies.Output('daily-btc', 'figure'),
    [
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),
    ]
)
############################## End update_bar function and callback ##############################

############################## Start update_btc function and callback ##############################
def update_btc(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    return { 
       'data': [go.Scatter(y=dff['BTC Price'],x=dff['Entry time'], mode='lines')],
       'layout':  go.Layout(height=400,width=600,title= 'Daily BTC Price',
                            margin={'l':40, 'b':40, 't':60,'r':10})
        
    }

@app.callback(
    dash.dependencies.Output('balance', 'figure'),
    [
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),
    ]
)
############################## End update_btc function and callback ##############################

############################## Start update_over function and callback ##############################
def update_over(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    return { 
       'data': [go.Scatter(y=dff['Entry balance'],x=dff['Entry time'], mode='lines')],
       'layout':  go.Layout(height=400,width=600,title= 'Balance Overtime',
                            margin={'l':40, 'b':40, 't':60,'r':10})
        
    }
############################## End update_over function and callback ##############################

if __name__ == "__main__":
    app.run_server(debug=True)
    #app.run_server(debug=True, host='0.0.0.0')
