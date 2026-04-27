# Google Nest Integration Setup

This guide will help you set up your JARVIS agent to read room temperature from your Google Nest thermostat.

## Prerequisites

1. Google Nest thermostat
2. Google Cloud Platform account
3. OAuth 2.0 credentials for Google Smart Device Management API

## Step 1: Enable Google Smart Device Management API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the "Smart Device Management API"
4. Go to "Credentials" and create OAuth 2.0 credentials
5. Download the credentials JSON file

## Step 2: Get Authorization Code

You'll need to get an authorization code from Google:

```bash
# Replace with your client ID and redirect URI
https://accounts.google.com/o/oauth2/v2/auth?client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:8000&response_type=code&scope=https://www.googleapis.com/auth/sdm.service&access_type=offline&prompt=consent
```

## Step 3: Exchange Authorization Code for Access Token

```bash
# Exchange the code for an access token
curl -X POST "https://oauth2.googleapis.com/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "code=AUTHORIZATION_CODE" \
  -d "redirect_uri=http://localhost:8000" \
  -d "grant_type=authorization_code"
```

## Step 4: Get Your Device ID

```bash
# List all devices
curl -X GET "https://smartdevicemanagement.googleapis.com/v1/enterprises/YOUR_PROJECT_ID/devices" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Step 5: Configure Environment Variables

Create a `.env` file in the agent directory:

```bash
# Google Nest Configuration
GOOGLE_NEST_ACCESS_TOKEN="your_access_token_here"
GOOGLE_NEST_PROJECT_ID="your_google_project_id"
GOOGLE_NEST_DEVICE_ID="your_device_id_here"
GOOGLE_NEST_CLIENT_ID="your_client_id"
GOOGLE_NEST_CLIENT_SECRET="your_client_secret"
```

## Step 6: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 7: Test the Integration

Start the JARVIS agent:

```bash
python3 server_main.py
```

Then test by asking:
- "What's the current temperature?"
- "How hot is it in here?"
- "What's the room temperature?"
- "Check the thermostat"

## Example Usage

Once set up, you can ask JARVIS questions like:

- "What's the current temperature in the living room?"
- "Is it too hot in here?"
- "What's the thermostat set to?"
- "Can you check the room temperature?"

The agent will automatically fetch the current temperature from your Google Nest and provide you with the information.

## Troubleshooting

### Common Issues

1. **403 Forbidden Error**: Check your access token and permissions
2. **Device Not Found**: Verify your device ID and project ID
3. **Invalid Credentials**: Ensure OAuth credentials are correct

### Refresh Token

Access tokens expire. You'll need to implement a refresh mechanism or manually update the token periodically.

### API Limits

Google Smart Device Management API has rate limits. Don't make too many requests in a short period.

## Security Notes

- Keep your access token secure and don't commit it to version control
- Use environment variables for sensitive data
- Consider implementing token refresh for production use
- Limit the scope of your OAuth credentials

## Advanced Features

You can extend the Google Nest tool to:

- Change thermostat settings
- Get humidity information
- Control multiple thermostats
- Set temperature schedules
- Get energy usage data

See the `tools/nest_tool.py` file for implementation details.
