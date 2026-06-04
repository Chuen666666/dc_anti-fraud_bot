# Discord 防詐防炸機器人

這個 Bot 會監聽指定的「禁止發言」頻道。只要使用者在該頻道發言，Bot 就會直接對該成員套用 Discord timeout 停權，不再逐一掃描每個頻道刪訊息。

## 環境需求

- Python 3.13
- Node.js 24 LTS（僅作為本機工具鏈版本標示；此專案目前不是 Node app）
- Discord Bot Token
- Bot 需要以下 Discord 權限：
  - View Channels
  - Read Message History
  - Send Messages
  - Moderate Members（成員停權）

Bot 的身分組必須高於要停權的成員，否則 Discord API 會拒絕 timeout。

## 本機設定

建立虛擬環境並安裝套件：

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

從範例檔建立本機設定檔：

```bash
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

- `INFO_CHANNEL`：發送通知的頻道 ID
- `NO_MSG_CHANNEL`：禁止發言的頻道 ID
- `TIMEOUT_MINUTES`：停權分鐘數。Discord timeout 上限是 28 天，所以最大有效值是 `40320`
- `info_msg`：通知訊息，可使用 `<user_id>` 和 `<NO_MSG_CHANNEL>` 佔位符

編輯 `token.env`：

```env
TOKEN=your_discord_bot_token
```

啟動 Bot：

```bash
python main.py
```

## Render 部署

建立 Render Web Service，使用以下設定：

- Runtime：Python 3
- Build Command：`pip install -r requirements.txt`
- Start Command：`python main.py`
- Health Check Path：`/`

Environment Variables：

- `TOKEN`：Discord Bot Token

Secret Files：

- Filename：`config.json`
- File Contents：填入和 `config.example.json` 相同格式的 JSON

Render 使用 Python 3.13 時，這份設定可以直接安裝目前的依賴版本。

## 開發工具

安裝並執行 pre-commit：

```bash
pre-commit install
pre-commit run --all-files
```

目前依賴版本：

- `discord.py>=2.7.1`
- `Flask>=3.1.3`
- `python-dotenv>=1.2.2`
- `pre-commit>=4.6.0`
- `ruff>=0.15.16`
- Ruff target version：Python 3.13
