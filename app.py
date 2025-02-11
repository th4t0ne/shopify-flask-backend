from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Shopify API credentials
import os

PASSWORD = os.environ.get("SHOPIFY_API_TOKEN")  # Wczytanie tokenu z zmiennej środowiskowej
SHOP_NAME = "yourshop.myshopify.com"
BASE_URL = f"https://{SHOP_NAME}/admin/api/2023-01/"


@app.route('/')
def home():
    return "Welcome to the Shopify Flask Backend! Use /modify-theme to send requests.", 200

@app.route('/modify-theme', methods=['POST'])
def modify_theme():
    try:
        # Pobierz JSON z żądania
        data = request.get_json()
        
        # Jeśli JSON jest pusty lub brak nagłówka Content-Type
        if data is None:
            return jsonify({"error": "Invalid JSON or missing Content-Type header"}), 400
        
        # Wyciągnij prompt
        prompt = data.get("prompt", "")
        
        # Walidacja promptu
        if "background color" in prompt and "theme.liquid" in prompt:
            asset_key = "layout/theme.liquid"
            new_content = "<style> body { background-color: black; } </style>"
        else:
            return jsonify({"error": "Unsupported prompt"}), 400

        # Pobranie ID głównego motywu
        theme_id = get_theme_id()
        if not theme_id:
            return jsonify({"error": "Could not fetch theme ID"}), 400

        # Przygotowanie danych do wysłania
        asset_data = {
            "asset": {
                "key": asset_key,
                "value": new_content
            }
        }

        # Wysłanie żądania do Shopify API
        response = requests.put(BASE_URL + f"themes/{theme_id}/assets.json", json=asset_data, headers={
            "X-Shopify-Access-Token": PASSWORD
        })
        
        # Walidacja odpowiedzi
        if response.status_code == 200:
            return jsonify({"message": f"Theme asset '{asset_key}' updated successfully!"})
        else:
            return jsonify({"error": response.json()}), 400
    except Exception as e:
        app.logger.error(f"Error in /modify-theme: {e}")
        return jsonify({"error": "Internal server error"}), 500

def get_theme_id():
    try:
        # Wysłanie żądania do Shopify API w celu pobrania motywów
        response = requests.get(BASE_URL + "themes.json", headers={
            "X-Shopify-Access-Token": PASSWORD
        })
        app.logger.info(f"Shopify API response: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            themes = response.json()["themes"]
            for theme in themes:
                if theme["role"] == "main":
                    return theme["id"]
        else:
            app.logger.error(f"Error fetching themes: {response.json()}")
            return None
    except Exception as e:
        app.logger.error(f"Error in get_theme_id: {e}")
        return None

if __name__ == "__main__":
    # Pobierz port ze zmiennej środowiskowej lub ustaw domyślny
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
