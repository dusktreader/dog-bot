from auto_name_enum import AutoNameEnum, auto

PLAYERS_REQUIRED_TO_PLAY = 1
BOT_NAME = "dog-bot"


class LogLevelEnum(AutoNameEnum):
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


class GameStatus(AutoNameEnum):
    IDLE = auto()
    AWAITING_PROBER = auto()
    AWAITING_VICTIM = auto()
    AWAITING_POISON = auto()
    AWAITING_ORDEAL = auto()
    AWAITING_ACCEPT_ORDEAL = auto()
    AWAITING_PROOFS = auto()
    AWAITING_ACCEPT_PROOFS = auto()


class Poison(AutoNameEnum):
    TRUTH = auto()
    DARE = auto()
    WYR = auto()

class Command(AutoNameEnum):
    START = auto()
    FINISH = auto()
    CONFIRM = auto()
    DENY = auto()
    JOIN = auto()
    LEAVE = auto()
    USERS = auto()
    STATUS = auto()
    CHAT = auto()
    CHOOSE_VICTIM = auto()
    CHOOSE_POISON = auto()
    CHOOSE_ORDEAL = auto()
    SKIP = auto()
    CHECK_PLAYERS = auto()
    CHECK_PROBER = auto()
    CHECK_VICTIM = auto()
    PICK_PROBER = auto()
    #DOUBLE = auto()
    MISS = auto()

    @classmethod
    def _missing_(cls, _):
        return cls.MISS
