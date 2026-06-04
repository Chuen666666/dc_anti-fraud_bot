# Discord Anti-Fraud Bot

偵測使用者是否在指定的「禁止發言」頻道發言。一旦觸發，機器人會直接對該成員套用 Discord timeout 停權，不再逐一掃描每個頻道刪訊息。

## Requirements

- Python 3.13
- Node.js 24 LTS（僅供本機工具鏈標示；此專案目前沒有 Node app）
- Discord Bot Token
- Bot 需要以下 Discord 權限：
  - View Channels
  - Read Message History
  - Send Messages
  - Moderate Members

Bot 的身分組必須高於要停權的成員，否則 Discord API 會拒絕 timeout。

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy config.example.json config.json
copy token.example.env token.env
```

編輯 `config.json`：

```json
{
  "INFO_CHANNEL": 123456789012345678,
  "NO_MSG_CHANNEL": 123456789012345678,
  "TIMEOUT_MINUTES": 40320,
  "info_msg": "偵測到 <user_id> 在 <NO_MSG_CHANNEL> 發言，已自動停權。"
}
```

- `INFO_CHANNEL`: 發送通知的頻道 ID
- `NO_MSG_CHANNEL`: 禁止發言的頻道 ID
- `TIMEOUT_MINUTES`: 停權分鐘數。Discord timeout 上限是 28 天，所以最大有效值是 `40320`
- `info_msg`: 通知訊息，可使用 `<user_id>` 和 `<NO_MSG_CHANNEL>` 佔位符

編輯 `token.env`：

```env
TOKEN=your_discord_bot_token
```

啟動：

```bash
python main.py
```

## Render Deploy

建立 Render Web Service，設定：

- Runtime: Python 3
- Build Command: `pip install -r requirements.txt`
- Start Command: `python main.py`
- Health Check Path: `/`

Environment Variables:

- `TOKEN`: Discord Bot Token

Secret Files:

- Filename: `config.json`
- File Contents: 填入和 `config.example.json` 相同格式的 JSON

Render 目前使用 Python 3.13 時，這份設定可直接安裝目前的依賴版本。

## Development

安裝 pre-commit：

```bash
pre-commit install
pre-commit run --all-files
```

目前設定使用：

- `discord.py>=2.7.1`
- `Flask>=3.1.3`
- `python-dotenv>=1.2.2`
- `pre-commit>=4.6.0`
- `ruff>=0.15.16`
- Ruff target version: Python 3.13
