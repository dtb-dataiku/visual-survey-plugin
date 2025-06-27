import dash
from dash import html, dash_table
import dash_bootstrap_components as dbc
import pandas as pd


# 'type'
# 'name'
# 'question'
# 'options'
# 'default'
# 'display'

# Create a dash component for ranking question
def create_question_card(card_id, **params):
    # Build a dash card for based on question parameters
    qtype = params.get('type', None)
    name = params.get('name', 'Question Name')
    question = params.get('question', 'Question')
    
    card = None
    if qtype == 'choice':
        options = params.get('options', None)
        if options:
            # Parse list of options
            
            default = params.get('default', options[0])

            options_df = params.get('options_df', pd.DataFrame({'label': ['Option'], 'value': [1]}))
            value = params.get('value', options_df.value.min())

            card = dbc.Card(
                dbc.CardBody(
                    [
                        html.H4(name, className='card-title'),
                        html.P(question, className='card-text'),
                        dbc.RadioItems(
                            id=card_id,
                            options=options_df.to_dict('records'),
                            value=value,
                            labelClassName='mr-3',
                            inputClassName='mr-1'
                        )
                    ]
                ),
                className='mb-4'
            )
    elif question_type == 'open':
        header = params.get('header', 'Header')
        subheader = params.get('subheader', 'Subheader')
        
        card = dbc.Card(
            dbc.CardBody(
                [
                    html.H4(header, className='card-title'),
                    html.P(subheader, className='card-text'),
                    dbc.Textarea(
                        id=card_id,
                        placeholder='Enter your response here...',
                        style={'height': '100px', 'width': 'auto'}
                    )
                ]
            ),
            className='mb-4'
        )
    elif question_type == 'rank':
        header = params.get('header', 'Header')
        subheader = params.get('subheader', 'Subheader')
        name = params.get('name', 'Name')
        options_df = params.get('options_df', pd.DataFrame({name: ['Option']}))
        
        card = dbc.Card(
            dbc.CardBody(
                [
                    html.H4(header, className='card-title'),
                    html.P(subheader, className='card-text'),
                    dash_table.DataTable(
                        id=card_id,
                        columns=[
                            {'name': name, 'id': name.lower(), 'type': 'text'},
                            {'name': 'Move Up', 'id': 'up', 'type': 'text'},
                            {'name': 'Move Down', 'id': 'down', 'type': 'text'}
                        ],
                        data=options_df.to_dict('records'),
                        style_cell={'textAlign': 'left', 'padding': '10px', 'fontFamily': 'sans-serif'},
                        style_header={
                            'backgroundColor': 'rgb(230, 230, 230)',
                            'fontWeight': 'bold'
                        },
                        style_cell_conditional=[
                            {'if': {'column_id': 'up'}, 'textAlign': 'center', 'cursor': 'pointer', 'width': '120px'},
                            {'if': {'column_id': 'down'}, 'textAlign': 'center', 'cursor': 'pointer', 'width': '120px'}
                        ]
                    )
                ]
            ),
            className='mb-4'
        )


    return card
