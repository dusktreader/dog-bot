import re

import openai
import snick
from loguru import logger

from bot.config import settings
from bot.exceptions import BadCommandInterpretation, BadUserInterpretation
from bot.types import CommandGuess, UserGuess


openai.api_key = settings.OPENAI_API_KEY


command_ai_messages = [
    dict(
        role="system",
        content=snick.dedent(
            """
            You are a discord bot that runs a game among members that have joined in a
            single channel dedicated to the game.

            You have the following commands (the underscores are important and must be preserved):
              - START: Starts a new game
              - FINISH: Finishes a game
              - CONFIRM: The player agrees with the current question
              - DENY: The player disagrees with the current question
              - JOIN: The player is requesting to join the current game
              - ENLIST: The player is adding another player to the game
              - LEAVE: The player is requesting to leave the current game
              - USERS: The player is requesting a list of all players in the game
              - STATUS: The player wants to know what the status of the game is and what commands are available
              - CHAT: The player just wants to chat with the bot
              - CHOOSE_VICTIM: The player is choosing another player to challenge
              - CHOOSE_POISON: The player is choosing the type of challenge they want
              - CHOOSE_ORDEAL: The player is choosing the details of a challenge for another player
              - SKIP: The player is forfeiting their turn
              - CHECK_PLAYERS: The player wants to see if there are enough players to continue playing
              - CHECK_PROBER: The player wants to see if the challenging player is still in the game
              - CHECK_VICTIM: The player wants to see if the challenged player is still in the game
              - PICK_PROBER: The player is choosing the next player to be a challenger
              - DOUBLE: The user is passing their challenge on to another user

            Users may send messages that don't match the commands exactly. Your job is to
            figure out what command they actually want.

            You will reply to each message with one sentence. The sentence should be prefixed by the
            guessed command followed by two dashes and then an explanation of why the command was chosen.

            For example, if a user typed in "I think dusky should go next", you should respond like:
            "CHOOSE_VICTIM -- I chose CHOOSE_VICTIM because the player is saying that they want Dusky to
            be the next player to take a turn."

            The commands, CHOOSE_VICTIM, ENLIST, CHOOSE_VICTIM, CHOOSE_POISON, and CHOOSE_ORDEAL, involve
            another user that will be mentioned in the user's message. For these messages, you should
            include the username after the command and separated by a colon. For example, if the user
            says, "I pick johnny", then your response should look like:
            "CHOOSE_VICTIM:johnny -- I chose this because the user is challenging johnny next.

            It's also possible that the username mentioned is a formatted text string like,
            <@12341234123412>. In this case, the number should be used as the user guess.

            For any messages that do not match a command, the resulting command should be
            "MISS" followed by an explanation.

            The output of your response will be parsed by an algorithm that will split on
            the dashes, so it is very important that your responses are precise.
            """
        ),
    ),
]


def guess_command(text) -> CommandGuess:
    logger.debug(f"Command AI processing input: {text}")
    command_ai_messages.append(dict(role="user", content=text))
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=command_ai_messages,
        temperature=1,
        max_tokens=100,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    message = response.choices[0].message
    logger.debug(f"AI responded with {message=}")
    command_ai_messages.append(message)
    pattern = r"(?P<command>\w+)(?::(?P<target>\s*.+))?\s*--\s*(?P<explanation>.*)"
    regex_match: re.Match = BadCommandInterpretation.enforce_defined(
        re.search(pattern, message.content),
        "AI Parsed command had an invalid pattern",
    )
    command_match = regex_match.group("command")
    explanation_match = regex_match.group("explanation")
    target_match = regex_match.group("target")

    logger.debug(f"Parsed guess as: {command_match=}, {explanation_match=}, {target_match=}")
    guess = CommandGuess(
        command=command_match,
        explanation=explanation_match,
        target=target_match,
    )

    logger.debug(f"Command AI guesses: {guess}")

    return guess


chat_ai_messages = [
    dict(
        role="system",
        content=snick.dedent(
            """
            You are an anthropomorphic dog. You are playful but ornery. You like to joke with
            people and your sense of humor is somewhat blue. You like to joke around about
            people taking dares or sharing uncomfortable truths.

            You should not greet the user because you are already familiar friends.

            You should limit your response to one to three sentences.
            """
        ),
    ),
]


def get_chat(text, was_miss=False):
    logger.debug(f"AI processing input: {text}")
    messages = chat_ai_messages
    if was_miss:
        messages.append(
            dict(
                role="system",
                content=snick.dedent(
                    """
                    You should make fun of the user for trying to use an unknown command and
                    not knowing how to play truth or dare.
                    """
                ),
            ),
        )

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=messages,
        temperature=1.5,
        max_tokens=100,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    message = response.choices[0].message.content
    logger.debug(f"AI sasses: '{message}'")
    return message


user_ai_messages = [
    dict(
        role="system",
        content=snick.dedent(
            """
            You are a discord bot that attempts to match a provided name with a username
            from a list of users that are in the same channel. You will be provided a
            name to match and a list of usernames. The name may not match a username
            exactly, so you need to pick the one that is closest. If none of the
            usernames are similar to the provided name, you should not select one.

            The input will be given as the provided name followed by a colon and then
            a comma-separated list of potential matches.

            You will reply to each message with one sentence. The sentence should have a
            single word which is the username you selected from the list followed by two
            dashes and then an explanation of why the username was chosen.
            """
        ),
    ),
]


def guess_user(text, user_list: list[str]) -> UserGuess:
    logger.debug(f"User AI processing input: {text=}, {user_list=}")
    user_list_text = ", ".join(user_list)
    user_ai_messages.append(
        dict(
            role="user",
            content=f"{text}: {user_list_text}",
        )
    )
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=user_ai_messages,
        temperature=1,
        max_tokens=30,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    message = response.choices[0].message
    logger.debug(f"AI responded with {message=}")

    pattern = r"(?P<name>.+)\s*--\s*(?P<explanation>.*)"
    regex_match: re.Match = BadUserInterpretation.enforce_defined(
        re.search(pattern, message.content),
        "AI Parsed user had an invalid pattern",
    )
    name_match = regex_match.group("name")
    explanation_match = regex_match.group("explanation")

    logger.debug(f"Parsed guess as: {name_match=}, {explanation_match=}")
    guess = UserGuess(
        name=name_match.strip(),
        explanation=explanation_match,
    )

    logger.debug(f"User AI guesses: {guess}")

    return guess
