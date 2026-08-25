import asyncio
import datetime
import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from typing import Any

import discord
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
DELETE_LOOKBACK_MINUTES = 5
DELETE_SCAN_PASSES = 2
DELETE_SCAN_CONCURRENCY = 2
REQUIRED_SERVER_CONFIG_KEYS = {'GUILD_ID', 'INFO_CHANNEL', 'NO_MSG_CHANNEL', 'info_msg'}


class HealthRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path != '/':
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        response = b"I'm alive!"
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, _request_format: str, *_args: Any) -> None:
        return


def run_health_server() -> None:
    port = int(os.environ.get('PORT', '8080'))
    with HTTPServer(('0.0.0.0', port), HealthRequestHandler) as server:
        server.serve_forever()


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


def get_delete_after() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC) - datetime.timedelta(
        minutes=DELETE_LOOKBACK_MINUTES
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


async def delete_recent_member_messages(
    guild: discord.Guild, member: discord.Member
) -> None:
    delete_after = get_delete_after()

    for scan_pass in range(1, DELETE_SCAN_PASSES + 1):
        for channel in guild.text_channels:
            try:
                async for recent_message in channel.history(
                    limit=None, after=delete_after
                ):
                    if recent_message.author.id != member.id:
                        continue

                    try:
                        await recent_message.delete()
                    except discord.Forbidden:
                        print(
                            f'[Warning] 第 {scan_pass} 輪沒有權限刪除 '
                            f'{channel.name} 的訊息。'
                        )
                    except discord.HTTPException as error:
                        print(
                            f'[Warning] 第 {scan_pass} 輪刪除 '
                            f'{channel.name} 的訊息失敗：{error}'
                        )
            except discord.Forbidden:
                print(
                    f'[Warning] 第 {scan_pass} 輪沒有權限讀取 '
                    f'{channel.name} 的訊息紀錄'
                )
            except discord.HTTPException as error:
                print(
                    f'[Warning] 第 {scan_pass} 輪讀取 '
                    f'{channel.name} 的訊息紀錄失敗：{error}'
                )


load_dotenv(dotenv_path=BASE_DIR / 'token.env')
TOKEN = os.getenv('TOKEN')
config = load_config()

intents = discord.Intents.none()
intents.guilds = True
intents.messages = True

bot = discord.Client(
    intents=intents,
    member_cache_flags=discord.MemberCacheFlags.none(),
    chunk_guilds_at_startup=False,
    max_messages=None,
)
delete_scan_slots = asyncio.Semaphore(DELETE_SCAN_CONCURRENCY)


@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot or message.guild is None:
        return

    server_config_result = get_server_config(message.guild.id)
    if server_config_result is None:
        return

    server_name, server_config = server_config_result
    no_msg_channel_id = int(server_config['NO_MSG_CHANNEL'])
    if message.channel.id != no_msg_channel_id:
        return

    if not isinstance(message.author, discord.Member):
        return

    member = message.author
    if is_whitelisted(member, server_config):
        print(f'[Info] {member} 在白名單中，已略過自動踢出')
        return

    if member.guild_permissions.administrator:
        print(f'[Info] {member} 有 Administrator 權限，已略過自動踢出')
        return

    reason = f'在 <#{no_msg_channel_id}> 發言，觸發自動踢出'

    try:
        await member.kick(reason=reason)
    except discord.Forbidden:
        print(
            f'[Warning] 權限不足，無法踢出 {member}。請確認 Bot 有 Kick Members 權限，且身分組高於目標。'
        )
        return
    except discord.HTTPException as error:
        print(f'[Warning] Discord API 踢出失敗：{error}')
        return

    async with delete_scan_slots:
        await delete_recent_member_messages(message.guild, member)

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
