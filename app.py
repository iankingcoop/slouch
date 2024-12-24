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


    ##### ----- set relevant Slack workspace ----- #####
    workspace_name = slouch_settings['workspace'] # how do I make this multiple slack channels??

    ##### ----- set relevant Slack channel ----- #####
    channel_name = slouch_settings['channel_name'] # how do I make this multiple slack channels??
    # target_channels = []

    # print("trying to print team info")
    # team_info = slack_web_client.team_info()
    # print(type(team_info), team_info)
    # print(team_info['team']['id'])
    # # parsed_team_id = team_info['team']['id']
    # parsed_team_id = "T07P6JGD048"

    # print("auth test flow")
    # print(slack_web_client.auth_test())

    # print("ricky bobby")
    # print(slack_web_client.auth_teams_list()['teams'][0]['id'])

    teams = slack_web_client.auth_teams_list()['teams']
    
    # List comprehension to find the 'id' where 'name' is 'iantesttwo'
    matches = [item['id'] for item in teams if item.get('name') == workspace_name]

    parsed_team_id = None
    # If a match is found, return the first result
    if matches:
        parsed_team_id = matches[0]
        logging.warning(f"current team: {parsed_team_id}")  # 'T07P6JGD048'
    else:
        logging.warning("No matching workspace name found.")
    
    ##### ----- retrieve "conversation ID" (ID for the workspace/channel where the app is listening...) ----- #####
    # slack_conv_id isn't hard coded... it could be, but these  next few lines help retrive the convo ID whether we're
    # in the test workspace or the prod workspace..
    slack_conv_id = None
    try:
        for result in slack_web_client.conversations_list(team_id=parsed_team_id):
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

def create_dlp_homepage(data):
    # Extract rules from the 'rules' object
    # rules = data.get("rules", {})
    rules = data

    home_view = {
  "type": "home",
  "callback_id": "home_view"
}
    block_sections = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Slouch security homepage*"
            }
        },
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "Slouch's capabilties are listed below. Contributions or feedback is welcome!\n<https://github.com/iankingcoop/slouch|Slouch Github>"
			},
			"accessory": {
				"type": "image",
				"image_url": "https://pbs.twimg.com/profile_images/1611583672632614913/OfmGknzg_400x400.jpg",
				"alt_text": "cute cat"
			}
		},
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":large_blue_diamond: Slouch can optionally be hooked up to poll for Slack Anomaly events, see the readme for more details. <https://github.com/iankingcoop/slouch|Slouch Github>\nRead more about <https://google.com|Slack anomaly events here.>"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":large_blue_diamond: Slouch checks for unusual user activity, such as activity outside of normal working hours, and sends an alert to the designated security contact :warning:"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":large_blue_diamond: DLP rules will send an alert to the designated security contact when triggered :rotating_light: <https://google.com|DLP rule list in github>. Active DLP rules are listed below. "
            }
        }
    ]

    # Dynamically add each rule as a section block, excluding the 'pre_signed_url'
    for i, (key, rule) in enumerate(rules.items(), 1):
        block_sections.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{key}* `{rule}`"
            }
        })

    home_view['blocks'] = block_sections
    return home_view


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

        msg_handler.scan_for_dlp(message)
        msg_handler.scan_time_of_day(message)

    @app.event("app_home_opened")
    def update_home_tab(client, event, logger):
        try:
            homepage = create_dlp_homepage(dlp_rules)
            print("homer")
            print(type(homepage))
            print(homepage)
            # views.publish is the method that your app uses to push a view to the Home tab
            client.views_publish(
                #     # the user that opened your app's app home
                user_id=event["user"],
                #     # the view object that appears in the app home
                view=homepage,
            )

        except Exception as e:
            logger.error(f"Error publishing home tab: {e}")

    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()


if __name__ == "__main__":
    main()