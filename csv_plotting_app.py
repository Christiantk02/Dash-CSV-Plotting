# Import libraries
import dash
import base64
import io
import pandas as pd
import plotly.express as px
from dash import html, dcc, Input, Output, State, MATCH

# Function to process uploaded CSV
def process_csv(contents):
    x, data = contents.split(',')
    decoded = base64.b64decode(data)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    return df


# Initialize the Dash app
app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True # IDEK why but it works

# Define the layout of the app
app.layout = html.Div([

    html.Div([  # Title Section
        html.H1('CSV Plotting App'),
        html.P('Plot and visualize CSV data.'),
        html.P('By Christian T.Kvernland')
    ]),

    html.Div([  # Drag and Drop Section
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select CSV Files', id='select-files-link')
            ]),
            multiple=False,
            accept='.csv',
            style={'width': '70%', 'height': '60px', 'margin': '0 auto', 'lineHeight': '60px', 'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px', 'textAlign': 'center'}      
        )
    ]),

    html.Div(id='output-data'),  # Output Section

    dcc.Store(id='stored-data', data=[]),  # Storage for data

    dcc.Dropdown(  # File Selector Section
        id='file-selector',
        multi=True,
        placeholder="Select files to plot...",
        style={'width': '60%', 'color': 'black'}
    ),

    html.Div(id='graphs') # Graph Section

], style={'backgroundColor': '#0d1b2a', 'minHeight': '100vh', 'padding': '20px', 'font-family': 'verdana', 'color': 'white'})


# App callback to handle file upload
@app.callback(
    Output('output-data', 'children'),
    Output('stored-data', 'data'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('stored-data', 'data')
)
def handle_upload(contents, filename, stored_data):
    if contents is None:
        return 'No file uploaded yet.', stored_data

    df = process_csv(contents)
    stored_data.append({'name': filename, 'data': df.to_json(date_format='iso', orient='split')})

    html_output = html.Div([
        html.H4(f'Uploaded: {filename}'),
        html.P(f"Rows: {len(df)}, Columns: {len(df.columns)}"),
        html.Hr(),
        html.P("Files uploaded so far:"),
        html.Ul([html.Li(d['name']) for d in stored_data]),
        html.Hr()
    ])

    return html_output, stored_data


# App callback to update file selector dropdown
@app.callback(
    Output('file-selector', 'options'),
    Input('stored-data', 'data')
)
def update_file_selector(stored_data):
    if not stored_data:
        return []
    return [{'label': d['name'], 'value': d['name']} for d in stored_data]


# App callback to plot selected files
@app.callback(
    Output('graphs', 'children'),
    Input('file-selector', 'value'),
    State('stored-data', 'data')
)
def plot_selected_files(values, stored_data):
    if not values:
        return 'No files selected for plotting.'

    graphs = []
    for val in values:
        for d in stored_data:
            if d['name'] == val:
                df = pd.read_json(io.StringIO(d['data']), orient='split')
                fig = px.line()
                graphs.append(
                    html.Div([
                        html.Div([
                            html.H3(f'Graph for {val}'),
                            dcc.Graph(
                                id={'type': 'graph', 'index': val},
                                figure=fig
                            ),
                            html.Hr()
                        ], style={'flex': '3', 'marginRight': '20px'}),

                        html.Div([
                            html.H4(f'Controls for {val}'),
                            dcc.Dropdown(
                                id={'type': 'dropdown', 'index': val},
                                options=[{'label': col, 'value': col} for col in df.columns],
                                multi=False,
                                placeholder="Select X Axis Data",
                                style={'color': 'black'}
                            ),
                            dcc.Checklist(
                                id={'type': 'checklist', 'index': val},
                                options=[{'label': col, 'value': col} for col in df.select_dtypes(include=['number']).columns],
                                labelStyle={'display': 'block'}
                            )
                        ], style={'maxHeight': '300px', 'overflowY': 'scroll', 'overflowX': 'hidden', 'flex': '1', 'display': 'flex', 'flexDirection': 'column', 'gap': '10px'})
                    ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '40px', 'backgroundColor': '#1b263b', 'borderRadius': '10px', 'padding': '15px'}))
    
    return graphs


# App callback to update graphs
@app.callback(
    Output({'type': 'graph', 'index': MATCH}, 'figure'),
    Input({'type': 'dropdown', 'index': MATCH}, 'value'),
    Input({'type': 'checklist', 'index': MATCH}, 'value'),
    State({'type': 'dropdown', 'index': MATCH}, 'id'),
    State('stored-data', 'data')
)

def update_graph(x_axis, y_axes, id, stored_data):
    if not x_axis or not y_axes:
        return px.line()
    
    if len(y_axes) == 1:
        y_axes = y_axes[0]

    for d in stored_data:
        if d['name'] == id['index']:
            df = pd.read_json(io.StringIO(d['data']), orient='split')
            
            try:
                df[x_axis] = pd.to_datetime(df[x_axis])
            except Exception:
                pass
            
            fig = px.line(df, x=x_axis, y=y_axes)
            return fig
    

# Run the app
app.run(debug=True)