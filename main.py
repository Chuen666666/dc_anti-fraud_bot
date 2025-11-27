import datetime
import json
import os
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

# 定義 BASE_DIR
BASE_DIR = Path(__file__).resolve().parent

# 讀取 config.json
CONFIG_PATH = BASE_DIR / 'config.json'
with CONFIG_PATH.open('r', encoding='utf-8') as f:
    config = json.load(f)

INFO_CHANNEL_ID = config['INFO_CHANNEL']
NO_MSG_CHANNEL_ID = config['NO_MSG_CHANNEL']
INFO_MESSAGE_TEMPLATE = config['info_msg']

# 讀取 token.env
load_dotenv(dotenv_path=BASE_DIR / 'token.env')
TOKEN = os.getenv('TOKEN')

# 設定 intents
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# 事件：監聽訊息
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.channel.id == NO_MSG_CHANNEL_ID:
        guild = message.guild
        target = message.author

        now = datetime.datetime.now(datetime.timezone.utc)
        time_limit = now - datetime.timedelta(minutes=5)

        # 清除該使用者五分鐘內訊息
        for channel in guild.text_channels:
            try:
                async for msg in channel.history(limit=None, after=time_limit):
                    if msg.author.id == target.id:
                        try:
                            await msg.delete()
                        except discord.Forbidden:
                            print(f'[Warning] 沒有刪除 {channel.name} 的權限')
                        except discord.HTTPException as e:
                            print(f'[Warning] 刪除訊息失敗: {e}')
            except discord.Forbidden:
                print(f'[Warning] 無法讀取頻道 {channel.name}（缺權限）')
            except discord.HTTPException as e:
                print(f'[Warning] 讀取頻道錯誤 {channel.name}: {e}')

        # 踢出使用者
        try:
            await guild.kick(target, reason='於禁言頻道傳送訊息')
        except discord.Forbidden:
            print('權限不足無法踢出使用者')
        except discord.HTTPException:
            print('Discord API 錯誤')

        # 發送通知
        notify_channel = guild.get_channel(INFO_CHANNEL_ID)
        if notify_channel:
            formatted_msg = INFO_MESSAGE_TEMPLATE.format(user=target, NO_MSG_CHANNEL=NO_MSG_CHANNEL_ID)
            await notify_channel.send(formatted_msg)

    await bot.process_commands(message)

# 啟動 bot
bot.run(TOKEN)