from buzz import Buzz
from discord import Member

from bot.constants import GameStatus, Command


class BadCommandInterpretation(Buzz):
    pass

class BadUserInterpretation(Buzz):
    pass


class UnknownTarget(Buzz):
    pass


class StateError(Buzz):
    pass


class NoSuchMappingError(StateError):
    pass


class NotEnoughPlayersError(StateError):
    def __init__(self, message: str, player_count: int, required_count: int):
        super().__init__(message)
        self.player_count = player_count
        self.required_count = required_count


class AlreadyJoinedError(StateError):
    def __init__(self, message: str, player: Member):
        super().__init__(message)
        self.player = player


class NotJoinedError(StateError):
    def __init__(self, message: str, player: Member):
        super().__init__(message)
        self.player = player


class AlreadyHaveProberError(StateError):
    def __init__(self, message: str, player: Member):
        super().__init__(message)
        self.player = player
