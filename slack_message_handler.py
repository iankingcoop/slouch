import re
import datetime
import pytz 
import json

class SlackMessageHandler:

    def __init__(self, slack_web_client, slack_conv_id, slouch_settings, dlp_rules):
        self.client = slack_web_client
        self.conversation_id = slack_conv_id
        # content is overwritten when a listener matches a slack event
        self.content = None

        ##### ----- set security point of contact ----- #####
        self.security_poc = slouch_settings['security_poc'] # find user id... replace in slouch_settings file

        ##### ----- set expected working hours ----- #####
        self.end_expected_hours_utc = slouch_settings['end_expected_hours_utc'] # how to easily reference working hours in config file + code?
        self.start_expected_hours_utc = slouch_settings['start_expected_hours_utc'] # how to easily reference working hours in config file + code?

        ##### ----- set DLP regex ----- #####
        self.dlp_rules = dlp_rules
    
    # TODO? consider allowing for a user ID OR username in the settings.
    # def validate_user_id(self, username):
    #     response = self.client.users_list()
    #     users = response['members']
    #     for user in users:
    #         if user['name'] == username:
    #             return user['id']
    #     return None
    

    # alert the security POC if there's a match -- in thread. "https://api.slack.com/methods/chat.postMessage" apparently its hard to start a DM.
    def send_dlp_alarm(self, msg, rule_name):
        self.client.chat_postMessage(
            channel=self.conversation_id,
            thread_ts=msg["ts"],
            text=f"DLP rule \"{rule_name}\" matched :rotating_light: <@{self.security_poc}>", #how to @ a user using a user ID?? U079RM8SLJJ
        )
        pass

    def send_time_day_alarm(self, msg):
        self.client.chat_postMessage(
            channel=self.conversation_id,
            thread_ts=msg["ts"],
            text=f"Unusual time of day :warning: <@{self.security_poc}>", #how to @ a user using a user ID?? U079RM8SLJJ
        )
        pass

    # react to the message if there's a dlp match. react with an emoji and reply in thread?
    def message_reaction_warning(self, msg):
        self.client.reactions_add(
            channel=self.conversation_id,
            timestamp=msg["ts"],
            name="warning"
        )

    def message_reaction_light(self, msg):
        self.client.reactions_add(
            channel=self.conversation_id,
            timestamp=msg["ts"],
            name="rotating_light"
        )
    
    def scan_for_dlp(self, slack_message):
        for rule_name, pattern in self.dlp_rules.items():
            print(777)
            print(rule_name, pattern)
            if re.match(pattern, slack_message['text']):
                # reaction
                self.message_reaction_light(slack_message)
                # send alert
                self.send_dlp_alarm(slack_message, rule_name)
                return True

        return False

    def is_timestamp_in_time_range(self, timestamp: str, start_time: str, end_time: str) -> bool:
        # Convert the timestamp to a timezone-aware datetime object in UTC
        utc_dt_object = datetime.datetime.fromtimestamp(float(timestamp), tz=datetime.timezone.utc)
        
        # Extract the time component (in UTC)
        timestamp_time = utc_dt_object.time()
        
        # Convert start_time and end_time to time objects
        start_time_obj = datetime.datetime.strptime(start_time, "%I %p").time()
        end_time_obj = datetime.datetime.strptime(end_time, "%I %p").time()
        
        # Check if the timestamp falls within the range
        if start_time_obj < end_time_obj:
            return start_time_obj <= timestamp_time <= end_time_obj
        else:
            return timestamp_time >= start_time_obj or timestamp_time <= end_time_obj
        
    def scan_time_of_day(self, slack_message):
        if self.is_timestamp_in_time_range(slack_message['ts'], self.end_expected_hours_utc, self.start_expected_hours_utc):
            self.message_reaction_warning(slack_message)
            self.send_time_day_alarm(slack_message)
