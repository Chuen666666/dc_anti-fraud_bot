# Discord 防詐防炸機器人

## 基礎環境

- Python（3.10+，建議使用 3.11+）
- Discord 伺服器（具管理員或擁有者的權限）
- Discord Bot（擁有 Token，並將它拉進 Discord 伺服器中）
- （可選）Ruff

> 不會建立 Bot 的話，可以依[這條影片](https://youtu.be/equ42VBYPrc?si=_81b7t4MDZGZwqs7)來操作

## Python 虛擬環境（Venv）與套件

1. 請先把本專案 clone 下來後，建立一個 Venv
2. 使用以下指令安裝依賴

```bash
pip install -r requirements.txt
```

## 從範例檔建立必要檔案

```bash
cp config.example.json config.json
cp token.example.env token.env
```

> 若使用 Windows 系統，請改用 `copy` 而非 `cp`

> 以上兩個檔案皆屬於敏感資訊，請勿上傳至公開的 GitHub

> 複製後，請到被複製的兩個文件中，依提示填上相應的資訊

## 啟動機器人

在 Venv 啟動的狀態下，執行以下指令（或以其他方式開啟 `main.py`）

```bash
python main.py
```

## Render 設定

若機器人跑在 Render 環境，它會自動維持上線狀態，Render 和 UptimeRobot 的設定方式如下：

1. 創建一個 Web Service
2. 選擇機器人的 GitHub Repo（可先 Fork 此 Repo）
3. 填入以下設定
   - Runtime: `Python3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py`
   - Environment Variables：填入名稱 `TOKEN` 以及具體的 Discord Bot Token 進去
   - Advanced
     - Secret Files：`Filename` 填入 `config.json`、`File Contents` 填入該 JSON 檔內容
     - Health Check Path: `/`（預設為 `/healthz`）
4. 最後點擊 `Deploy Web Service`
5. 至 UptimeRobot：創建 HTTP / website monitoring 並填入 Render 中該 Bot 的網址
