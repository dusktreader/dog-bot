import re
import sys
from contextlib import contextmanager
from dataclasses import dataclass

import discord
import snick
from loguru import logger
from discord.utils import find as discord_find

from bot.config import settings
from bot.ai import guess_command, guess_user, get_chat, guess_action
from bot.constants import Command, BOT_NAME
from bot.exceptions import StateError
from bot.state_machine import process_action
from bot.types import CommandGuess, Game, Action, UserGuess, ActionGuess


logger.remove()
logger.add(sys.stderr, level="TRACE")


@contextmanager
def log_chat(channel):
    async def _send(message):
        print("SENDING: ", message)
        await channel.send(message.record["message"])

    handler_id = logger.add(_send, level="INFO")
    print("ADDED HANDLER", handler_id)
    try:
        yield
    finally:
        logger.remove(handler_id)
        print("REMOVED HANDLER", handler_id)



class MyClient(discord.Client):
    current_game: Game = Game()

    def parse_command(self, action_guess: ActionGuess, command_text: str):
        logger.debug(f"Attempting to parse command directly from: {command_text}")
        regex_match = re.match(
            r"^{bot_name}\s+(?P<command>\w+)(?:\s+<@(?P<target_id>\d+)>)?$".format(
                bot_name=BOT_NAME,
            ),
            command_text,
        )
        if regex_match is None:
            logger.debug("Couldn't parse command from input")
            return
        command_text = regex_match.group("command").upper()
        try:
            action_guess.command = Command(command_text)
        except Exception as err:
            logger.debug(f"Regex parsed command invalid: {err}. Falling back to command guessing")
            action_guess.command = None
            return
        target_id_text = regex_match.group("target_id")
        if target_id_text is None:
            action_guess.target_id = None
            return
        try:
            action_guess.target_id = int(target_id_text)
        except Exception as err:
            logger.debug(f"Regex parsed target_id invalid: {err}. Falling back to command guessing")
            action_guess.command = None

    async def on_ready(self):
        logger.debug(f'Logged on as {self.user}!')

    async def on_message(self, message):
        with log_chat(message.channel):
            logger.debug(f'Message from {message.author} in {message.channel}: {message.content}')
            if self.user not in message.mentions:
                logger.debug("Skipping message since dog-bot wasn't mentioned")
                return

            logger.info("At your service!")

            message.content = message.content.replace(f"<@{self.user.id}>", BOT_NAME)
            logger.debug(f"Sanitized content: {message.content}")
            if message.author != self.user:
                # try to parse exact command to save AI work
                action_guess = ActionGuess(player_id=message.author.id)
                self.parse_command(action_guess, message.content)
                if action_guess.command is None or action_guess.command is Command.MISS:
                    logger.debug("Couldn't parse command directly. Falling back to guessing")
                    player_id_map = {m.display_name: m.id for m in message.channel.members if m.display_name != BOT_NAME}
                    guess_action(action_guess, message.content, player_id_map)

                logger.debug(f"Looking up {action_guess.target_id=}  in {message.channel.members}")
                action = Action(
                    command=action_guess.command,
                    player=message.author,
                    target=discord_find(lambda m: m.id == action_guess.target_id, message.channel.members),
                    game=self.current_game,
                    choice="FIX ME",
                )
                logger.debug(f"Constructed this action from the guess: {action}")


                try:
                    process_action(action)
                except StateError as err:
                    await message.channel.send(err.message)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = MyClient(intents=intents)


def run():
    client.run(settings.DISCORD_TOKEN)

"""
<@{message.author.id}>, I can't start a new game because
there is already one going!

<@{message.author.id}> started a new game! Come join in for some spicy fun!

<@{message.author.id}> ended the game! Start a new one to get it going again!

<@{message.author.id}>, I can't finish a game because
there isn't any going yet!

<@{message.author.id}>, you can't join the game because nobody has started one yet!

<@{message.author.id}>, you can't join the game, dude...you are already playing...

<@{message.author.id}> has joined the game! Give 'em hell!!

<@{message.author.id}>, you can't leave the game because THERE IS NO GAME! Figure it out!

<@{message.author.id}>, you can't leave the game, because you never joined it. Come on, dude!

<@{message.author.id}> has left the game! Guess they couldn't handle it...

<@{message.author.id}>, there are no games in progress. So...None. There are No users in the nonexistent game. 🤦🤦🤦

<@{message.author.id}> here are the current players: {player_list}

<@{message.author.id}>, there are no games in progress. So, how about No? No challenge for you. 😠

<@{message.author.id}>, you need to wait your turn, there, hotshot. ✈️

<@{message.author.id}> has challenged you, <@{action.target}>! Truth or Dare?!
"""
