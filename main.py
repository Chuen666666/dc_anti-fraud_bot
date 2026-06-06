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
REQUIRED_SERVER_CONFIG_KEYS = {'GUILD_ID', 'INFO_CHANNEL', 'NO_MSG_CHANNEL', 'info_msg'}

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


def validate_optional_notification(
    server_config: dict[str, Any], server_name: str
) -> None:
    info_channel = server_config['INFO_CHANNEL']
    info_msg = server_config['info_msg']

    if info_channel is None and info_msg is None:
        return

    if info_channel is None or info_msg is None:
        raise RuntimeError(
            f'{server_name}.INFO_CHANNEL 和 {server_name}.info_msg 必須同時填值或同時為 null'
        )

    try:
        int(info_channel)
    except (TypeError, ValueError) as error:
        raise RuntimeError(
            f'{server_name}.INFO_CHANNEL 必須是 Discord ID 數字'
        ) from error

    if not isinstance(info_msg, str) or not info_msg:
        raise RuntimeError(f'{server_name}.info_msg 必須是非空字串')


def validate_whitelist(server_config: dict[str, Any], server_name: str) -> None:
    whitelist_role_ids = server_config.get('WHITELIST_ROLE_IDS', [])

    if not isinstance(whitelist_role_ids, list):
        raise RuntimeError(f'{server_name}.WHITELIST_ROLE_IDS 必須是陣列')

    for role_id in whitelist_role_ids:
        try:
            int(role_id)
        except (TypeError, ValueError) as error:
            raise RuntimeError(
                f'{server_name}.WHITELIST_ROLE_IDS 只能包含 Discord 身分組 ID 數字'
            ) from error


def validate_server_config(server_config: dict[str, Any], server_name: str) -> None:
    missing_keys = REQUIRED_SERVER_CONFIG_KEYS - server_config.keys()
    if missing_keys:
        missing_key_list = ', '.join(sorted(missing_keys))
        raise RuntimeError(f'{server_name} 缺少設定欄位：{missing_key_list}')

    for key in ('GUILD_ID', 'NO_MSG_CHANNEL'):
        try:
            int(server_config[key])
        except (TypeError, ValueError) as error:
            raise RuntimeError(f'{server_name}.{key} 必須是 Discord ID 數字') from error

    validate_optional_notification(server_config, server_name)
    validate_whitelist(server_config, server_name)


def load_config() -> dict[str, Any]:
    config_path = get_config_path()

    try:
        with config_path.open(encoding='utf-8') as config_file:
            config = json.load(config_file)
    except FileNotFoundError as error:
        raise RuntimeError(f'找不到設定檔：{config_path}') from error
    except json.JSONDecodeError as error:
        raise RuntimeError(f'設定檔不是合法 JSON：{config_path}') from error

    if not isinstance(config, dict):
        raise RuntimeError('設定檔最外層必須是物件')

    if not config:
        raise RuntimeError('設定檔至少要包含一個伺服器設定')

    for server_name, server_config in config.items():
        if not isinstance(server_config, dict):
            raise RuntimeError(f'{server_name} 必須是物件')
        validate_server_config(server_config, server_name)

    print(f'已讀取設定檔：{config_path}')
    return config


def get_server_config(guild_id: int) -> tuple[str, dict[str, Any]] | None:
    for server_name, server_config in config.items():
        if int(server_config['GUILD_ID']) == guild_id:
            return server_name, server_config

    return None


def get_timeout_until(server_config: dict[str, Any]) -> datetime.datetime:
    timeout_minutes = int(server_config.get('TIMEOUT_MINUTES', DEFAULT_TIMEOUT_MINUTES))
    timeout_minutes = min(timeout_minutes, DISCORD_MAX_TIMEOUT_MINUTES)
    return datetime.datetime.now(datetime.UTC) + datetime.timedelta(
        minutes=timeout_minutes
    )


def should_send_notification(server_config: dict[str, Any]) -> bool:
    return (
        server_config['INFO_CHANNEL'] is not None
        and server_config['info_msg'] is not None
    )


def is_whitelisted(member: discord.Member, server_config: dict[str, Any]) -> bool:
    whitelist_role_ids = {
        int(role_id) for role_id in server_config.get('WHITELIST_ROLE_IDS', [])
    }
    member_role_ids = {role.id for role in member.roles}
    return bool(whitelist_role_ids & member_role_ids)


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

    server_config_result = get_server_config(message.guild.id)
    if server_config_result is None:
        await bot.process_commands(message)
        return

    server_name, server_config = server_config_result
    no_msg_channel_id = int(server_config['NO_MSG_CHANNEL'])
    if message.channel.id != no_msg_channel_id:
        await bot.process_commands(message)
        return

    if not isinstance(message.author, discord.Member):
        return

    member = message.author
    if is_whitelisted(member, server_config):
        print(f'[Info] {member} 在白名單中，已略過自動停權。')
        return

    if member.guild_permissions.administrator:
        print(f'[Info] {member} 有 Administrator 權限，已略過自動停權。')
        return

    reason = f'在 <#{no_msg_channel_id}> 發言，觸發自動停權'

    try:
        await member.timeout(get_timeout_until(server_config), reason=reason)
    except discord.Forbidden:
        print(
            f'[Warning] 權限不足，無法停權 {member}。請確認 Bot 有 Moderate Members 權限，且身分組高於目標。'
        )
        return
    except discord.HTTPException as error:
        print(f'[Warning] Discord API 停權失敗：{error}')
        return

    if not should_send_notification(server_config):
        return

    notify_channel = message.guild.get_channel(int(server_config['INFO_CHANNEL']))
    if isinstance(notify_channel, discord.abc.Messageable):
        formatted_msg = (
            server_config['info_msg']
            .replace('<user_id>', f'<@{member.id}>')
            .replace('<NO_MSG_CHANNEL>', f'<#{no_msg_channel_id}>')
            .replace('<guild_name>', message.guild.name)
            .replace('<server_name>', server_name)
        )
        await notify_channel.send(formatted_msg)


if __name__ == '__main__':
    if not TOKEN:
        raise RuntimeError('找不到 TOKEN。請設定環境變數 TOKEN，或建立 token.env。')

    keep_alive()
    bot.run(TOKEN)
