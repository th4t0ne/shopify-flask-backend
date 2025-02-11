from flask import Flask, request, jsonify
import requests
import os

# Inicjalizacja aplikacji Flask
app = Flask(__name__)

# Shopify API credentials
PASSWORD = os.environ.get("SHOPIFY_API_TOKEN")
SHOP_NAME = os.environ.get("SHOP_NAME", "hhwh1d-2p.myshopify.com")
API_VERSION = "2023-01"
BASE_URL = f"https://{SHOP_NAME}/admin/api/{API_VERSION}/"

# Endpoint główny
@app.route('/')
def home():
    return "Welcome to the Shopify Flask Backend!", 200

# Pobieranie pliku theme.liquid
@app.route('/get-theme', methods=['GET'])
def get_theme():
    try:
        theme_id = get_theme_id()
        if not theme_id:
            return jsonify({"error": "Could not fetch theme ID"}), 400

        asset_key = "layout/theme.liquid"
        response = requests.get(BASE_URL + f"themes/{theme_id}/assets.json", params={
            "asset[key]": asset_key
        }, headers={
            "X-Shopify-Access-Token": PASSWORD
        })

        if response.status_code == 200:
            asset_content = response.json().get("asset", {}).get("value", "")
            return jsonify({"theme_content": asset_content}), 200
        else:
            return jsonify({"error": response.json()}), 400
    except Exception as e:
        return jsonify({"error": f"Internal server error: {e}"}), 500

# Funkcja pomocnicza do pobierania ID głównego motywu
def get_theme_id():
    try:
        response = requests.get(BASE_URL + "themes.json", headers={
            "X-Shopify-Access-Token": PASSWORD
        })
        if response.status_code == 200:
            themes = response.json().get("themes", [])
            for theme in themes:
                if theme.get("role") == "main":
                    return theme.get("id")
        return None
    except Exception as e:
        return None

# Uruchomienie aplikacji
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
