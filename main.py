import discord
from discord.ext import commands
import youtube_dl
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
urlsToDownload = []
queue = []
queueNames = []
connection = None


@bot.event
async def on_ready():
    print("bot ready!!!!")


@bot.command()
async def play(ctx, url):
    global connection
    voice_channel = ctx.author.voice.channel
    if (connection == None):
        connection = await voice_channel.connect()

    if len(queue) == 0:
        await downloadMusicAndAddToQueue(ctx, url)
        await playNext(ctx)
    else:
        urlsToDownload.append(url)


@bot.command()
async def salir(ctx):
    await desconectar(ctx)


async def downloadMusicAndAddToQueue(ctx, url):
    ydl_opts = {
        'format': 'worstaudio/worst',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '48',
        }],
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        url2 = info['formats'][0]['url']
        queue.append(url2)
        queueNames.append(info['title'])


@bot.command()
async def skip(ctx):
    connection.stop()


async def playNext(ctx):
    """loop that is in charge of playing all the songs on the queue until there is none left"""
    global connection
    # While there are songs to play
    while (len(queue) > 0):
        FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                          'options': '-vn -filter:a "volume=0.25"'}

        audio_source = discord.FFmpegPCMAudio(queue[0], **FFMPEG_OPTIONS)
        connection.play(audio_source)

        while (connection.is_playing()):
            await asyncio.sleep(1)

        # if there is still music to download
        if (len(urlsToDownload) > 0):
            currentMusicToDownload = urlsToDownload.pop(0)
            await downloadMusicAndAddToQueue(ctx, currentMusicToDownload)

        # Remove from the queue the music that just played
        queue.pop(0)
        queueNames.pop(0)
    await ctx.send("No quedan canciones en la lista")
    await desconectar(ctx)
    return


@bot.command()
async def q(ctx):
    # Does not work properly, threading is shit and ydl takes too much time
    msg = ""
    for cancion in queueNames:
        msg += cancion+"\n"
    await ctx.send(msg)


@bot.command()
async def current(ctx):
    msg = f"Currently playing {queueNames[0]}"
    await ctx.send(msg)


async def desconectar(ctx):
    global connection
    global queue
    global queueNames

    queue = []
    queueNames = []

    voice_client = ctx.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
        connection = None

bot.run(os.getenv("MY_KEY"))
