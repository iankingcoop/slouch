import os
import logging

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
# from config file import configurations?
from slack_message_handler import SlackMessageHandler
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


    #TODO should these values be init'd in the SlouchMessageHandler instead??
    #TODO i think ill just pass them to SlouchMessageHandler... but should i just abstract these all into "slouch_settings"?
    ##### ----- access configuration file ----- #####
    with open('slouch_settings.json') as config_file:
        slouch_settings = json.load(config_file)

    ##### ----- access dlp rules file ----- #####
    with open('dlp_rules.json') as dlp_file:
        dlp_rules = json.load(dlp_file)


    ##### ----- set relevant Slack channel ----- #####
    channel_name = slouch_settings['channel_name'] # how do I make this multiple slack channels??
    # target_channels = []

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

    return app, slack_web_client, slack_conv_id, slouch_settings, dlp_rules


def main():

    app, slack_web_client, slack_conv_id, slouch_settings, dlp_rules = init_app()

    msg_handler = SlackMessageHandler(slack_web_client, slack_conv_id, slouch_settings, dlp_rules)

    ##### ----- slack bot event triggers ----- #####
    # message: the main event trigger, an ask-dnr inbound AKA "message"
    @app.event("message")  # https://api.slack.com/events/message.channels
    def respond_channel_message(client, body, message, event, say):
        if message.get("type") != "message":
            logging.warning(
                "Message is not of type ~message~. Maybe it's a block_actions event. Stopping."
            )
            return

        if message.get("text") is None:
            logging.warning(
                "Message doesn't have any text. Not sure why... is it really a message? Stopping."
            )
            return

        # TODO will it be able to monitor im messages? or no... just specific channels...
        # if message.get("channel_type") == "im":
        #     logging.warning("Not paying attention to IM messages right now.")
        #     return

        logging.warning("Looks like a message we can work with: {}".format(message))

        # record the slack message text
        msg_handler.content = message["text"]

        msg_handler.scan_message(message["ts"])
        msg_handler.post_faq_content(message["ts"])
        msg_handler.initial_reply(message["ts"])