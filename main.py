import datetime
import json
import os
from pathlib import Path
from threading import Thread

import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask


# 啟動迷你網頁，讓 Render 持續上線
app = Flask(__name__)


@app.route('/')
def home():
    return "I'm alive!"


def run():
    app.run(host='0.0.0.0', port=8080)


def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()


# 定義 BASE_DIR
BASE_DIR = Path(__file__).resolve().parent

# 讀取 config.json
if os.path.exists('/etc/secrets/config.json'):
    CONFIG_PATH = Path('/etc/secrets/config.json')
elif (BASE_DIR / 'config.json').exists():
    CONFIG_PATH = BASE_DIR / 'config.json'
else:
    CONFIG_PATH = Path('config.json')

try:
    with CONFIG_PATH.open('r', encoding='utf-8') as f:
        config = json.load(f)
    print(f'成功讀取設定檔：{CONFIG_PATH}')
except Exception as e:
    print(f'讀取設定檔失敗！路徑：{CONFIG_PATH}，錯誤：{e}')

# 讀取 token.env
TOKEN = os.getenv('TOKEN')

if not TOKEN:
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

    if message.guild is None:
        return

    if message.channel.id == config['NO_MSG_CHANNEL']:
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
        notify_channel = guild.get_channel(config['INFO_CHANNEL'])
        if notify_channel:
            formatted_msg = (
                config['info_msg']
                .replace('<user_id>', f'<@{target.id}>')
                .replace('<NO_MSG_CHANNEL>', f'<#{config["NO_MSG_CHANNEL"]}>')
            )

            if isinstance(notify_channel, discord.abc.Messageable):
                await notify_channel.send(formatted_msg)

    await bot.process_commands(message)


# 啟動 bot
if __name__ == '__main__':
    if TOKEN:
        keep_alive()
        bot.run(TOKEN)
    else:
        print('錯誤！TOKEN 為空')
