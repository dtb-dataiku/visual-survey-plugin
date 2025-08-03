import pandas as pd

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

from visualsurvey.schema import QuestionType, SurveyQuestion


# FACTORY HELPERS
def _render_text_input(q: SurveyQuestion) -> html.Div:
    return html.Div([dbc.Textarea(
        id={"role": "input", "qid": q.id},
        placeholder="Your response...",
        value=q.default,
        required=r.required,
        debounce=True,
        className="w-100"
    )])

def _render_single_choice(q: SurveyQuestion) -> html.Div:
    options_df = pd.DataFrame({"label": q.options, "value": q.values})
    
    return html.Div([dbc.RadioItems(
        id={"role": "input", "qid": q.id},
        options=options_df.to_dict("records"),
        value=q.default,
        required=q.required,
        className="ps-2 d-block"
    )])

def _render_multi_choice(q: SurveyQuestion) -> html.Div:
    options_df = pd.DataFrame({"label": q.options, "value": q.values})
    
    return html.Div([dbc.Checklist(
        id={"role": "input", "qid": q.id},
        options=options_df.to_dict("records"),
        required=q.required,
        className="ps-2 d-block"
    )])

# VERY simple ranking: user selects a unique rank for each option via a dropdown.
# More sophisticated drag-and-drop would require dash-sortable, left as future work.
def _render_rank(q: SurveyQuestion) -> html.Div:
    rows = []
    for idx, option in enumerate(q.options, start=1):
        dropdown = dcc.Dropdown(
            id={"role": "rank-select", "qid": q.id, "option": option},
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
    card_body = _RENDERERS[q.qtype](q)
    
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


# # Create a dash component for ranking question
# def create_question_card(card_id, **params):
#     # Build a dash card for based on question parameters
#     qtype = params.get('type', None)
#     name = params.get('name', 'Question Name')
#     question = params.get('question', 'Question')
    
#     card = None
#     if qtype == 'choice':
#         options = params.get('options', None)
#         default = params.get('default', None)
        
#         if options:
#             # Parse list of options
#             if all(list(map(lambda o: VALUES_DELIMITER in o, options))):
#                 values = [o.split(VALUES_DELIMITER)[1] for o in options]
#                 options = [o.split(VALUES_DELIMITER)[0] for o in options]
#             else:
#                 values = [i for i in range(1, len(options) + 1)]
            
#             # Set default option to equivalent value
#             mapping = dict(zip(options, values))
#             default = mapping.get(default, default)
#             if default not in values:
#                 default = values[0]
                
#             # Create dataframe of options
#             options_df = pd.DataFrame({'label': options, 'value': values})

#             # Build card
#             card = dbc.Card(
#                 dbc.CardBody(
#                     [
#                         html.H4(name, className='card-title'),
#                         html.P(question, className='card-text'),
#                         dbc.RadioItems(
#                             id=card_id,
#                             options=options_df.to_dict('records'),
#                             value=default,
#                             labelClassName='mr-3',
#                             inputClassName='mr-1'
#                         )
#                     ]
#                 ),
#                 className='mb-4'
#             )
#     elif qtype == 'open':
#         # Build card
#         card = dbc.Card(
#             dbc.CardBody(
#                 [
#                     html.H4(name, className='card-title'),
#                     html.P(question, className='card-text'),
#                     dbc.Textarea(
#                         id=card_id,
#                         placeholder='Enter your response here...',
#                         style={'height': '100px', 'width': '400px'}
#                     )
#                 ]
#             ),
#             className='mb-4'
#         )
#     elif qtype == 'rank':
#         options = params.get('options', None)
#         display = params.get('display', 'Item')
        
#         if options:                
#             # Create dataframe of options
#             options_df = pd.DataFrame({display.lower(): options})
#             options_df['up'] = '🔼'
#             options_df['down'] = '🔽'
            
#             # Build list of columns
#             cols = [
#                 {'name': display, 'id': display.lower(), 'type': 'text'},
#                 {'name': 'Move Up', 'id': 'up', 'type': 'text'},
#                 {'name': 'Move Down', 'id': 'down', 'type': 'text'}
#             ]
        
#             card = dbc.Card(
#                 dbc.CardBody(
#                     [
#                         html.H4(name, className='card-title'),
#                         html.P(question, className='card-text'),
#                         dash_table.DataTable(
#                             id=card_id,
#                             columns=cols,
#                             data=options_df.to_dict('records'),
#                             style_cell={'textAlign': 'left', 'padding': '10px', 'fontFamily': 'sans-serif'},
#                             style_header={
#                                 'backgroundColor': 'rgb(230, 230, 230)',
#                                 'fontWeight': 'bold'
#                             },
#                             style_cell_conditional=[
#                                 {'if': {'column_id': 'up'}, 'textAlign': 'center', 'cursor': 'pointer', 'width': '120px'},
#                                 {'if': {'column_id': 'down'}, 'textAlign': 'center', 'cursor': 'pointer', 'width': '120px'}
#                             ]
#                         )
#                     ]
#                 ),
#                 className='mb-4'
#             )

#     return card
