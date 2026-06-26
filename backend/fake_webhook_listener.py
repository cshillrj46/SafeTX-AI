# File: backend/fake_webhook_listener.py

from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/alert")
async def receive_alert(request: Request):
    data = await request.json()
    print("\n[✅ Webhook recebido!]")
    print(data)
    return {"status": "received"}
