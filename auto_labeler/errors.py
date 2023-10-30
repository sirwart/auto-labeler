'''A very basic class to print known errors to the CLI output and exit'''
class ValidationError(Exception):
    def __init__(self, message):
        super().__init__(message)