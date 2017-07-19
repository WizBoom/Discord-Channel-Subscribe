import logging
import sqlite3
import time
import requests
import datetime
import asyncio
import json
import argparse
import sys
from prettytable import PrettyTable

import discord
from discord.ext import commands

# config setup
with open('config.json') as f:
    config = json.load(f)

with open('channels.json') as c:
    channels = json.load(c)

#logging setup
logger = logging.getLogger('discord')
logger.setLevel(config['LOGGING']['LEVEL']['ALL'])
formatter = logging.Formatter(style='{', fmt='{asctime} [{levelname}] {message}', datefmt='%Y-%m-%d %H:%M:%S')
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
handler.setLevel(config['LOGGING']['LEVEL']['CONSOLE'])
logger.addHandler(handler)
handler = logging.FileHandler(config['LOGGING']['FILE'])
handler.setFormatter(formatter)
handler.setLevel(config['LOGGING']['LEVEL']['FILE'])
logger.addHandler(handler)

# bot setup
logger.info('Creating bot object ...')
bot = commands.Bot(command_prefix=config['COMMAND_PREFIX'], description=config['DESCRIPTION'])
logger.info('Setup complete')

unfoundRoles = []

@bot.event
async def on_ready():
    logger.info('Logged in')
    await bot.change_presence(game=discord.Game(name='Crusading'))

@bot.event
async def on_message(message):
    """
    Logs attempes to use the bot.
    Args:
        message (discord.Message) - message sent in the channel
    Returns:
        None
    """
    try:
        if message.author == bot.user:
            return
        if message.content.startswith(config['COMMAND_PREFIX']):
            logger.info('Command "{}" from "{}" in "{}"'.format(message.content, message.author.name, message.channel.name))
        if 'bot' in message.content.lower():
            logger.info('Bot in message: "{}" by "{}" in "{}"'.format(message.content, message.author.name, message.channel.name))
        await bot.process_commands(message)
    except Exception as e:
        logger.error('Exception in on_message(): ' + str(e))

@bot.command(
    name='subscribe',
    brief='Subscribes to certain channels',
    help='Subscribe to groups on the server. Use !subscribe to see what\' available and use !subscribe [GROUPNAME] to subscribe! See unsubscribing for unsubscribing',
    pass_context=True
)
async def command_subscribe(context):
    """Command - subscribe"""
    try:
        blChannels=[]
        for bl in channels["BlacklistedChannels"]:
            blChannels.append(bl["ID"])
        if not context.message.channel.id in blChannels:
            message = await subscribe(context)
            await bot.say(message)
        else:
            await bot.say("This command cannot be used from this channel")
    except Exception as e:
        logger.error('Exception in !subscribe: ' + str(e))


async def subscribe(context):
    message = context.message
    x = message.content.split()
    if len(x) <= 1:
        #RETURN CURRENT GROUPS
        groupList = PrettyTable()
        groupList.field_names = ["Name", "Description", "Type"]
        nothingFound = True
        for channel in channels["Roles"]:
            role = discord.utils.get(message.server.roles, name=channel['Role'])
            if not role is None and not role in message.author.roles:
                nothingFound = False
                groupList.add_row([channel["Name"], channel["Description"], channel["Type"]])
        if not nothingFound:
            return "```" + groupList.get_string(sortby="Name") + "```"
        else:
            return "```No other groups to subscribe to```"
    args = message.content.split(' ', 1)[1]
    args = args.strip()
    args = args.lower()

    for channel in channels["Roles"]:
        clean = channel['Name'].strip()
        clean = clean.lower()
        if args == clean:
            role = discord.utils.get(message.server.roles, name=channel['Role'])
            if role in message.author.roles:
                return message.author.mention + ", you're already subscribed to " + channel['Name']
            if not role is None: 
                member = message.author
                await bot.add_roles(member,role) 
                return message.author.mention + ", you're now subscribed to " + channel['Name']

    return message.author.mention + ", I can't find " + args

@bot.command(
    name='unsubscribe',
    brief='Unsubscribes from channels',
    help='Unubscribe from groups on the server. Use !unsubscribe to see what you\'re subscribed to and use !unsubscribe [GROUPNAME] to unsubscribe! See subscribing for subscribing',
    pass_context=True
)
async def command_unsubscribe(context):
    """Command - unsubscribe"""
    try:
        message = await unsubscribe(context)
        await bot.say(message)
    except Exception as e:
        logger.error('Exception in !unsubscribe: ' + str(e))


async def unsubscribe(context):
    message = context.message
    x = message.content.split()
    if len(x) <= 1:
        #RETURN CURRENT GROUPS
        groupList = PrettyTable()
        groupList.field_names = ["Name", "Description", "Type"]
        nothingFound = True
        for channel in channels["Roles"]:
            role = discord.utils.get(message.server.roles, name=channel['Role'])
            if not role is None and role in message.author.roles:
                nothingFound = False
                groupList.add_row([channel["Name"], channel["Description"], channel["Type"]])
        if not nothingFound:
            return "```" + groupList.get_string(sortby="Name") + "```"
        else:
            return "```No other groups to unsubscribe from```"

    args = message.content.split(' ', 1)[1]
    args = args.strip()
    args = args.lower()

    for channel in channels["Roles"]:
        clean = channel['Name'].strip()
        clean = clean.lower()
        if args == clean:
            role = discord.utils.get(message.server.roles, name=channel['Role'])
            if role is None:
                return message.author.mention + ", I can't find " + args
            if not role in message.author.roles:
                return message.author.mention + ", you're not subscribed to " + channel['Name']
            member = message.author
            await bot.remove_roles(member,role) 
            return message.author.mention + ", you're now unsubscribed from " + channel['Name']
    return message.author.mention + ", I can't find " + args

if __name__ == '__main__':
    try:
        logger.info('Scheduling background tasks ...')
        logger.info('Starting run loop ...')
        bot.run(config['TOKEN'])
    except KeyboardInterrupt:
        logger.warning('Logging out ...')
        bot.loop.run_until_complete(bot.logout())
        logger.warning('Logged out')
    except Exception as e:
        logger.error('Caught unknown error: ' + str(e))
    finally:
        logger.warning('Closing ...')
        bot.loop.close()
        logger.info('Done')
