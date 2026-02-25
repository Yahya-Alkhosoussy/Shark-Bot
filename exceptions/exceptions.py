class SharkBotException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class ItemNotFound(SharkBotException):
    def __init__(self, message: str, error_code: int):
        """
        Docstring for __init__

        :param message: Error Message
        :type message: str
        :param error_code: The Error code for the specific error (check exceptions.md)
        :type error_code: int
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code

    def __str__(self):
        return f"{self.message} (Error code: {self.error_code})"


class RoleNotAdded(SharkBotException):
    def __init__(self, message: str, error_code: int):
        super().__init__(message)
        self.message = message
        self.error_code = error_code

    def __str__(self):
        return f"{self.message} (Error code: {self.error_code})"


class BirthdateFormatError(SharkBotException):
    def __init__(self, message: str, error_code: int):
        super().__init__(message)
        self.message = message
        self.error_code = error_code

    def __str__(self):
        return f"{self.message} (Error code: {self.error_code})"


class FormatError(SharkBotException):
    def __init__(self, message: str, error_code: int):
        super().__init__(message)
        self.message = message
        self.error_code = error_code

    def __str__(self):
        return f"{self.message} (Error code: {self.error_code})"
