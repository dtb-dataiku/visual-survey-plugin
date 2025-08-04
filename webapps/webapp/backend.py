import datetime
import json
import uuid
from pathlib import Path
from typing import Dict, List, Tuple

import dataiku
from dataiku.customwebapp import *
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State, ALL
import dash_bootstrap_components as dbc
from flask import request
import pandas as pd
from faker import Faker

from visualsurvey.schema import QuestionType, parse_questions
from visualsurvey.survey import build_survey_layout


# CONFIGURATION
# Get plugin parameters
print("--> Get parameters")
webapp_config = get_webapp_config()

survey_header = webapp_config['survey_header']
survey_subheader = webapp_config['survey_subheader']
question_ds_name = webapp_config['question_dataset']
folder_name = webapp_config['folder_name']
anonymous = webapp_config['anonymous']

question_cols_map = {
    webapp_config['type_column']: 'qtype',
    webapp_config['name_column']: 'id',
    webapp_config['question_column']: 'label',
    webapp_config['options_column']: 'options',
    webapp_config['default_option_column']: 'default',
    webapp_config['required_column']: 'required'
}


# HELPER
def _normalize_rank_responses(rank_values: List[int], rank_ids: List[Dict]) -> Dict[str, str]:
    """Convert per-option dropdown selections into a single string per question."""
    by_question: Dict[str, Dict[str, int]] = {}
    duplicates: List[str] = []
    
    for val, cid in zip(rank_values, rank_ids):
        qid, opt = cid['qid'], cid['opt']
        # Detect duplicate ranks for the same question
        if qid in by_question and val in by_question[qid].values():
            if qid not in duplicates:
                duplicates.append(qid)
        by_question.setdefault(qid, {})[opt] = val
        
    # Order options by ascending rank (1 is first)
    compact: Dict[str, str] = {}
    for qid, mapping in by_question.items():
        ordered_opts = [opt for opt, _ in sorted(mapping.items(), key=lambda r: r[1])]
        compact[qid] = ' | '.join(ordered_opts)
        
    return compact, duplicates

def _find_missing_required(response: Dict[str, str]) -> List[str]:
    """Return list of missing question IDs for required questions left unanswered."""
    missing: List[str] = []
    for q in questions:
        if not q.required:
            continue
            
        if response.get(q.id, "") in ("", "[]"):
            missing.append(q.id)
            
    return missing


def _get_user(anonymous: bool) -> str:
    """Gets Dataiku identifier or anonymous identifier."""
    headers = dict(request.headers)
    auth_info_browser = dataiku.api_client().get_auth_info_from_browser_headers(headers)
    
    user = auth_info_browser['authIdentifier']
    if anonymous:
        f = Faker('en_US')
        if '@' in user:
            user = '@'.join([f.bothify('#' * 16), user.split('@')[1]])
        else:
            user = '@'.join([f.bothify('#' * 16), 'anonymous.com'])


# SETUP
# Load questions
question_cols = list(question_cols_map.keys())
questions_df = dataiku.Dataset(question_ds_name).get_dataframe(columns=questions_cols)
questions_df = questions_df.rename(columns=question_cols_map)
questions_df = questions_df.loc[questions_df.qtype.isin(QuestionType.list_types())]

questions = parse_questions(questions_df.to_dict('records'))


# APP
# Define function to serve app; give Dash a factory, not an object
def serve_layout() -> html.Div:
    """Factory for app.layout so each browser session starts fresh."""
    alert = dbc.Alert(id="alert-submit", is_open=False, duration=4000, className="mt-2")
    
    return html.Div([
        build_survey_layout(questions),
        alert
    ])

# Set stylesheet
app.config.external_stylesheets = [dbc.themes.BOOTSTRAP]

# Define layout
app.layout = serve_layout

