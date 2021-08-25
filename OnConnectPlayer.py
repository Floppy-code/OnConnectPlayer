import os
import discord
import asyncio
import time
import numpy as np
import threading
from pytube import YouTube

from SoundManager import SoundManager

TOKEN = 'ODc3OTg3NjUwMDcyNjMzMzg0.YR6ntw.Q0YQ_0Z0rfmJalfxZ5P6TwKkA8Q'
FFMPEG = './ffmpeg.exe'

intents = discord.Intents.all()     #TODO Fix later...
client = discord.Client(intents = intents)           #Client instance

@client.event
async def on_ready():
    voice_channel_list = []         #List of all voice channels
    voice_channel_dict = {}         #Dictionary of all voice channels available to the bot. Key: Channel ID, Values: List of users
    connected_members = []          #Newly found connected members.
    
    #Initialization
    initialize_voice_variables(voice_channel_list, voice_channel_dict)
    
    sound_manager = SoundManager.get_singleton()
    sound_manager.load_members_csv()

    #Setting on startup bot state.
    await set_bot_state()
    
    #Thread 1
    #Refreshing guilds, voice channels and users
    thread1 = threading.Thread(target = refresh_channels, args = (voice_channel_list,))
    
    #Thread 2
    #Monitoring if any new users connected
    thread2 = threading.Thread(target = check_users, args = (voice_channel_list, voice_channel_dict, connected_members))
    
    #Thread 3
    #Main program loop
    loop = asyncio.get_event_loop()
    thread3 = threading.Thread(target = bot_loop, args = (sound_manager, connected_members, loop))
    
    #All threads start
    thread1.start()
    thread2.start()
    thread3.start()

    print('[INFO] Initialization done!')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if ('!SetMusic' in message.content):
        #!SetMusic "YouTube link"
        line_split = message.content.split(' ')
        command = line_split[0]
        link = line_split[1]

        if ('youtube' not in link):
            await message.reply('Yeah, that won\'t work chief. I need a full youtube link.')
            return
        if (YouTube(link).length > 15):
            await message.reply('Ohhh hell naw... You think that people want to listen to a sound that\'s longer than 15 seconds?')
            return

        #Get SoundManager singleton
        sound_manager = SoundManager.get_singleton()
        #Add a new member and download his sound.
        sound_manager.add_member(message.author.id, link)

        await message.reply("Your custom sound will be awailable shortly.")
    elif ('!Help' in message.content):
        await message.reply('Hey, I\'m Bleep Bloop!\n You can set your custom sound by writing "!SetMusic YourYoutubeLinkHere."')


def bot_loop(sound_manager, connected_members, async_loop):
    while True:
        #Check if any new members connected to voice chat.
        if (len(connected_members) > 0):
            for member in connected_members:
                sound = sound_manager.get_member_sound(member.id)
                if (sound != None):
                    #Play sound in channel
                    future = asyncio.run_coroutine_threadsafe(play_sound_channel(member.voice.channel, sound), async_loop)
                    result = future.result()
            #Clear newly connected list
            connected_members.clear()
        time.sleep(1.0)


async def play_sound_channel(voice_channel, sound_path):
    #Connect to a voice channel
    vchannel = await voice_channel.connect()
    #Play audio using ffmpeg
    vchannel.play(discord.FFmpegPCMAudio(executable = FFMPEG, source = sound_path))
    while vchannel.is_playing():
        time.sleep(0.1)
    await vchannel.disconnect()

def initialize_voice_variables(voice_list, voice_dist):
    guilds = client.guilds
    for guild in guilds:
        for vchannel in guild.voice_channels:
            voice_list.append(vchannel)
            voice_dist[vchannel.id] = vchannel.members

def refresh_channels(voice_list):
    '''Refreshes all voice channels to find newly connected users.'''
    while True:
        guilds = client.guilds
        for guild in guilds:
            for vchannel in guild.voice_channels:
                voice_list.append(vchannel)
        time.sleep(0.5)

def check_users(voice_list, voice_dist, conn_list):
    '''Check for newly connected users in any available voice channels.'''
    while True:
        for vchannel in voice_list:
            new_members = vchannel.members
            old_members = voice_dist[vchannel.id]
            if len(new_members) != len(old_members):
                #Find newly connected and disconnected users.
                connected_users = [x for x in new_members if x not in old_members]
                #disconnected_users = [x for x in old_members if x not in new_members]  #Unused for now
                for user in connected_users:
                    if user is not client.user:
                        conn_list.append(user)
                #Update dictionary
                voice_dist[vchannel.id] = new_members

        time.sleep(0.5)

async def set_bot_state():
    '''Sets the bots state.'''
    activity = discord.Game("Rave Party!")
    await client.change_presence(activity = activity, status = discord.Status.online)

client.run(TOKEN)