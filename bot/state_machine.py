from random import choice
from typing import Protocol, Any

from discord import Member
from loguru import logger

from bot.constants import GameStatus, Command, Poison, PLAYERS_REQUIRED_TO_PLAY
from bot.types import Game, Action






from bot.exceptions import (
    StateError,
    NoSuchMappingError,
    NotEnoughPlayersError,
    AlreadyJoinedError,
    NotJoinedError,
    AlreadyHaveProberError,
)


def process_action(action: Action):
    if action.command == Command.STATUS:
        available_commands = ", ".join(transitions.get(action.game.status, {}).keys())
        action.game.message_queue.append(f"<@{action.player.id}> wants to know the status of the game")
        action.game.message_queue.append(f"The game status is: {action.game.status}, and the available actions are: {available_commands}")
        return

    transition_function = NoSuchMappingError.enforce_defined(
        transitions.get(action.game.status, {}).get(action.command),
        f"There is no transition from status {action.game.status} for command {action.command}",
    )
    logger.debug(f"Processing {transition_function=}")
    action.game.status = transition_function(action)


def join_game(action: Action) -> GameStatus:
    AlreadyJoinedError.require_condition(action.player not in action.game.players, f"Player {action.player} has already joined the game")
    action.game.players.append(action.player)
    action.game.message_queue.append(f"<@{action.player.id}> has joined the game")
    return action.game.status


def enlist_player(action: Action) -> GameStatus:
    AlreadyJoinedError.require_condition(action.target not in action.game.players, f"Player {action.player} has already joined the game")
    action.game.players.append(action.target)
    action.game.message_queue.append(f"<@{action.target.id}> has been enlisted into the game")
    return action.game.status


def leave_game(action: Action) -> GameStatus:
    NotJoinedError.require_condition(action.player in action.game.players, f"Player {action.player} has not joined the game")
    action.game.players.remove(action.player)
    action.game.message_queue.append(f"<@{action.player.id}> has left the game")
    return action.game.status


def list_players(action: Action) -> GameStatus:
    action.game.message_queue.append(f"<@{action.player.id}> asked who is playing.")
    player_list_text = " | ".join(f"<@{p.id}>" for p in action.game.players)
    action.game.message_queue.append(f"Current players are: {player_list_text}.")
    return action.game.status


def check_players(action: Action) -> GameStatus:
    action.game.message_queue.append(f"<@{action.player.id}> checked game status")
    if len(action.game.players) < PLAYERS_REQUIRED_TO_PLAY:
        action.game.message_queue.append(f"Not enough players ({len(action.game.players)}/{PLAYERS_REQUIRED_TO_PLAY}) to continue. Ending game.")
        action.game.victim = None
        action.game.prober = None
        action.game.poison = None
        return GameStatus.IDLE

    return Game.status


def check_prober(action: Action) -> GameStatus:
    action.game.message_queue.append(f"<@{action.player.id}> checked prober status")
    if action.game.prober not in action.game.players:
        action.game.message_queue.append(f"The current prober <@{action.game.prober.id}> bailed.")
        action.game.prober = None
        return GameStatus.AWAITING_PROBER
    return game.status


def check_victim(action: Action) -> GameStatus:
    action.game.message_queue.append(f"<@{action.player.id}> checked victim status")
    if action.game.prober not in action.game.players:
        action.game.message_queue.append(f"The current victim <@{action.game.victim.id}> bailed.")
        action.game.victim = None
        action.game.poison = None
        return GameStatus.AWAITING_VICTIM
    return action.game.status


def pick_prober(action: Action) -> GameStatus:
    AlreadyHaveProberError.require_condition(
        action.game.prober is None,
        f"There is already a prober selected",
    )
    action.game.prober = choice(action.game.players)
    action.game.message_queue.append(f"Choosing a new prober...and it's <@{action.game.prober.id}>!")
    return GameStatus.AWAITING_VICTIM


def try_to_start_game(action: Action) -> GameStatus:
    NotEnoughPlayersError.require_condition(
        len(action.game.players) >= PLAYERS_REQUIRED_TO_PLAY,
        f"Not enough players to play. Have {len(action.game.players)}; need {PLAYERS_REQUIRED_TO_PLAY}",
    )
    action.game.message_queue.append(f"<@{action.player.id}> started the game")
    return GameStatus.AWAITING_PROBER


