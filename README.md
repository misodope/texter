# Texter - SMS to GitHub PR Bot

A FastAPI application that receives SMS messages via Twilio webhooks, processes them using Warp AI, and creates GitHub Pull Requests via MCP (Model Context Protocol).

## Architecture

```
Mobile → Twilio → FastAPI Webhook → Warp O2 (MCP) → GitHub PRs
                                    ↓
                            SMS Response with PR Link
```

## Features

- Secure Twilio webhook integration with signature validation
- SMS-based PR creation workflow
- Warp AI integration via MCP for GitHub operations
- Automated response with PR links

## Prerequisites

- Python 3.9+
- Twilio account with phone number
- Warp account with API key
- GitHub account (connected to Warp via MCP)
- ngrok (for local development)

## Setup

1. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials:
# - Twilio account SID, auth token, and phone number
# - Warp API key, environment ID, and model ID
```

4. Run the server:
```bash
uvicorn main:app --reload --port 8000
```

5. Expose local server (development only):
```bash
ngrok http 8000
```

6. Configure Twilio webhook:
   - Go to Twilio Console → Phone Numbers
   - Set webhook URL to: `https://your-ngrok-url.ngrok.io/webhook/sms`

7. Set up Warp Platform:
   - Sign up for Warp at https://app.warp.dev
   - Create an API key in your Warp workspace settings
   - Create or configure an environment with GitHub access
   - Set up the GitHub MCP server in your Warp workspace
   - Add your credentials to `.env`

## Usage

Send an SMS to your Twilio number with instructions for creating a PR. The bot will:
1. Validate the Twilio request signature
2. Process your message with Warp AI
3. Create a GitHub PR via MCP
4. Send back a response with the PR link

## Project Structure

```
texter/
├── main.py              # FastAPI application entry point
├── app/
│   ├── __init__.py
│   ├── config.py        # Configuration management
│   ├── routes/
│   │   └── webhook.py   # Twilio webhook handlers
│   ├── services/
│   │   ├── twilio.py    # Twilio integration
│   │   └── warp.py      # Warp/MCP integration
│   └── utils/
│       └── validators.py # Request validation
├── requirements.txt
├── .env.example
└── README.md
```

## Development

- FastAPI auto-documentation: `http://localhost:8000/docs`
- ReDoc documentation: `http://localhost:8000/redoc`

## Security

- All Twilio requests are validated using signature verification
- Environment variables for sensitive credentials
- No secrets in version control
