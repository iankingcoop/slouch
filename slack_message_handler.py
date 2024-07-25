import re

class SlackMessageHandler:

    def __init__(self, slack_web_client, slack_conv_id, slouch_settings, dlp_rules):
        self.client = slack_web_client
        self.conversation_id = slack_conv_id
        # content is overwritten when a listener matches a slack event
        self.content = None

        ##### ----- set security point of contact ----- #####
        self.security_poc = slouch_settings['security_poc'] # find user id... replace in slouch_settings file

        ##### ----- set expected working hours ----- #####
        self.working_hours = slouch_settings['working_hours'] # how to easily reference working hours in config file + code?

        ##### ----- set DLP regex ----- #####
        self.dlp_rules = dlp_rules['rules']


    # check to see if any DLP rules match
    def scan_message(rule, slack_message):
        if re.match(rule, slack_message):
            return True
        return False
    
    def check_dlp_pattern(self, slack_message):
        for rule_name, pattern in self.dlp_rules['rules']:
            if re.match(pattern, slack_message):
                return "DLP rule \"f{rule_name}\" matched"


        return False

    # alert the security POC if there's a match -- in thread. "https://api.slack.com/methods/chat.postMessage" apparently its hard to start a DM.
    def send_alert(self, body):
        self.client.chat_postMessage(
            channel=self.conversation_id,
            thread_ts=body["container"]["message_ts"],
            text="DLP rule matched :rotating_light: @{self_security_poc}", #how to @ a user using a user ID??
        )
        pass

    # react to the message if there's a dlp match. react with an emoji and reply in thread?
    def message_reaction(self, body):
        self.app.client.reactions_add(
            channel=self.conversation_id,
            timestamp=body["container"]["message_ts"],
            name="rotating_light: @{self_security_poc}", #how to @ a user using a user ID??
        )