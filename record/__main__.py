from datetime import datetime
import os

from typing import Dict, Callable, Optional

import discord
from dotenv import load_dotenv
from discord import ApplicationContext, Guild, Member, TextChannel, VoiceChannel, VoiceClient, VoiceState, sinks

load_dotenv()

bot = discord.Bot()
record_command = bot.create_group(
    name='record',
    description='record command',
    guild_only=True
)

connections = {}


@bot.event
async def on_ready():
    print(bot.user)


async def once_done(sink: sinks.mp3.MP3Sink, file_name: str, channel: TextChannel):
    await sink.vc.disconnect()
    audio_data: Dict[int, sinks.core.AudioData] = sink.audio_data

    del connections[channel.guild.id]
    files = [
        discord.File(audio.file, f'{file_name}.{sink.encoding}') for _user_id, audio in audio_data.items()
    ]

    await channel.send(content='未錄製到數據' if len(files) == 0 else None, files=files)


def has_in_voice(func: Callable) -> Callable[[ApplicationContext], None]:
    async def wrap(interaction: ApplicationContext, *args) -> None:
        guild_id = interaction.guild.id

        if guild_id in connections:
            if interaction.author.voice.channel == connections[guild_id]['channel']:
                return await func(interaction, *args)
            return await interaction.respond('您不在錄製頻道中')
        await interaction.respond('尚未錄製')

    return wrap


@record_command.command(name='start', description='開始錄製')
async def start(interaction: ApplicationContext):
    author: Member = interaction.author
    guild: Guild = interaction.guild

    channel = author.voice and author.voice.channel

    if channel is None:
        await interaction.respond('你不在語音頻道中')
    else:
        (voice := await channel.connect()).start_recording(
            sinks.MP3Sink(),
            once_done,
            datetime.now().strftime('%Y-%m-%dT%H_%M_%S_%f%Z'),
            interaction.channel
        )

        connections.update({guild.id: {
            'voice': voice,
            'recording': True,
            'channel': channel
        }})

        await interaction.respond('開始錄音')


@record_command.command(name='pause', description='暫停/繼續 錄製')
@has_in_voice
async def pause(interaction: ApplicationContext):
    guild_id = interaction.guild.id

    if guild_id in connections:
        vc: VoiceClient = connections[guild_id]['voice']

        if connections[guild_id]['recording']:
            vc.toggle_pause()
            connections[guild_id]['recording'] = False
            await interaction.respond('已暫停錄音')
        else:
            vc.toggle_pause()
            connections[guild_id]['recording'] = True
            await interaction.respond('已回復錄音')
    else:
        await interaction.respond('目前並無錄音')


@record_command.command(name='stop', description='停止錄製')
@has_in_voice
async def stop(interaction: ApplicationContext):
    if interaction.guild.id in connections:
        vc: VoiceClient = connections[interaction.guild.id]['voice']
        vc.stop_recording()
        await interaction.respond('正在保存')
    else:
        await interaction.respond('目前並無錄音')


@bot.event
async def on_voice_state_update(_member: Member, before: VoiceState, after: VoiceState):
    channel = before.channel or after.channel
    guild = channel.guild

    _channel: Optional[VoiceChannel] = guild.id in connections and connections[guild.id]['channel']

    if len([_ for _ in channel.members if not _.bot]) == 0 and _channel and _channel.id == channel.id:
        voice: VoiceClient = connections[guild.id]['voice']
        voice.stop_recording()

bot.run(os.getenv('DISCORD_TOKEN'))
