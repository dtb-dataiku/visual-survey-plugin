from dataiku.customwebapp import *

# Access the parameters that end-users filled in using webapp config
# For example, for a parameter called "input_dataset"
# input_dataset = get_webapp_config()["input_dataset"]

import dataiku

import pandas as pd
import datetime

import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from flask import request

from visualsurvey.survey import create_question_card


# PLUGIN
# Get parameters
webapp_config = get_webapp_config()
survey_header = webapp_config['survey_header']
survey_subheader = webapp_config['survey_subheader']
dataset_name = webapp_config['dataset_name']
type_col = webapp_config['type_column']
header_col = webapp_config['header_column']
subheader_col = webapp_config['subheader_column']
options_col = webapp_config['options_column']
folder_name = webapp_config['folder_name']
anonymous = webapp_config['anonymous']

# SETUP
# Set delimiter
DELIMITER = '|'

# Map question type to dash component element
ELEMENT_MAP = {
    'choice': 'value',
    'open': 'value',
    'rank': 'data'
}

# Load questions
questions_cols = [type_col, header_col, subheader_col, options_col]
questions_ds = dataiku.Dataset(dataset_name)
questions_df = questions_ds.get_dataframe(columns=questions_cols)
questions_df = questions_df.loc[questions_df[type_col] in ELEMENT_MAP.keys(), ]

# Build list of question card parameters
questions = []
for i, row in questions_df.iterrows():
    questions.append({
        'type': row[type_col],
        'name': row[header_col],
        'question': row[subheader_col],
        'options': row[options_col].split(DELIMITER) if row[type_col] != 'open' else None,
        'display': 'Item' if row[type_col] == 'rank' else None
    })

# Get folder responses
folder = dataiku.Folder(folder_name)






# Input data
RANK_OPTIONS = [{'option': f'Option {i+1}'} for i in range(3)]
rank_df = pd.DataFrame(RANK_OPTIONS)
rank_df['up'] = '🔼'
rank_df['down'] = '🔽'

OPTIONS = [{'label': f'Label {i+1}', 'value': i + 1} for i in range(5)]
options_df = pd.DataFrame(OPTIONS)


# Build question cards
questions = [
    {
        'question_type': 'ranking',
        'header': 'Question 1',
        'subheader': 'Rank these.',
        'name': 'Option',
        'options_df': rank_df
    },
    {
        'question_type': 'choice',
        'header': 'Question 2',
        'subheader': 'Which one do you need?',
        'options_df': options_df,
        'value': 1
    },
    {
        'question_type': 'choice',
        'header': 'Question 3',
        'subheader': 'Which one do you want?',
        'options_df': options_df,
        'value': 1
    },
    {
        'question_type': 'open',
        'header': 'Question 4',
        'subheader': 'Do you have any thoughts?'
    }
]

question_cards = []
for q, question in enumerate(questions):
    question_cards.append(create_question_card(f'question-card-{q}', **question))
    
# APP
# Set stylesheet
app.config.external_stylesheets = [dbc.themes.BOOTSTRAP]

# Define layout
app.layout = html.Div([
    dbc.Container(
        [
            # Header
            dbc.Row(dbc.Col(html.Div(
                [
                    html.H1(survey_header, className='text-center text-primary mb-4'),
                    html.P(survey_subheader, className='text-center')
                ],
                className='py-4'
            ))),
            # Survey
            dbc.Row(dbc.Col(question_cards)),
            # Submit
            dbc.Row(dbc.Col(html.Div(dbc.Button(
                'Submit Responses',
                id='submit-button',
                color='primary',
                size='lg',
                n_clicks=0
            ), className='text-center'))),
            # Output
            dbc.Row(dbc.Col(html.Div(id='survey-output', className='mt-5')))
        ],
        fluid=True,
        className='bg-light p-5'
    )
])

