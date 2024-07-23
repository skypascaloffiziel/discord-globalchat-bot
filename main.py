import discord
from discord.ext import commands, tasks
import json
import os
import aiohttp
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Intents konfigurieren
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# Erstelle den Bot
bot = commands.Bot(command_prefix='!', intents=intents)

# Bot Status
activity = discord.Streaming(name="Globalchateinrichten mit !setup", url="http://www.twitch.tv/sapcepascal")
bot.activity = activity

# Initialisiere die JSON-Datei für Globalchat
if not os.path.exists('globalchat.json'):
    with open('globalchat.json', 'w') as f:
        json.dump({"global_channels": [], "banned_users": [], "banned_servers": []}, f)

def load_data():
    with open('globalchat.json', 'r') as f:
        return json.load(f)

def save_data(data):
    with open('globalchat.json', 'w') as f:
        json.dump(data, f, indent=4)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    fetch_status.start()  # Start the status update loop

# Globalchat Setup Command
@bot.command(name='setup', help='Fügt diesen Kanal zum Globalchat hinzu')
@commands.has_permissions(administrator=True)
async def setup(ctx):
    data = load_data()
    if ctx.channel.id not in data['global_channels']:
        data['global_channels'].append(ctx.channel.id)
        save_data(data)
        await ctx.send(f'Dieser Kanal wurde zum Globalchat hinzugefügt.')
    else:
        await ctx.send('Dieser Kanal ist bereits im Globalchat.')

# Globalchat Remove Command
@bot.command(name='remove', help='Entfernt diesen Kanal vom Globalchat')
@commands.has_permissions(administrator=True)
async def remove(ctx):
    data = load_data()
    if ctx.channel.id in data['global_channels']:
        data['global_channels'].remove(ctx.channel.id)
        save_data(data)
        await ctx.send(f'Dieser Kanal wurde vom Globalchat entfernt.')
    else:
        await ctx.send('Dieser Kanal ist nicht im Globalchat.')

# Ban Command
@bot.command(name='ban', help='Bannt einen Benutzer oder Server vom Globalchat')
@commands.has_role(1262534683535609906)  # Ersetzen Sie durch die ID der entsprechenden Rolle
async def ban(ctx, id: int):
    data = load_data()
    if id not in data['banned_users'] and id not in data['banned_servers']:
        if ctx.guild.get_member(id):
            data['banned_users'].append(id)
        else:
            data['banned_servers'].append(id)
        save_data(data)
        await ctx.send(f'ID {id} wurde vom Globalchat gebannt.')
    else:
        await ctx.send('Diese ID ist bereits gebannt.')

# Unban Command
@bot.command(name='unban', help='Entbannt einen Benutzer oder Server vom Globalchat')
@commands.has_role(1262534683535609906)  # Ersetzen Sie durch die ID der entsprechenden Rolle
async def unban(ctx, id: int):
    data = load_data()
    if id in data['banned_users']:
        data['banned_users'].remove(id)
        save_data(data)
        await ctx.send(f'ID {id} wurde entbannt.')
    elif id in data['banned_servers']:
        data['banned_servers'].remove(id)
        save_data(data)
        await ctx.send(f'ID {id} wurde entbannt.')
    else:
        await ctx.send('Diese ID ist nicht gebannt.')

# Error Handling für fehlende Berechtigungen
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Netter Versuch. Du versuchst mich wohl illegaler weise zu benutzen. Du darfst das nicht. Du bist böse. Lass das. Aber keine Angst, dir passiert sonst weiter nix.")
    elif isinstance(error, commands.MissingRole):
        await ctx.send("Netter Versuch. Du versuchst mich wohl illegaler weise zu benutzen. Du darfst das nicht. Du bist böse. Lass das. Aber keine Angst, dir passiert sonst weiter nix.")
    else:
        raise error

# Globalchat Nachricht senden
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    data = load_data()

    if message.channel.id in data['global_channels']:
        if message.author.id in data['banned_users'] or message.guild.id in data['banned_servers']:
            return
        
        for channel_id in data['global_channels']:
            if channel_id != message.channel.id:
                channel = bot.get_channel(channel_id)
                if channel:
                    embed = discord.Embed(description=message.content, color=discord.Color.blue())
                    embed.set_author(name=f'{message.author} ({message.author.top_role.name})', icon_url=message.author.avatar.url)
                    await channel.send(embed=embed)

    await bot.process_commands(message)

# Status Fetch Task
@tasks.loop(seconds=19)
async def fetch_status():
    url = 'dein uptime kuma push link '
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                print('Status update sent successfully')
            else:
                print(f'Failed to send status update: {response.status}')

bot.run(TOKEN)
