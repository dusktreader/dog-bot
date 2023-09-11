import os
import sys

import discord
import openai
from dotenv import load_dotenv
from loguru import logger

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
openai.api_key = os.getenv("OPENAI_API_KEY")

logger.remove()
logger.add(sys.stderr, level="DEBUG")


ai_messages = [
    {
      "role": "system",
      "content": "You are a discord bot that runs a game among members that have joined in a  single channel dedicated to the game.\n\nYou have the following commands: \n- join: Adds the requesting user to the current game\n- leave: Removes the requesting user from the current game.\n- who: Prints out a list of the current users in the game.\n\nUsers may send messages that don't match the commands exactly. Your job is to figure out what command they actually want.\n\nYou will reply to each message with one sentence. The sentence should have a single word which is the command followed by a colon and then an explanation of why the command was chosen.\n\nFor example, if a user typed in \"I want to play\", you should respond like: \"join: I chose join because the user is saying that they want to join in the game.\"\n\nThe output of your response will be parsed by an algorithm that will split on the colon, so it is very important that your responses are precise."
    },
]

def get_command(text):
    ai_messages.append(
        dict(
            role="user",
            content=text,
        )
    )
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=ai_messages,
        temperature=1,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    message = response.choices[0].message
    ai_messages.append(message)
    (command, explanation) = message.content.split(":")
    logger.debug(f"Assistant guesses {command}: {explanation}")
    return command


class MyClient(discord.Client):
    async def on_ready(self):
        logger.debug(f'Logged on as {self.user}!')

    async def on_message(self, message):
        logger.debug(f'Message from {message.author} in {message.channel}: {message.content}')
        if message.author != self.user:
            command = get_command(message.content)
            await message.channel.send(f"<@{message.author.id}> issued command {command}")


intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(TOKEN)
