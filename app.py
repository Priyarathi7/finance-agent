# app.py
from flask import Flask, render_template, request, redirect, jsonify
import requests
import json
from dotenv import load_dotenv
import os
import uuid
from firestore import create_conversation, add_message, get_messages, get_conversation

# Load environment variables
load_dotenv(".env")

app = Flask(__name__)

# Constants
MCP_URL = "https://fi-mcp-dev-931723138542.us-central1.run.app/mcp/stream"
MCP_SESSION_ID = "mcp-session-594e48ea-fea1-40ef-8c52-7552dd9272af"
#GEMINI_API_KEY = "AIzaSyBPDULDOrhFbhrE3yhTvL5Ja_Xchg-nBOQ"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

HEADERS = {
    "Content-Type": "application/json",
    "Mcp-Session-Id": MCP_SESSION_ID
}

logged_in = False


def call_mcp_tool(tool_name):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": {}
        }
    }
    response = requests.post(MCP_URL, headers=HEADERS, json=payload)
    return response

def fetch_all_financial_data():
    print("inside fetch_all_financial_data")
    tools = ["fetch_bank_transactions", "fetch_credit_report", "fetch_mf_transactions", "fetch_epf_details", "fetch_net_worth", "fetch_stock_transactions" ]
    result_data = {}
    for tool in tools:
        try:
            res = call_mcp_tool(tool)
            json_data = res.json()
            text_data = json.loads(json_data["result"]["content"][0]["text"])
            result_data[tool] = text_data
        except Exception as e:
            result_data[tool] = f"Error: {str(e)}"
    return result_data

def call_gemini_api(user_input, financial_context, history=[]):
    print("History:", history)
    system_preamble = """
You are a professional financial assistant designed to provide concise and insightful responses based only on the user’s financial data.

Instructions:
- Analyze the user's query in relation to their financial data. Always support answers with evidence from the context below.
- Respond clearly in plain English using concise bullet points (ideally no more than 5, but fewer is fine).
- Be analytical: identify trends, patterns, anomalies, or correlations where applicable.
- Use Bank Transactions to infer earnings and spending behavior. Try to estimate monthly salary and expenditure. Use these insights in your response.
- If monthly income or expenditure is unclear, politely ask the user to provide that information.
- If the user appears to be saving consistently and they want to acheive some financial goal, you may suggest possible investment options such as:
    • Fixed Deposits (assume 8% annual return)
    • Mutual Funds (assume 12% annual return)
- When projecting for future financial goals (like buying a car or house), account for inflation:
    • Use an annual inflation rate of 6% for estimating rise in costs and living expenses.
- Avoid vague or generic financial advice.
- If required data is missing, mention what's missing and ask the user to provide it.
- Try to reach a conclusive suggestion for user once you get the income and expenditure information from user.
- If the query is vague or not directly related to financial data, ask the user to clarify or rephrase.
"""

    # Format history as list of message dicts
    formatted_history = [
        {"role": msg["role"], "parts": [{"text": msg["text"]}]}
        for msg in history
    ]

    formatted_history = [{"role": "user", "parts": [{"text": system_preamble}]}] + formatted_history

    # Initial message with all financial context
    context_text = f"""
Below is the user's financial data:

Bank Transactions: {json.dumps(financial_context.get('fetch_bank_transactions'), indent=2)}
Credit Report: {json.dumps(financial_context.get('fetch_credit_report'), indent=2)}
Mutual Fund Transactions: {json.dumps(financial_context.get('fetch_mf_transactions'), indent=2)}
EPF Summary: {json.dumps(financial_context.get('fetch_epf_details'), indent=2)}
Net Worth: {json.dumps(financial_context.get('fetch_net_worth'), indent=2)}
Stock Transactions: {json.dumps(financial_context.get('fetch_stock_transactions'), indent=2)}
"""

    # Construct the full conversation
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": context_text}]},
            *formatted_history,
            {"role": "user", "parts": [{"text": user_input}]}
        ]
    }

    headers = {"Content-Type": "application/json"}

    response = requests.post(
        f"{GEMINI_URL}?key={GEMINI_API_KEY}",
        headers=headers,
        json=payload
    )
    return response.json()


@app.route('/')
def home():
    global logged_in
    if not logged_in:
        res = call_mcp_tool("fetch_bank_transactions")
        try:
            data = res.json()
            text_json = json.loads(data["result"]["content"][0]["text"])
            if text_json.get("status") == "login_required":
                login_url = text_json["login_url"].replace("http://localhost:8080", "https://fi-mcp-dev-931723138542.us-central1.run.app")
                return render_template('login.html', login_url=login_url)
        except Exception as e:
            return f"Error parsing login response: {str(e)}"
    return render_template('dashboard.html')

@app.route('/login_done')
def login_done():
    global logged_in
    logged_in = True
    return redirect('/')

@app.route('/ask_gemini', methods=['POST'])
def ask_gemini():
    try:
        req = request.get_json()
        user_input = req.get("query")
        history = req.get("history", [])
        conversation_id = request.json.get("conversation_id")
        if not conversation_id:
            conversation_id = create_conversation(None)
        add_message(conversation_id, user_input, "user")
        financial_data = fetch_all_financial_data()
        # firebase_history = get_conversation(conversation_id)
        # print("firebase_history:", firebase_history)
        # formatted_history = []
        # for msg in firebase_history:
        #     if msg.get("role") == "user":
        #         formatted_history.append({"role": "user", "text": msg.get("text")})
        #     elif msg.get("role") == "agent":
        #         formatted_history.append({"role": "model", "text": msg.get("text")})
        # print("Formatted history:",formatted_history)

        #gemini_response = call_gemini_api(user_input, financial_data, formatted_history)
        gemini_response = call_gemini_api(user_input, financial_data, history)

        answer = gemini_response.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        add_message(conversation_id, answer, "agent")
        return jsonify({"response": answer, "conversation_id": conversation_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/financial_data')
def financial_data():
    return render_template('financial_data.html')

@app.route('/api/financial_info')
def financial_info():
    data_type = request.args.get('type')
    tools = {
        "fetch_bank_transactions",
        "fetch_credit_report",
        "fetch_mf_transactions",
        "fetch_epf_details",
        "fetch_net_worth",
        "fetch_stock_transactions"
    }

    if data_type not in tools:
        return jsonify({"error": "Invalid type"}), 400
    try:
        res = call_mcp_tool(data_type)
        json_data = res.json()
        text_data = json.loads(json_data["result"]["content"][0]["text"])
        return jsonify(text_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/conversations", methods=["GET"])
def fetch_conversations():
    return jsonify(get_messages())


@app.route("/messages/<conversation_id>", methods=["GET"])
def fetch_messages(conversation_id):
    return jsonify(get_messages(conversation_id))


if __name__ == '__main__':
    app.run(debug=True)
