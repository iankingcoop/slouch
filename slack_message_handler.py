



class SlouchMessageHandler:

    def __init__(self, slack_web_client, slack_conv_id):
        self.client = slack_web_client
        self.conversation_id = slack_conv_id
        # content is overwritten when a listener matches a slack event
        self.content = None
        self.security_poc?

    # check to see if any DLP rules match
    def scan_message():
        pass

    # alert the security POC if there's a match
    def send_alert():
        pass

    # react to the message if there's a dlp match. react with an emoji and reply in thread?
    def message_reaction():
        pass