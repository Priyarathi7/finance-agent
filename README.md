💰 AI-Powered Financial Assistant

This is a smart AI financial assistant that integrates with the FI MCP server to analyze a user's complete financial data (bank transactions, credit report, investments, net worth, etc.) and provide personalized, actionable financial advice through an interactive chat interface.

🚀 Features

🔐 Secure login via the FI MCP server

💬 Intelligent chat interface for financial advice

📊 Dashboard to view all your financial data in one place

🧠 AI-driven responses based on user's real-time financial data

💾 Tracks spending, savings, income, investments, and more

💪 Setup Instructions

1. Clone the Repository

git clone https://github.com/yourusername/ai-financial-assistant.git
cd ai-financial-assistant

2. Create the serviceAccountKey.json File

This file is used to connect to Firebase. Place it in the root directory of the project.

✅ Sample Format:

{
  "type": "service_account",
  "project_id": "your-firebase-project-id",
  "private_key_id": "somekeyid",
  "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR-PRIVATE-KEY\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-abc12@your-project.iam.gserviceaccount.com",
  "client_id": "someclientid",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-abc12%40your-project.iam.gserviceaccount.com"
}

3. Create a .env File

This file stores your Gemini API key.

✅ Sample Format:

GEMINI_API_KEY=your-gemini-api-key-here

4. Install Dependencies

pip install -r requirements.txt

Make sure the following are installed:

Flask

firebase-admin

python-dotenv

requests

(You can generate a requirements.txt with pip freeze > requirements.txt if needed.)

5. Run the AI Assistant

python app.py

🧑‍💼 How It Works

When you run the app, it opens a login page that initiates the login flow via the FI MCP server.

Once logged in successfully, you'll be redirected to a chat interface.

Here, you can interact with the AI assistant and ask questions like:

"Can I afford to buy a car in 2 years?"

"How much am I saving per month?"

"Suggest investment options based on my income and expenses"

Navigate to the dashboard to view all your financial data in one place.

📌 Project Structure

├── app.py
├── templates/
│   ├── dashboard.html
│   ├
│   └── login.html
├── static/
│   ├── css/
│   └── js/
├── serviceAccountKey.json   <-- 🔐 Firebase credentials
├── .env                     <-- 🔑 Gemini API key
└── README.md

🔮 Future Improvements

Add goal-setting features (e.g. saving for a home, travel)

Proactive alerts and insights

Integration with WhatsApp/Email for periodic summaries

Visualization of financial progress

Multi-user support and analytics dashboard

