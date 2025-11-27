# 機器人建置與使用教學
## 基礎環境
- Python（3.10+，建議使用 3.11+）
- Discord 伺服器（具管理員或擁有者的權限）
- Discord Bot（擁有 Token，並將它拉進 Discord 伺服器中）
> 不會建立 Bot 的話，可以依[這條影片](https://youtu.be/equ42VBYPrc?si=_81b7t4MDZGZwqs7)來操作
## Python 虛擬環境（Venv）與套件
1. 請先把本專案 clone 下來後，建立一個 Venv
2. 若有提示要安裝 `requirements.txt` 中的內容，安裝；否則在建立完 Venv 後，使用以下指令安裝
```bash
pip install -r requirements.txt
```
## 檔案修改
|原檔名|修改檔名|修改內容|
|:-:|:-:|:-:|
|`config.example.json`|`config.json`|依提示貼上頻道 ID|
|`token.example.env`|`token.env`|將 Discord Bot 的 Token 放入|
> 以上兩個檔案皆屬於敏感資訊，請勿上傳至公開的 GitHub

> 另外，若使用 Render 來線上跑 Discord Bot，請在 Render &rarr; Service &rarr; Environment Variables 新增 `DISCORD_BOT_TOKEN = <填入你的 BOT TOKEN>`