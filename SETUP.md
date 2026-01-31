# Setup Guide

This guide walks you through setting up the Texter application from scratch.

## Step 1: Environment Setup

### Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

### Twilio Configuration

1. Go to [Twilio Console](https://console.twilio.com/)
2. Navigate to Account → API Keys & Tokens
3. Copy your Account SID and Auth Token
4. Get your Twilio phone number from Phone Numbers section

Add to `.env`:
```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
```

### Warp Platform Configuration

1. Sign up at [Warp Platform](https://app.warp.dev)
2. Navigate to Workspace Settings → API Keys
3. Create a new API key
4. Create or select an Environment:
   - Go to Environments section
   - Create a new environment or use an existing one
   - Note the Environment ID (UID)
5. Set up GitHub MCP server:
   - Go to MCP Servers section
   - Add GitHub MCP server
   - Authenticate with GitHub
   - Note the MCP server ID

Add to `.env`:
```
WARP_API_KEY=your_warp_api_key_here
WARP_ENVIRONMENT_ID=your_environment_id_here
WARP_MODEL_ID=claude-sonnet-4
```

## Step 3: Run the Application

### Start the FastAPI server

```bash
uvicorn main:app --reload --port 8000
```

Or run directly:

```bash
python main.py
```

The server will start at `http://localhost:8000`

- API Documentation: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

## Step 4: Expose Local Server (Development)

For local development, you need to expose your local server to the internet so Twilio can send webhooks.

### Using ngrok

1. Install ngrok: https://ngrok.com/download
2. Start ngrok:
   ```bash
   ngrok http 8000
   ```
3. Note the HTTPS forwarding URL (e.g., `https://abc123.ngrok.io`)

### Alternative: Use Warp's built-in tunnel

If Warp provides a tunneling feature, you can use that instead.

## Step 5: Configure Twilio Webhook

1. Go to [Twilio Console → Phone Numbers](https://console.twilio.com/phone-numbers)
2. Click on your phone number
3. Scroll to "Messaging" section
4. Set "A message comes in" webhook to:
   ```
   https://your-ngrok-url.ngrok.io/webhook/sms
   ```
5. Set HTTP method to `POST`
6. Save configuration

## Step 6: Test the Application

Send an SMS to your Twilio phone number with a message like:

```
Create a PR to fix the bug in the authentication module
```

The application will:
1. Receive the SMS via Twilio webhook
2. Validate the Twilio signature
3. Send the request to Warp AI
4. Warp will use the GitHub MCP server to create a PR
5. Send back a response with the task/PR link

## Troubleshooting

### Common Issues

**Issue: `ValidationError` on startup**
- Make sure all required environment variables are set in `.env`
- Check that variable names match exactly

**Issue: Twilio webhook fails with 403 Forbidden**
- Ensure your ngrok URL is correct in Twilio console
- Check that signature validation is working (it uses your auth token)

**Issue: Warp API errors**
- Verify your Warp API key is correct
- Ensure the environment ID exists and is accessible
- Check that GitHub MCP server is properly configured

**Issue: `warp-agent-sdk` import error**
- Make sure you've installed all dependencies: `pip install -r requirements.txt`
- Verify you're using Python 3.9 or higher

### Debugging

Enable debug mode by setting in `.env`:
```
DEBUG=true
```

Check logs in the console for detailed error messages.

## Production Deployment

For production, you should:

1. Use a proper hosting service (AWS, GCP, Heroku, etc.)
2. Set up HTTPS with a valid SSL certificate
3. Use environment variables from your hosting provider
4. Set up monitoring and logging
5. Consider rate limiting and authentication
6. Use a process manager like `gunicorn` or `supervisor`

Example production run with gunicorn:

```bash
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Twilio Python SDK](https://www.twilio.com/docs/libraries/python)
- [Warp Platform Docs](https://docs.warp.dev/)
- [Warp Python SDK](https://github.com/warpdotdev/warp-sdk-python)
