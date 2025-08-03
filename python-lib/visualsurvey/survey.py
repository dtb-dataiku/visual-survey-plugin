import pandas as pd

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

from visualsurvey.schema import QuestionType, SurveyQuestion


# FACTORY HELPERS










# Create a dash component for ranking question
def create_question_card(card_id, **params):
    # Build a dash card for based on question parameters
    qtype = params.get('type', None)
    name = params.get('name', 'Question Name')
    question = params.get('question', 'Question')
    
    card = None
    if qtype == 'choice':
        options = params.get('options', None)
        default = params.get('default', None)
        
        if options:
            # Parse list of options
            if all(list(map(lambda o: VALUES_DELIMITER in o, options))):
                values = [o.split(VALUES_DELIMITER)[1] for o in options]
                options = [o.split(VALUES_DELIMITER)[0] for o in options]
            else:
                values = [i for i in range(1, len(options) + 1)]
            
            # Set default option to equivalent value
            mapping = dict(zip(options, values))
            default = mapping.get(default, default)
            if default not in values:
                default = values[0]
                
            # Create dataframe of options
            options_df = pd.DataFrame({'label': options, 'value': values})

            # Build card
            card = dbc.Card(
                dbc.CardBody(
                    [
                        html.H4(name, className='card-title'),
                        html.P(question, className='card-text'),
                        dbc.RadioItems(
                            id=card_id,
                            options=options_df.to_dict('records'),
                            value=default,
                            labelClassName='mr-3',
                            inputClassName='mr-1'
                        )
                    ]
                ),
                className='mb-4'
            )
    elif qtype == 'open':
        # Build card
        card = dbc.Card(
            dbc.CardBody(
                [
                    html.H4(name, className='card-title'),
                    html.P(question, className='card-text'),
                    dbc.Textarea(
                        id=card_id,
                        placeholder='Enter your response here...',
                        style={'height': '100px', 'width': '400px'}
                    )
                ]
            ),
            className='mb-4'
        )
    elif qtype == 'rank':
        options = params.get('options', None)
        display = params.get('display', 'Item')
        
        if options:                
            # Create dataframe of options
            options_df = pd.DataFrame({display.lower(): options})
            options_df['up'] = '🔼'
            options_df['down'] = '🔽'
            
            # Build list of columns
            cols = [
                {'name': display, 'id': display.lower(), 'type': 'text'},
                {'name': 'Move Up', 'id': 'up', 'type': 'text'},
                {'name': 'Move Down', 'id': 'down', 'type': 'text'}
            ]
        
            card = dbc.Card(
                dbc.CardBody(
                    [
                        html.H4(name, className='card-title'),
                        html.P(question, className='card-text'),
                        dash_table.DataTable(
                            id=card_id,
                            columns=cols,
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
