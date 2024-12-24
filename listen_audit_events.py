# listen for audit events
import requests
import time

# Your OAuth token (bot token) with auditlogs:read scope
token = 'xoxp-your-token'

# Slack API endpoint for audit logs
url = 'https://api.slack.com/audit/v1/logs'

# Function to fetch audit logs with pagination
def get_audit_logs(cursor=None):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    # Include cursor if provided
    params = {}
    if cursor:
        params['cursor'] = cursor

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        audit_logs = response.json()
        return audit_logs.get('entries', []), audit_logs['response_metadata'].get('next_cursor', None)
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return [], None

# Continuously poll for audit events, avoid duplicates by using cursor
def listen_for_audit_logs():
    next_cursor = None
    while True:
        logs, next_cursor = get_audit_logs(cursor=next_cursor)
        if logs:
            for event in logs:
                process_event(event)
        
        # Sleep for a while before polling again (poll every 60 seconds)
        time.sleep(60)

# Function to process each event
def process_event(event):
    # Example: Print the event type and other details
    print(f"Event: {event['action']}, Actor: {event['actor']['name']}")

# Start listening for audit logs
listen_for_audit_logs()
