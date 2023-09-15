import re
import sys
from dataclasses import dataclass

import discord
import snick
from loguru import logger
from discord.utils import find as discord_find

from bot.config import settings
from bot.ai import guess_command, guess_user, get_chat
from bot.constants import Command, BOT_NAME
from bot.exceptions import StateError
from bot.state_machine import process_action
from bot.types import CommandGuess, Game, Action, UserGuess


logger.remove()
logger.add(sys.stderr, level="DEBUG")


class MyClient(discord.Client):
    current_game: Game = Game()

    async def on_ready(self):
        logger.debug(f'Logged on as {self.user}!')

    async def on_message(self, message):
        logger.debug(f'Message from {message.author} in {message.channel}: {message.content}')
        if self.user not in message.mentions:
            logger.debug("Skipping message since dog-bot wasn't mentioned")
            return

        message.content = message.content.replace(f"<@{self.user.id}>", "DOGBOT")
        logger.debug(f"Santized content: {message.content}")
        if message.author != self.user:
            # try to parse exact command to save AI work
            guess: CommandGuess = guess_command(message.content)
            guess.command = guess.command.replace(" ", "_")
            if guess.command is Command.CHAT:
                chat_message = get_chat(message.content)
                await message.channel.send(f"<@{message.author.id}>, {chat_message}")
            elif guess.command is Command.MISS:
                chat_message = get_chat(message.content, was_miss=True)
                await message.channel.send(f"<@{message.author.id}>, {chat_message}")
            else:

                try:
                    command = Command(guess.command)
                except Exception as err:
                    logger.debug("Invalid command guessed by AI: {guess.command}")
                    await message.channel.send(
                        snick.unwrap(
                            f"""
                            I'm an idiot, <@{message.author.id}, I got confused and made up my own command:
                            {guess.command}.
                            Please try again, and I'll try to be smarter!
                            """)
                    )
                    return

                if command is Command.MISS:
                    await message.channel.send(f"I got confused, I'm sorry. I thought the command was {guess.command}")
                    return

                await message.channel.send(snick.unwrap(f"_I chose this command based on {message.author.name}'s message: {guess.command}_"))
                await message.channel.send(snick.unwrap(f"_About why I chose this command: {guess.explanation}_"))

                target = None
                if guess.target is not None:
                    logger.debug("Trying to deduce the player from {guess.target}")
                    regex_match = re.search(r"<@(\d+)>", guess.target)
                    if regex_match is not None:
                        logger.debug("Target is a player id")
                        target_id = int(regex_match.group(0))
                        logger.debug(f"Using {target_id=}")
                        target = discord_find(lambda m: m.id == target_id, message.mentions),
                    else:
                        logger.debug("Target must be a name. Looking them up")
                        possible_player_names = {m.display_name: m for m in message.channel.members if m.display_name != BOT_NAME}
                        logger.debug(f"Possible target names are {', '.join(possible_player_names.keys())}")
                        target = possible_player_names.get(guess.target)
                        if target is None:
                            logger.debug(f"No exact match. Asking AI to guess the name")
                            user_guess: UserGuess = guess_user(guess.target, list(possible_player_names.keys()))
                            await message.channel.send(snick.unwrap(f"The user target name is {user_guess.name}"))
                            await message.channel.send(snick.unwrap(f"_About why I chose this user: {user_guess.explanation}_"))
                            logger.debug(f"Looking up {user_guess.name} in {', '.join(possible_player_names.keys())}")
                            target = possible_player_names.get(user_guess.name)
                            if target is None:
                                await message.channel.send(f"Well, shit...I can't guess who that is referring to. Sorry!")
                                return

                action = Action(
                    command=command,
                    player=message.author,
                    target=target,
                    game=self.current_game,
                    choice="FIX ME",
                )

                try:
                    process_action(action)
                    for bot_message in action.game.iter_messages():
                        await message.channel.send(bot_message)
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
