from flask import Flask, render_template, request, redirect, jsonify
import requests
import json

app = Flask(__name__)

MCP_URL = "https://fi-mcp-dev-931723138542.us-central1.run.app/mcp/stream"
MCP_SESSION_ID = "mcp-session-594e48ea-fea1-40ef-8c52-7552dd9272af"
HEADERS = {
    "Content-Type": "application/json",
    "Mcp-Session-Id": MCP_SESSION_ID
}

# Store login status
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

@app.route('/')
def home():
    global logged_in
    if not logged_in:
        # Initial MCP request to check login status
        res = call_mcp_tool("fetch_bank_transactions")
        try:
            data = res.json()
            text_json = json.loads(data["result"]["content"][0]["text"])
            if text_json.get("status") == "login_required":
                # Replace localhost with live domain
                login_url = text_json["login_url"].replace("http://localhost:8080", "https://fi-mcp-dev-931723138542.us-central1.run.app")
                return render_template('login.html', login_url=login_url)
        except Exception as e:
            return f"Error parsing response: {str(e)}"
    return render_template('dashboard.html')

@app.route('/login_done')
def login_done():
    global logged_in
    logged_in = True
    return redirect('/')

@app.route('/fetch/<tool>')
def fetch_tool_data(tool):
    try:
        res = call_mcp_tool(tool)
        return jsonify(res.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

