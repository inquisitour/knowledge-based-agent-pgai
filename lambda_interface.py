import os
import json
from data_processing import DBops
from agent import ResponseAgent

def create_response_card(follow_up_suggestions, used_buttons):
    dynamic_buttons = [
        {"text": suggestion, "value": suggestion} 
        for suggestion in follow_up_suggestions if suggestion not in used_buttons
    ]

    static_buttons = [
        {"text": "Main Menu", "value": "main menu"}
    ]

    all_buttons = dynamic_buttons + static_buttons
    available_buttons = all_buttons[:5]  # Limit to 5 buttons per card

    if not available_buttons:
        available_buttons = all_buttons
        used_buttons = []

    return {
        "version": 1,
        "contentType": "application/vnd.amazonaws.card.generic",
        "genericAttachments": [{
            "title": "More Information",
            "subTitle": "Choose an option to learn more:",
            "buttons": available_buttons
        }]
    }, used_buttons

def lambda_handler(event, context):
    print("Lambda handler started")
    agent = ResponseAgent()
    print("Agent initialized!")

    session_attributes = event.get('sessionAttributes', {})
    used_buttons = session_attributes.get('used_buttons', '').split(',') if session_attributes.get('used_buttons') else []
    chat_history = json.loads(session_attributes.get('chat_history', '[]'))

    print(f"This is the event: {event}")

    if "currentIntent" in event.keys():
        user_query = event['currentIntent']['slots'].get('Gynequery')
    else:
        # Function URL post event
        body = event['body']
        body = body.replace("'",'"')
        body_dict = json.loads(body)
        
        # Client ID
        client_id = body_dict['client_id'] 
        
        # User Query
        user_query = body_dict['user_query'] 
        
        print(f"Client ID: {client_id},  User Query: {user_query}")
    
    #user_query = "what is glaucoma???"
    
    print(f'User query from slot: {user_query}')
    
    print
    
    if not user_query:
        user_query = event.get('inputTranscript')
    if not user_query:
        user_query = "Start Conversation"
    elif user_query not in used_buttons and user_query != "main menu":
        used_buttons.append(user_query)

    print(f"Received query: {user_query}")
    chat_history.append({"role": "user", "content": user_query})
    print(chat_history)

    try:
        response_message = agent.answer_question(user_query, chat_history)
        chat_history.append({"role": "assistant", "content": response_message})
        print("Response generated")

        follow_up_suggestions = agent.extract_follow_up_questions(response_message)
        responseCard, updated_used_buttons = create_response_card(follow_up_suggestions, used_buttons)

        session_attributes['used_buttons'] = ','.join(updated_used_buttons)
        session_attributes['chat_history'] = json.dumps(chat_history[-12:])  # Keep only last 12 interactions

        print("Returning response from Lambda")
        response = {
            "sessionAttributes": session_attributes,
            "dialogAction": {
                "type": "Close",
                "fulfillmentState": "Fulfilled",
                "message": {
                    "contentType": "PlainText",
                    "content": response_message
                }
            }
        }

        if user_query:
            response["dialogAction"]["responseCard"] = responseCard
        
        print(f"Returning response: {response}")

        return response

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return {
            "dialogAction": {
                "type": "Close",
                "fulfillmentState": "Failed",
                "message": {
                    "contentType": "PlainText",
                    "content": "I'm sorry, but I encountered an error. Please try again."
                }
            }
        }

# If you need to include the S3 and database operations, uncomment and modify these lines:
# S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
# S3_FILE_KEY = os.getenv("S3_FILE_KEY")
# db_ops = DBops()
# db_ops.setup_database()
# In the lambda_handler function, add:
# db_ops.process_file_from_s3(S3_BUCKET_NAME, S3_FILE_KEY)