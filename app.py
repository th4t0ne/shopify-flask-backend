from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Shopify API credentials
PASSWORD = os.environ.get("SHOPIFY_API_TOKEN")  # Admin API Access Token
SHOP_NAME = "hhwh1d-2p.myshopify.com"  # Oryginalny adres sklepu Shopify
BASE_URL = f"https://{SHOP_NAME}/admin/api/2023-01/"

@app.route('/')
def home():
    return "Welcome to the Shopify Flask Backend! Use /modify-theme to send requests.", 200

@app.route('/modify-theme', methods=['POST'])
def modify_theme():
    try:
        # Pobierz dane JSON z zapytania
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON or missing Content-Type header"}), 400

        prompt = data.get("prompt", "").lower()
        asset_key = "layout/theme.liquid"
        new_content = ""

        # Interpretacja promptów
        if "change the background color to" in prompt:
            bg_color = prompt.split("to")[1].strip()
            # Generowanie poprawnego kodu HTML
            new_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                {{ content_for_header }}
                <style>
                    body {{
                        background-color: {bg_color};
                    }}
                </style>
            </head>
            <body>
                {{ content_for_layout }}
            </body>
            </html>
            """
        else:
            return jsonify({"error": "Unsupported prompt"}), 400

        # Pobierz ID głównego motywu
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

        # Wyślij zmiany do Shopify
        response = requests.put(BASE_URL + f"themes/{theme_id}/assets.json", json=asset_data, headers={
            "X-Shopify-Access-Token": PASSWORD
        })
        if response.status_code == 200:
            return jsonify({"message": f"Theme asset '{asset_key}' updated successfully!"})
        else:
            return jsonify({"error": response.json()}), 400
    except Exception as e:
        app.logger.error(f"Error in /modify-theme: {e}")
        return jsonify({"error": "Internal server error"}), 500

def get_theme_id():
    try:
        # Wysłanie żądania do Shopify API w celu pobrania listy motywów
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
        app.logger.error(f"Error fetching theme ID: {e}")
        return None

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
