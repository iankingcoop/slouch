import os

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
# from config file import configurations?
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import json






# --- new initiate app ---

def init_app():
    ##### ----- Init Slack app  ----- #####
    app = App(
        token=os.environ.get("SLACK_BOT_TOKEN"),
        signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    )

    # init slack web client
    slack_web_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])

    ##### ----- access configuration file ----- #####
    with open('config.json') as config_file:
        config = json.load(config_file)

    ##### ----- set security point of contact ----- #####
    security_poc = config['security_poc'] # find user id... replace in config file

    ##### ----- set expected working hours ----- #####
    working_hours = config['working_hours'] # how to easily reference working hours in config file + code?

    ##### ----- access dlp rules file ----- #####
    with open('dlp_rules.json') as config_file:
        dlp_rules = json.load(config_file)

    ##### ----- set DLP regex ----- #####
    dlp_rules = dlp_rules['rules'] # how to easily reference working hours in config file + code?

    ##### ----- set relevant Slack channel ----- #####
    channel_name = config['channel_name'] # how do I make this multipple??
    # target_channels = []
    api_key = config['api_key']

    ##### ----- retrieve "conversation ID" (ID for the workspace/channel where the app is listening...) ----- #####
    # slack_conv_id isn't hard coded... it could be, but these  next few lines help retrive the convo ID whether we're
    # in the test workspace or the prod workspace..
    slack_conv_id = None
    try:
        for result in slack_web_client.conversations_list():
            if slack_conv_id is not None:
                break
            for channel in result["channels"]:
                # for target_channel in target_channels?
                if channel["name"] == channel_name:
                    slack_conv_id = channel["id"]
                    break

    except SlackApiError as e:
        print(f"Error: {e}")

    return app, slack_web_client, slack_conv_id
