import datetime
import json
import uuid

from pathlib import Path
from typing import Dict, List, Tuple

import dataiku
import dash
import dash_bootstrap_components as dbc
import pandas as pd

from dataiku.customwebapp import *
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State, ALL
from flask import request

from visualsurvey.schema import build_survey_layout
from visualsurvey.survey import QuestionType, parse_questions


# CONFIGURATION
# Get plugin parameters
webapp_config = get_webapp_config()

SURVEY_HEADER = webapp_config['survey_header']
SURVEY_SUBHEADER = webapp_config['survey_subheader']
QUESTION_DATASET_NAME = webapp_config['question_dataset']
RESPONSE_FOLDER_NAME = webapp_config['folder_name']
ANONYMOUS = webapp_config['anonymous']

QUESTION_COLS_MAP = {
    webapp_config['type_column']: 'question_type',
    webapp_config['name_column']: 'id',
    webapp_config['question_column']: 'label',
    webapp_config['options_column']: 'options',
    webapp_config['default_option_column']: 'default',
    webapp_config['required_column']: 'required'
}


# HELPER FUNCTIONS
def load_questions_dataset(dataset_name: str, column_map: Dict[str, str] = QUESTION_COLS_MAP) -> pd.DataFrame:
    """Load questions from dataset. Filter out missing or invalid question types."""
    
    cols = list(column_map.values())
    
    allowed_types = QuestionType.list_types()
    
    df = dataiku.Dataset(dataset_name).get_dataframe()
    df = df.rename(columns=column_map)
    
    df = (
        df
        .dropna(subset=['question_type', 'id', 'label'])
        .loc[df.question_type.isin(allowed_types), cols]
        .fillna({'options': '', 'default': '', 'required': 'False'})
    )
    
    return df

def normalize_multi_choice_responses() -> Dict[str, str]:
    """Convert multi-choice selections into a single string per question."""
    pass

def normalize_rank_responses(rank_values: List[int], rank_ids: List[Dict]) -> Dict[str, str]:
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
    for qid, rankings in by_question.items():
        ordered_opts = [opt for opt, _ in sorted(rankings.items(), key=lambda r: r[1])]
        compact[qid] = ' | '.join(ordered_opts)
        
    return compact, duplicates

def find_missing_required(response: Dict[str, str]) -> List[str]:
    """Return list of missing question IDs for required questions left unanswered."""
    
    missing: List[str] = []
    for q in QUESTIONS:
        if not q.required:
            continue
            
        if response.get(q.id, "") in ("", "[]"):
            missing.append(q.id)
            
    return missing


def get_user(anonymous: bool) -> str:
    """Gets Dataiku identifier or anonymous identifier."""
    
    headers = dict(request.headers)
    auth_info_browser = dataiku.api_client().get_auth_info_from_browser_headers(headers)
    
    user = auth_info_browser['authIdentifier']
    if anonymous:        
        if '@' in user:
            user = '@'.join([uuid.uuid4().hex, user.split('@')[1]])
        else:
            user = '@'.join([uuid.uuid4().hex, 'hidden.unk'])
            
    return user


# SETUP
# Load questions
questions_df = load_questions_dataset(QUESTION_DATASET_NAME)
QUESTIONS = parse_questions(questions_df.to_dict('records'))


# APP
# Define function to serve app; give Dash a factory, not an object
def serve_layout() -> html.Div:
    """Factory for app.layout so each browser session starts fresh."""
    
    header = html.Header(
        dbc.Container(
            [
                html.H1(SURVEY_HEADER, className="display-5 mb-1"),
                html.P(SURVEY_SUBHEADER, className="lead mb-0")
            ],
            fluid=False
        ),
        className="py-4 bg-light border-bottom sticky-top"
    )
    content = dbc.Container(build_survey_layout(QUESTIONS), fluid=True, className="py-4")
    
    return html.Div([header, content])

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
def submit_survey(_n_clicks: int, scalar_values: List, scalar_ids: List[Dict], rank_values: List[int], rank_ids: List[Dict]) -> Tuple[str, str, bool, bool]:
    """Collect answers, save to managed folder, and notify user."""
    
    # Collect responses
    response: Dict[str, str] = {
        cid['qid']: json.dumps(val) if isinstance(val, list) else str(val or "") for val, cid in zip(scalar_values, scalar_ids)
    }
    
    # Flatten rank responses and find any duplicated ranks
    compact_ranks, dup_rank_qids = normalize_rank_responses(rank_values, rank_ids)
    response.update(compact_ranks)
    
    # Find any missing response
    missing_qids = find_missing_required(response)
    
    # Validate responses
    if missing_qids or dup_rank_qids:
        problems: List[str] = []
        if missing_qids:
            problems.append(f"Unanswered required question(s): {', '.join(missing_qids)}")
        if dup_rank_qids:
            problems.append(f"Duplicate ranks detected in: {', '.join(dup_rank_qids)}")
        
        message = "❗ " + "\n".join(problems)
        return message, "warning", True, False
    
    # Add metadata to responses
    response['response_id'] = uuid.uuid4().hex
    response['timestamp'] = datetime.datetime.utcnow().isoformat()
    response['respondent'] = get_user(ANONYMOUS)
    
    # Save as JSON to managed folder
    try:
        folder = dataiku.Folder(RESPONSE_FOLDER_NAME)
        file_name = f"{response['response_id']}.json"
        folder.upload_data(file_name, json.dumps(response).encode('utf-8'))
        message = "✅ Thank you! Your response has been recorded."
        return message, "success", True, True
    except Exception as e:
        message = "🚫 Sorry, something went wrong while saving. Please try again."
        return message, "danger", True, False