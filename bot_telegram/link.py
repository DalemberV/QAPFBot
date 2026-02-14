import requests

TOKEN = " " #de botfather
WEBHOOK_URL = " " #de modal

url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}"

response = requests.get(url)
print(response.json())

#git push origin main --force