def finish_game(action: Action) -> GameStatus:
    action.game.message_queue.append(f"<@{action.player.id}> stopped the game")
        action.game.victim = None
        action.game.prober = None
        action.game.poison = None
        return GameStatus.IDLE


def choose_victim(action: Action) -> GameStatus:
    NotJoinedError.require_condition(action.target in action.game.players, "Can't choose a victim {action.target} that isn't in the game")
    action.game.victim = action.target
    action.game.message_queue.append(f"<@{action.player.id}> challenged <@{action.target.id}>!")
    return GameStatus.AWAITING_POISON


def choose_poison(action: Action) -> GameStatus:
    action.game.poison = action.choice
    action.game.message_queue.append(f"<@{action.player.id}> chose {action.choice}!")
    return GameStatus.AWAITING_ORDEAL


def choose_ordeal(action: Action) -> GameStatus:
    action.game.ordeal = action.choice
    action.game.message_queue.append(f"<@{action.player.id}> challenged <@{action.target.id}> with '{action.choice}'!")
    return GameStatus.AWAITING_ACCEPT_ORDEAL


def accept_ordeal(action: Action) -> GameStatus:
    action.game.message_queue.append(f"<@{action.player.id}> accepted <@{action.game.prober.id}>'s challenge!")
    return GameStatus.AWAITING_PROOFS


def provide_proofs(action: Action) -> GameStatus:
    action.game.message_queue.append(f"<@{action.player.id}> provided proof!")
    return GameStatus.AWAITING_ACCEPT_PROOFS


def accept_proofs(action: Action) -> GameStatus:
    action.game.message_queue.append(f"<@{action.player.id}> accepted <@{action.game.victim.id}>'s proof!")
    action.game.prober = action.game.victim
    action.game.message_queue.append(f"Now it's <@{action.game.prober.id}>'s turn to pick a victim!")
    action.game.victim = None
    action.game.poison = None
    action.game.ordeal = None
    return GameStatus.AWAITING_VICTIM


class TransitionFunction(Protocol):
    def __call__(self, action: Action) -> GameStatus:
        ...


transitions: dict[GameStatus, dict[Command, TransitionFunction]] = {
    GameStatus.IDLE: {
        Command.START: try_to_start_game,
        Command.JOIN: join_game,
        Command.LEAVE: leave_game,
        Command.USERS: list_players,
        Command.ENLIST: enlist_player,
    },

    GameStatus.AWAITING_PROBER: {
        Command.JOIN: join_game,
        Command.LEAVE: leave_game,
        Command.CHECK_PLAYERS: check_players,
        Command.PICK_PROBER: pick_prober,
        Command.USERS: list_players,
    },

    GameStatus.AWAITING_VICTIM: {
        Command.JOIN: join_game,
        Command.LEAVE: leave_game,
        Command.CHECK_PLAYERS: check_players,
        Command.CHECK_PROBER: check_prober,
        Command.CHOOSE_VICTIM: choose_victim,
        Command.USERS: list_players,
    },

    GameStatus.AWAITING_POISON: {
        Command.JOIN: join_game,
        Command.LEAVE: leave_game,
        Command.CHECK_PROBER: check_prober,
        Command.CHECK_VICTIM: check_victim,
        Command.CHOOSE_POISON: choose_poison,
        Command.USERS: list_players,
    },

    GameStatus.AWAITING_ORDEAL: {
        Command.JOIN: join_game,
        Command.LEAVE: leave_game,
        Command.CHECK_PROBER: check_prober,
        Command.CHECK_VICTIM: check_victim,
        Command.CHOOSE_ORDEAL: choose_ordeal,
        Command.USERS: list_players,
    },

    GameStatus.AWAITING_ACCEPT_ORDEAL: {
        Command.JOIN: join_game,
        Command.LEAVE: leave_game,
        Command.CHECK_VICTIM: check_victim,
        Command.CONFIRM: accept_ordeal,
        Command.USERS: list_players,
    },

    GameStatus.AWAITING_PROOFS: {
        Command.JOIN: join_game,
        Command.LEAVE: leave_game,
        Command.CHECK_PROBER: check_prober,
        Command.CHECK_VICTIM: check_victim,
        Command.CONFIRM: provide_proofs,
        Command.USERS: list_players,
    },

    GameStatus.AWAITING_ACCEPT_PROOFS: {
        Command.JOIN: join_game,
        Command.LEAVE: leave_game,
        Command.CHECK_VICTIM: check_prober,
        Command.CONFIRM: accept_proofs,
        Command.USERS: list_players,
    },
}
