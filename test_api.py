import requests

TOKEN = "TU_TOKEN_AQUI"  # Cambia esto

print("🔍 Probando API de Telegram...")

# Prueba 1: getMe
try:
    url = f"https://api.telegram.org/bot{"8885575677:AAHN3u6FRWxtY2sVOe3Rlte1RzNPyz5djyM"}/getMe"
    r = requests.get(url, timeout=5)
    print(f"📡 getMe: {r.status_code}")
    print(f"📄 Respuesta: {r.text[:200]}")

    if r.status_code == 200:
        data = r.json()
        if data.get("ok"):
            print(f"✅ Bot encontrado: @{data['result']['username']}")
        else:
            print(f"❌ Token inválido: {data.get('description')}")
    else:
        print(f"❌ Error HTTP: {r.status_code}")

except Exception as e:
    print(f"❌ Error de conexión: {e}")
    print("   ¿Puedes acceder a https://api.telegram.org en tu navegador?")

print("\n" + "=" * 50)

# Prueba 2: getUpdates
try:
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    r = requests.get(url, timeout=5)
    print(f"📡 getUpdates: {r.status_code}")

    if r.status_code == 200:
        data = r.json()
        if data.get("ok"):
            updates = data.get("result", [])
            print(f"✅ {len(updates)} mensajes pendientes")
        else:
            print(f"❌ Error: {data.get('description')}")
    else:
        print(f"❌ Error HTTP: {r.status_code}")

except Exception as e:
    print(f"❌ Error: {e}")