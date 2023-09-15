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
    pass


class AlreadyJoinedError(StateError):
    pass


class NotJoinedError(StateError):
    pass


class AlreadyHaveProberError(StateError):
    pass