# CALLBACKS
# Handle ranking question
def register_callbacks_for_ranking_question(cid):
    @app.callback(
        Output(cid, 'data'),
        Input(cid, 'active_cell'),
        State(cid, 'data'),
        prevent_initial_call=True
    )
    def _callback(active_cell, current_data, _cid=cid):
        if not active_cell or not current_data:
            return dash.no_update
        
        row = active_cell['row']
        col_id = active_cell['column_id']
        
        df = pd.DataFrame(current_data)
        
        if col_id == 'up' and row > 0:
            df.iloc[row], df.iloc[row - 1] = df.iloc[row - 1].copy(), df.iloc[row].copy()
        elif col_id == 'down' and row < len(df) - 1:
            df.iloc[row], df.iloc[row + 1] = df.iloc[row + 1].copy(), df.iloc[row].copy()
        else:
            return dash.no_update
        
        return df.to_dict('records')
    
for q, question in enumerate(questions):
    if question['type'] == 'rank':
        register_callbacks_for_ranking_question(f'question-card-{q}')

# Handle submit button
states = [
    State(f'question-card-{q}', ELEMENT_MAP[question['question_type']])
    for q, question in enumerate(questions)
]

@app.callback(
    Output('survey-output', 'children'),
    Input('submit-button', 'n_clicks'),
    *states,
    prevent_initial_call=True
)
def submit_survey(n_clicks, *responses):
    if not n_clicks:
        return dash.no_update
    
    # Get user
    client = dataiku.api_client()
    headers = dict(request.headers)
    auth_info_browser = client.get_auth_info_from_browser_headers(headers)
    user = auth_info_browser['authIdentifier']
    
    # Build dataframe of responses
    now = datetime.datetime.now()
    response_data = []
    for r, response in enumerate(responses):
        question = questions[r]
        if question['question_type'] == 'ranking':
            name = question['name'].lower()
            df = pd.DataFrame({
                'option': [item[name] for item in response],
                'order': range(1, len(response) + 1)
            })
            
            for _, row in df.iterrows():
                response_data.append({
                    'question_id': r,
                    'question_type': question['question_type'],
                    'question_header': question['header'],
                    'question_subheader': question['subheader'],
                    'question_option': row['option'],
                    'question_value': row['order'],
                    'user': user,
                    'timestamp': now
                })
        elif question['question_type'] == 'choice':
            option = (
                question['options_df']
                .loc[question['options_df']['value'] == response, 'label']
                .iloc[0]
            )
            
            response_data.append({
                'question_id': r,
                'question_type': question['question_type'],
                'question_header': question['header'],
                'question_subheader': question['subheader'],
                'question_option': option,
                'question_value': response,
                'user': user,
                'timestamp': now
            })
        elif question['question_type'] == 'open':
            response_data.append({
                'question_id': r,
                'question_type': question['question_type'],
                'question_header': question['header'],
                'question_subheader': question['subheader'],
                'question_option': response if response else 'No response provided.',
                'question_value': len(response) if response else 0,
                'user': user,
                'timestamp': now
            })
            
    response_df = pd.DataFrame(response_data)
    
    # Save responses
    user_str = '_at_'.join(user.split("@")).replace(".", "_")
    filename = "-".join(["response", user_str, now.strftime("%Y%m%d-%H%M%S")]) + ".csv"
    csv = response_df.to_csv(index=False).encode("utf-8")
    folder.upload_data(filename, csv)
        
    # Build confirmation message
    cols = ['question_id', 'question_header', 'question_subheader']
    display_df = (
        response_df
        .sort_values([*cols, 'question_value'])
        .groupby(cols, as_index=False)
        .agg({'question_option': lambda o: o.str.cat(sep=', ')})
        .drop(columns=['question_id'])
    )
    
    parts = []
    parts.append(html.H4('Thank you!', className='alert-heading'))
    parts.append(html.P("Your submission has been successfully recorded. Here is a summary of your response."))
    parts.append(html.Hr())
    
    for _, row in display_df.iterrows():
        question_header = row['question_header']
        question_subheader = row['question_subheader']
        question_response = row['question_option']
        
        parts.append(html.H5(f"{question_header} - {question_subheader}"))
        parts.append(html.P(question_response))
    
    return dbc.Alert(parts, color='success', dismissable=True)
