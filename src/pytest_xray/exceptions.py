class XrayError(Exception):
    """Custom exception for Jira XRAY"""

    def __init__(self, message=''):
        self.message = message
