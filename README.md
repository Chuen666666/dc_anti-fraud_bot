# Discord 防詐防炸機器人

這個 Bot 會監聽指定的「禁止發言」頻道。只要使用者在該頻道發言，Bot 就會踢出該成員，並自動刪除該成員五分鐘內在伺服器發過的訊息。

## 安全限制

- 有 Administrator 權限的成員不會被 Bot 自動踢出，即使 Bot 身分組比對方高也一樣。
- 擁有 `WHITELIST_ROLE_IDS` 白名單身分組的成員不會被 Bot 自動踢出，也不會發通知。
- Bot 會固定刪除該成員五分鐘內在伺服器發過的訊息，不透過 JSON 控制。
- 如果 `INFO_CHANNEL` 和 `info_msg` 都是 `null`，Bot 只會踢出和刪訊息，不會發通知。
- 如果 `INFO_CHANNEL` 和 `info_msg` 只有其中一個是 `null`，程式啟動時會直接報錯，避免部署後才發現設定不完整。

## 環境需求

- Python 3.13
- Node.js 24 LTS（僅作為本機工具鏈版本標示；此專案目前不是 Node app）
- Discord Bot Token
- Bot 需要以下 Discord 權限：
  - View Channels
  - Read Message History
  - Send Messages
  - Manage Messages
  - Kick Members

Bot 的身分組必須高於要踢出的非管理員成員，否則 Discord API 會拒絕 kick。若要刪除其他成員的歷史訊息，Bot 也需要 `Manage Messages` 權限。

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
  "server1": {
    "GUILD_ID": 111111111111111111,
    "INFO_CHANNEL": 123456789012345678,
    "NO_MSG_CHANNEL": 123456789012345678,
    "WHITELIST_ROLE_IDS": [
      111111111111111111
    ],
    "info_msg": "被懲處人：<user_id>\n懲處原因：於 <NO_MSG_CHANNEL> 傳送訊息\n使用法原：【文字頻道條例】第一、三條\n懲處內容：踢出伺服器，並自動刪除該使用者五分鐘內傳送的所有訊息"
  },
  "server_without_notification": {
    "GUILD_ID": 333333333333333333,
    "INFO_CHANNEL": null,
    "NO_MSG_CHANNEL": 345678901234567890,
    "WHITELIST_ROLE_IDS": [],
    "info_msg": null
  }
}
```

設定說明：

- `server1`、`server_without_notification`：你自己命名的 server name，可以改成任何容易辨識的名稱。
- `GUILD_ID`：Discord 伺服器 ID，Bot 會用這個 ID 找到對應設定。
- `INFO_CHANNEL`：發送通知的頻道 ID；若不發通知，必須設成 `null`。
- `NO_MSG_CHANNEL`：禁止發言的頻道 ID。
- 刪除歷史訊息的回溯時間固定為五分鐘，不能用 JSON 調整。
- `WHITELIST_ROLE_IDS`：身分組白名單。填入 Discord Role ID；擁有任一白名單身分組的成員不會被自動踢出。可省略或設成空陣列。
- `info_msg`：通知訊息，可使用 `<user_id>`、`<NO_MSG_CHANNEL>`、`<guild_name>` 和 `<server_name>` 佔位符；若不發通知，必須設成 `null`。

如果某個伺服器沒有填在 `config.json` 裡，Bot 會忽略該伺服器的訊息。

編輯 `token.env`：

```env
TOKEN=your_discord_bot_token
```

啟動 Bot：

```bash
python main.py
```

## 取得伺服器 ID

1. 在 Discord 使用者設定中開啟 Developer Mode。
2. 右鍵伺服器名稱。
3. 點選 Copy Server ID。
4. 把伺服器 ID 填到 `GUILD_ID`。

## 取得身分組 ID

1. 在 Discord 使用者設定中開啟 Developer Mode。
2. 到伺服器設定的 Roles / 身分組頁面。
3. 右鍵要加入白名單的身分組。
4. 點選 Copy Role ID。
5. 把身分組 ID 填到 `WHITELIST_ROLE_IDS`。

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

多伺服器部署時，只需要在 Render 的 `config.json` Secret File 裡新增一格 server name 和對應的 `GUILD_ID` 設定，不需要新增 Render service，也不需要建立多個 Bot Token。

## 開發工具

安裝開發依賴並執行 pre-commit：

```bash
pip install -r requirements-dev.txt
pre-commit install
pre-commit run --all-files
```

目前執行期依賴版本：

- `discord.py>=2.7.1`
- `python-dotenv>=1.2.2`

開發依賴版本：

- `pre-commit>=4.6.0`
- `ruff>=0.15.16`
- Ruff target version：Python 3.13
