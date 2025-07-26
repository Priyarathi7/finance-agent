from flask import Flask, render_template, request, redirect, jsonify
import requests
import json

from dotenv import load_dotenv
import os
# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Constants
MCP_URL = "https://fi-mcp-dev-931723138542.us-central1.run.app/mcp/stream"
MCP_SESSION_ID = "mcp-session-594e48ea-fea1-40ef-8c52-7552dd9272af"
#GEMINI_API_KEY = "AIzaSyBPDULDOrhFbhrE3yhTvL5Ja_Xchg-nBOQ"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY");
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

def call_gemini_api(user_input, financial_context):
    context_text = f"""
    The user is seeking financial help or guidance. Here is their financial data:

    Bank Transactions: {json.dumps(financial_context.get('fetch_bank_transactions'), indent=2)}
    Credit Report: {json.dumps(financial_context.get('fetch_credit_report'), indent=2)}
    Mutual Fund Transactions: {json.dumps(financial_context.get('fetch_mf_transactions'), indent=2)}
    EPF Summary: {json.dumps(financial_context.get('fetch_epf_details'), indent=2)}
    Net Worth: {json.dumps(financial_context.get('fetch_net_worth'), indent=2)}
    Stock Transactiom: {json.dumps(financial_context.get('fetch_stock_transactions'), indent=2)}

    Now respond to the user's query based on the above context.
    Query: {user_input}
    """

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": context_text}]
            }
        ]
    }

    headers = {
        "Content-Type": "application/json"
    }

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
        user_input = request.json.get("query")
        financial_data = fetch_all_financial_data()
        gemini_response = call_gemini_api(user_input, financial_data)

        answer = gemini_response.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        return jsonify({"response": answer})
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
        print(f"Calling FI MCP tool for: {data_type}")
        res = call_mcp_tool(data_type)
        json_data = res.json()
        text_data = json.loads(json_data["result"]["content"][0]["text"])
        return jsonify(text_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

