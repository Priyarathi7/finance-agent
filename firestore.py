import re
import firebase_admin
from firebase_admin import credentials, firestore
from flask import jsonify
from datetime import datetime
import uuid
import json

# Initialize Firebase app only once
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

# Create Firestore client
db = firestore.client()

# Global conversation_id for the app session
GLOBAL_CONVERSATION_ID = str(uuid.uuid4())

def create_conversation(conversation_id=None):
    if conversation_id is None:
        conversation_id = GLOBAL_CONVERSATION_ID

    print("Creating conversation", conversation_id)
    db.collection("conversations").document(conversation_id).set({
        "conversation_id": conversation_id,
        "created_at": datetime.utcnow(),
        "last_updated": datetime.utcnow()
    }) 
    return conversation_id

def add_message(conversation_id, message_text, sender):
    db.collection("messages").document(str(uuid.uuid4())).set({
        "conversation_id": conversation_id,
        "role": "user",
        "text": message_text,
        "timestamp": firestore.SERVER_TIMESTAMP
    })
    # db.collection("conversations").document(conversation_id).update({
    #     "last_updated": datetime.utcnow()
    # })


def get_messages():
    messages_ref = db.collection("messages")
    messages = messages_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).stream()

    conversations = {}
    for msg in messages:
        msg_data = msg.to_dict()
        conv_id = msg_data["conversation_id"]
        if conv_id not in conversations:
            conversations[conv_id] = {
                "conversation_id": conv_id,
                "latest_message": msg_data["text"],
                "last_updated": msg_data["timestamp"]
            }

    sorted_conversations = sorted(conversations.values(), key=lambda x: x["last_updated"], reverse=True)
    return sorted_conversations
