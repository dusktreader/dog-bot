from dataclasses import dataclass, field

from discord import Member

from bot.constants import GameStatus, Command, Poison


@dataclass
class Game:
    players: list[Member] = field(default_factory=lambda: [])
    prober: Member | None = None
    victim: Member | None = None
    poison: Poison | None = None
    ordeal: str | None = None
    status: GameStatus = GameStatus.IDLE

    def reset(self):
        self.prober = None
        self.victim = None
        self.poison = None
        self.ordeal = None
        self.status = GameStatus.Idle


@dataclass
class CommandGuess:
    command: str
    explanation: str
    target: str | None = None


@dataclass
class UserGuess:
    name: str
    explanation: str


@dataclass
class ActionGuess:
    player_id: int
    target_id: int | None = None
    command: Command | None = None
    choice: Poison | str | None = None


@dataclass
class Action:
    command: Command
    player: Member
    game: Game
    target: Member | None
    choice: Poison | str

    def __str__(self):
        target_info = ""
        if self.target is not None:
            target_info = f": target={self.target}"
        return f"player={self.player} issued command={self.command}{target_info}"
