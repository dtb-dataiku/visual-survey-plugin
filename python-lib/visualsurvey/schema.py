from typing import List

import dash
import dash_bootstrap_components as dbc
import pandas as pd

from dash import dcc, html

from .survey import QuestionType, SurveyQuestion


# FACTORY HELPERS
def _render_text_input(q: SurveyQuestion) -> html.Div:
    return html.Div([dbc.Textarea(
        id={"role": "input", "qid": q.id},
        placeholder="Your response...",
        value=q.default,
        debounce=True,
        className="w-100"
    )])

def _render_single_choice(q: SurveyQuestion) -> html.Div:
    options_df = pd.DataFrame({"label": q.options, "value": q.options})
    
    return html.Div([dbc.RadioItems(
        id={"role": "input", "qid": q.id},
        options=options_df.to_dict("records"),
        value=q.default,
        className="ps-2 d-block"
    )])

def _render_multi_choice(q: SurveyQuestion) -> html.Div:
    options_df = pd.DataFrame({"label": q.options, "value": q.options})
    
    return html.Div([dbc.Checklist(
        id={"role": "input", "qid": q.id},
        options=options_df.to_dict("records"),
        className="ps-2 d-block"
    )])

# VERY simple ranking: user selects a unique rank for each option via a dropdown.
# More sophisticated drag-and-drop would require dash-sortable, left as future work.
def _render_rank(q: SurveyQuestion) -> html.Div:
    rows = []
    for idx, option in enumerate(q.options, start=1):
        dropdown = dcc.Dropdown(
            id={"role": "rank-select", "qid": q.id, "opt": option},
            options=[{"label": str(i), "value": i} for i in range(1, len(q.options) + 1)],
            value=idx,
            clearable=False,
            style={"width": "4rem"}
        )
        rows.append(
            html.Div(
                [html.Span(option, className="flex-grow-1"), dropdown],
                className="d-flex align-items-center mb-2"
            )
        )
        
    hint_text = "Assign each item a unique rank (1 = highest). Duplicate ranks will be flagged."
    hint = html.Small(hint_text, className="text-secondary fst-italic")

# Map question type to renderer
_RENDERERS = {
    QuestionType.TEXT: _render_text_input,
    QuestionType.SINGLE_CHOICE: _render_single_choice,
    QuestionType.MULTI_CHOICE: _render_multi_choice,
    QuestionType.RANK: _render_rank
}

def create_question_card(q: SurveyQuestion) -> dbc.Card:
    """Return a Bootstrap card that encapsulates the question and its options."""

    card_body = _RENDERERS[q.question_type](q)
    
    return dbc.Card(
        [
            dbc.CardHeader(html.H5(q.label, className="mb-0")),
            dbc.CardBody(body)
        ],
        className="mb-4 shadow-sm"
    )

def build_survey_layout(questions: List[SurveyQuestion]) -> html.Div:
    """Wrap all question cards in container."""
    
    cards = [create_question_card(q) for q in questions]
    submit_button = dbc.Button(
        "Submit",
        id="btn-submit-survey",
        color="primary",
        className="mt-3",
        n_clicks=0
    )
    
    return html.Div(
        cards + [submit_button],
        className="mx-auto my-4",
        style={"maxWidth": "850px"}
    )