# Define submit callback
@app.callback(
    Output("alert-submit", "children"),
    Output("alert-submit", "color"),
    Output("alert-submit", "is_open"),
    Output("btn-submit-survey", "disabled"),
    Input("btn-submit-survey", "n_clicks"),
    # All free‑text / radio / checklist answers
    State({"role": "input", "qid": ALL}, "value"),
    State({"role": "input", "qid": ALL}, "id"),
    # All rank dropdowns (0..N per question)
    State({"role": "rank-select", "qid": ALL, "opt": ALL}, "value"),
    State({"role": "rank-select", "qid": ALL, "opt": ALL}, "id"),
    prevent_initial_call=True
)
def submit_survey(_n_clicks: int, scalar_values: List, scalar_ids: List[Dict], rank_values: List[int], rank_ids: List[Dict]): # -> Tuple[str, str, bool, bool]
    """Collect answers, save to managed folder, and notify user."""
    
    # Collect responses
    response: Dict[str, str] = {
        cid['qid']: json.dumps(val) if isinstance(val, list) else str(val or "") for val, cid in zip(scalar_values, scalar_ids)
    }
    
    # Flatten rank responses and find any duplicated ranks
    compact_ranks, dup_rank_qids = _normalise_rank_answers(rank_values, rank_ids)
    response.update(compact_ranks)
    
    # Find any missing response
    missing_qids = _find_missing_required(response)
    
    # Validate responses
    if missing_qids or dup_rank_qids:
        problems: List[str] = []
        if missing_qids:
            problems.append(f"Unanswered required question(s): {', '.join(missing_qids)}")
        if dup_rank_qids:
            problems.append(f"Duplicate ranks detected in: {', '.join(dup_rank_qids)}")
        
        message = "❗ " + "; ".join(problems)
        return message, "warning", True, False
    
    # Add metadata to responses
    response['response_id'] = uuid.uuid4().hex
    response['timestamp'] = datetime.datetime.utcnow().isoformat()
    response['respondent'] = _get_user(anonymous)
    
    # Save as JSON to managed folder
    try:
        folder = dataiku.Folder(folder_name)
        file_name = f"{response['response_id']}.json"
        folder.upload_data(file_name, json.dumps(response).encode('utf-8'))
        message = "✅ Thank you! Your response has been recorded."
        return message, "success", True, True
    except Exception as e:
        message = "🚫 Sorry, something went wrong while saving. Please try again."
        return message, "danger", True, False




# # PLUGIN
# # Get parameters
# print("--> Get parameters")
# webapp_config = get_webapp_config()
# survey_header = webapp_config['survey_header']
# survey_subheader = webapp_config['survey_subheader']
# question_ds_name = webapp_config['question_dataset']
# type_col = webapp_config['type_column']
# name_col = webapp_config['name_column']
# question_col = webapp_config['question_column']
# options_col = webapp_config['options_column']
# default_col = webapp_config['default_option_column']
# display_col = webapp_config['display_column']
# folder_name = webapp_config['folder_name']
# anonymous = webapp_config['anonymous']

# # SETUP
# # Map question type to dash component element
# print("--> Map question type to dash component element")
# ELEMENT_MAP = {
#     'choice': 'value',
#     'open': 'value',
#     'rank': 'data'
# }

# # Load questions
# print("--> Load questions")
# questions_cols = [type_col, name_col, question_col, options_col, default_col, display_col]
# questions_ds = dataiku.Dataset(question_ds_name)
# questions_df = questions_ds.get_dataframe(columns=questions_cols)
# questions_df = questions_df.loc[questions_df[type_col].isin(ELEMENT_MAP), ]

# # Build list of question card parameters
# print("--> Build list of question card parameters")
# questions = []
# for i, row in questions_df.iterrows():
#     questions.append({
#         'type': row[type_col],
#         'name': row[name_col],
#         'question': row[question_col],
#         'options': row[options_col].split(OPTIONS_DELIMITER) if row[type_col] != 'open' else None,
#         'default': row[default_col] if row[type_col] == 'choice' else None,
#         'display': row[display_col] if row[type_col] == 'rank' and row[display_col] else None
#     })

# # Get folder responses
# print("--> Get folder responses")
# folder = dataiku.Folder(folder_name)

# # Get faker object
# f = Faker('en_US')


# # APP
# # Define function to serve app; give Dash a factory, not an object
# def serve_layout():
#     # Build question cards
#     question_cards = []
#     for q, question in enumerate(questions):
#         question_cards.append(create_question_card(f'question-card-{q}', **question))
        
#     return html.Div([
#         dbc.Container(
#             [
#                 # Header
#                 dbc.Row(dbc.Col(html.Div(
#                     [
#                         html.H1(survey_header, className='text-center text-primary mb-4'),
#                         html.P(survey_subheader, className='text-center')
#                     ],
#                     className='py-4'
#                 ))),
#                 # Survey
#                 dbc.Row(dbc.Col(question_cards)),
#                 # Submit
#                 dbc.Row(dbc.Col(html.Div(dbc.Button(
#                     'Submit Responses',
#                     id='submit-button',
#                     color='primary',
#                     size='lg',
#                     n_clicks=0
#                 ), className='text-center'))),
#                 # Output
#                 dbc.Row(dbc.Col(html.Div(id='survey-output', className='mt-5')))
#             ],
#             fluid=True,
#             className='bg-light p-5'
#         )
#     ])
    

# # Set stylesheet
# app.config.external_stylesheets = [dbc.themes.BOOTSTRAP]

# # Define layout
# app.layout = serve_layout

# # CALLBACKS
# # Handle ranking question
# def register_callbacks_for_rank_question(cid):
#     @app.callback(
#         Output(cid, 'data'),
#         Input(cid, 'active_cell'),
#         State(cid, 'data'),
#         prevent_initial_call=True
#     )
#     def _callback(active_cell, current_data, _cid=cid):
#         print(f'--> Callback for {_cid}')
#         if not active_cell or not current_data:
#             return dash.no_update
        
