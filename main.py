import datetime
import json
import os
from pathlib import Path
from threading import Thread
from typing import Any

import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_TIMEOUT_MINUTES = 28 * 24 * 60
DISCORD_MAX_TIMEOUT_MINUTES = 28 * 24 * 60

app = Flask(__name__)


@app.route('/')
def home() -> str:
    return "I'm alive!"


def run_health_server() -> None:
    port = int(os.environ.get('PORT', '8080'))
    app.run(host='0.0.0.0', port=port)


def keep_alive() -> None:
    Thread(target=run_health_server, daemon=True).start()


def get_config_path() -> Path:
    render_secret_path = Path('/etc/secrets/config.json')

    if render_secret_path.exists():
        return render_secret_path

    local_config_path = BASE_DIR / 'config.json'
    if local_config_path.exists():
        return local_config_path

    return Path('config.json')


def load_config() -> dict[str, Any]:
    config_path = get_config_path()

    try:
        with config_path.open(encoding='utf-8') as config_file:
            config = json.load(config_file)
    except FileNotFoundError as error:
        raise RuntimeError(f'找不到設定檔: {config_path}') from error
    except json.JSONDecodeError as error:
        raise RuntimeError(f'設定檔不是合法 JSON: {config_path}') from error

    required_keys = {'INFO_CHANNEL', 'NO_MSG_CHANNEL', 'info_msg'}
    missing_keys = required_keys - config.keys()
    if missing_keys:
        missing_key_list = ', '.join(sorted(missing_keys))
        raise RuntimeError(f'設定檔缺少欄位: {missing_key_list}')

    print(f'已讀取設定檔: {config_path}')
    return config


def get_timeout_until(config: dict[str, Any]) -> datetime.datetime:
    timeout_minutes = int(config.get('TIMEOUT_MINUTES', DEFAULT_TIMEOUT_MINUTES))
    timeout_minutes = min(timeout_minutes, DISCORD_MAX_TIMEOUT_MINUTES)
    return datetime.datetime.now(datetime.UTC) + datetime.timedelta(
        minutes=timeout_minutes
    )


load_dotenv(dotenv_path=BASE_DIR / 'token.env')
TOKEN = os.getenv('TOKEN')
config = load_config()

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot or message.guild is None:
        return

    if message.channel.id != config['NO_MSG_CHANNEL']:
        await bot.process_commands(message)
        return

    if not isinstance(message.author, discord.Member):
        return

    member = message.author
    reason = f'在 <#{config["NO_MSG_CHANNEL"]}> 發言, 觸發自動停權'

    try:
        await member.timeout(get_timeout_until(config), reason=reason)
    except discord.Forbidden:
        print(
            f'[Warning] 權限不足, 無法停權 {member}。請確認機器人有「成員停權」權限且身分組高於目標。'
        )
        return
    except discord.HTTPException as error:
        print(f'[Warning] Discord API 停權失敗: {error}')
        return

    notify_channel = message.guild.get_channel(config['INFO_CHANNEL'])
    if isinstance(notify_channel, discord.abc.Messageable):
        formatted_msg = (
            config['info_msg']
            .replace('<user_id>', f'<@{member.id}>')
            .replace('<NO_MSG_CHANNEL>', f'<#{config["NO_MSG_CHANNEL"]}>')
        )
        await notify_channel.send(formatted_msg)


if __name__ == '__main__':
    if not TOKEN:
        raise RuntimeError('找不到 TOKEN。請設定環境變數 TOKEN, 或建立 token.env。')

    keep_alive()
    bot.run(TOKEN)
