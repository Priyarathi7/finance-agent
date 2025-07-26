from flask import Flask, request, jsonify
import vertexai
from vertexai.preview.generative_models import GenerativeModel
import requests

vertexai.init(project="protean-cove-466413-v7", location="us-central1")

app = Flask(__name__)
model = GenerativeModel("gemini-2.0-flash")

MCP_SERVER_URL = "https://fi-mcp-dev-931723138542.us-central1.run.app/mcp/stream"

@app.route("/", methods=["GET"])
def index():
    return "Your local MCP-Gemini Flask server is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        user_input = data.get("prompt", "What is my balance?")
        session_id = data.get("session_id", "default-session")

        # Step 1: Interpret prompt with Gemini
        gemini_response = model.generate_content(user_input)
        prompt_understood = gemini_response.text

        # Step 2: Call MCP server
        mcp_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "fetch_bank_transactions",
                "arguments": {}
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Mcp-Session-Id": session_id
        }
        mcp_response = requests.post(MCP_SERVER_URL, json=mcp_payload, headers=headers)
        print(mcp_response)
        mcp_data = mcp_response.json()

        # Step 3: Parse response
        if "result" in mcp_data:
            content = mcp_data["result"]["content"]
            if content and content[0]["type"] == "text":
                text_data = content[0]["text"]
                if "\"status\": \"login_required\"" in text_data:
                    # Login required
                    import json
                    try:
                        login_info = json.loads(text_data)
                        return jsonify({
                            "gemini_response": prompt_understood,
                            "status": "login_required",
                            "message": login_info.get("message", "Login is required."),
                            "login_url": login_info.get("login_url")
                        })
                    except json.JSONDecodeError:
                        return jsonify({
                            "gemini_response": prompt_understood,
                            "status": "login_required",
                            "raw_text": text_data
                        })
                else:
                    # Already logged in, return actual financial data
                    return jsonify({
                        "gemini_response": prompt_understood,
                        "status": "success",
                        "financial_data": text_data
                    })

        return jsonify({
            "gemini_response": prompt_understood,
            "status": "unknown",
            "response": mcp_data
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("Starting Flask app...")
    app.run(debug=True)