#         row = active_cell['row']
#         col_id = active_cell['column_id']
        
#         df = pd.DataFrame(current_data)
        
#         if col_id == 'up' and row > 0:
#             df.iloc[row], df.iloc[row - 1] = df.iloc[row - 1].copy(), df.iloc[row].copy()
#         elif col_id == 'down' and row < len(df) - 1:
#             df.iloc[row], df.iloc[row + 1] = df.iloc[row + 1].copy(), df.iloc[row].copy()
#         else:
#             return dash.no_update
        
#         return df.to_dict('records')
    
# for q, question in enumerate(questions):
#     if question['type'] == 'rank':
#         register_callbacks_for_rank_question(f'question-card-{q}')

# # Handle submit button
# states = [
#     State(f'question-card-{q}', ELEMENT_MAP[question['type']])
#     for q, question in enumerate(questions)
# ]

# @app.callback(
#     Output('survey-output', 'children'),
#     Input('submit-button', 'n_clicks'),
#     *states,
#     prevent_initial_call=True
# )
# def submit_survey(n_clicks, *responses):
#     print(f'--> Callback for submit-survey')
#     if not n_clicks:
#         return dash.no_update
    
#     # Get user
#     print('--> Callback submit-survey: Get user')
#     client = dataiku.api_client()
#     headers = dict(request.headers)
#     auth_info_browser = client.get_auth_info_from_browser_headers(headers)
    
#     user = auth_info_browser['authIdentifier']
#     if anonymous:
#         if '@' in user:
#             user = '@'.join([f.bothify('#' * 16), user.split('@')[1]])
#         else:
#             user = '@'.join([f.bothify('#' * 16), 'hidden.com'])
    
#     # Build dataframe of responses
#     print('--> Callback submit-survey: Build dataframe of responses')
#     now = datetime.datetime.now()
#     response_data = []
#     for r, response in enumerate(responses):
#         question = questions[r]
#         if question['type'] == 'rank':
#             display = question['display'].lower()
#             df = pd.DataFrame({
#                 'option': [item[display] for item in response],
#                 'order': range(1, len(response) + 1)
#             })
            
#             for _, row in df.iterrows():
#                 response_data.append({
#                     'question_id': r,
#                     'type': question['type'],
#                     'name': question['name'],
#                     'question': question['question'],
#                     'response': row['option'],
#                     'value': row['order'],
#                     'user': user,
#                     'timestamp': now
#                 })
#         elif question['type'] == 'choice':
#             options = question['options']
#             if all(list(map(lambda o: VALUES_DELIMITER in o, options))):
#                 values = [o.split(VALUES_DELIMITER)[1] for o in options]
#                 options = [o.split(VALUES_DELIMITER)[0] for o in options]
#             else:
#                 values = [i for i in range(1, len(options) + 1)]
            
#             mapping = dict(zip(values, options))
            
#             response_data.append({
#                 'question_id': r,
#                 'type': question['type'],
#                 'name': question['name'],
#                 'question': question['question'],
#                 'response': mapping.get(response),
#                 'value': response,
#                 'user': user,
#                 'timestamp': now
#             })
#         elif question['type'] == 'open':
#             response_data.append({
#                 'question_id': r,
#                 'type': question['type'],
#                 'name': question['name'],
#                 'question': question['question'],
#                 'response': response if response else 'No response provided.',
#                 'value': len(response) if response else 0,
#                 'user': user,
#                 'timestamp': now
#             })
            
#     response_df = pd.DataFrame(response_data)
    
#     # Save responses
#     print('--> Callback submit-survey: Save responses')
#     user_str = '_at_'.join(user.split("@")).replace(".", "_")
#     filename = "-".join(["response", user_str, now.strftime("%Y%m%d-%H%M%S")]) + ".csv"
#     csv = response_df.to_csv(index=False).encode("utf-8")
#     folder.upload_data(filename, csv)
        
#     # Build confirmation message
#     print('--> Callback submit-survey: Build confirmation message')
#     cols = ['question_id', 'name', 'question']
#     display_df = (
#         response_df
#         .sort_values([*cols, 'value'])
#         .groupby(cols, as_index=False)
#         .agg({'response': lambda o: o.str.cat(sep=', ')})
#         .drop(columns=['question_id'])
#     )
    
#     parts = []
#     parts.append(html.H4('Thank you!', className='alert-heading'))
#     parts.append(html.P("Your submission has been successfully recorded. Here is a summary of your response."))
#     parts.append(html.Hr())
    
#     for _, row in display_df.iterrows():
#         name = row['name']
#         question = row['question']
#         question_response = row['response']
        
#         parts.append(html.H5(f"{name} - {question}"))
#         parts.append(html.P(question_response))
    
#     return dbc.Alert(parts, color='success', dismissable=True)
