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
    """
    Strona główna aplikacji.
    """
    return "Welcome to the Shopify Flask Backend!", 200

# Pobieranie pliku theme.liquid
@app.route('/get-theme', methods=['GET'])
def get_theme():
    """
    Pobieranie zawartości pliku theme.liquid z Shopify.
    """
    try:
        app.logger.info("Fetching theme ID...")
        theme_id = get_theme_id()
        if not theme_id:
            app.logger.error("Could not fetch theme ID.")
            return jsonify({"error": "Could not fetch theme ID"}), 400

        app.logger.info(f"Theme ID fetched: {theme_id}")
        asset_key = "layout/theme.liquid"
        response = requests.get(BASE_URL + f"themes/{theme_id}/assets.json", params={
            "asset[key]": asset_key
        }, headers={
            "X-Shopify-Access-Token": PASSWORD
        })

        app.logger.info(f"Response from Shopify: {response.status_code}, {response.text}")
        if response.status_code == 200:
            asset_content = response.json().get("asset", {}).get("value", "")
            return jsonify({"theme_content": asset_content}), 200
        else:
            app.logger.error(f"Error fetching asset: {response.json()}")
            return jsonify({"error": response.json()}), 400
    except Exception as e:
        app.logger.error(f"Error fetching theme.liquid: {e}")
        return jsonify({"error": "Internal server error"}), 500

# Endpoint do modyfikacji pliku theme.liquid
@app.route('/modify-theme', methods=['POST'])
def modify_theme():
    """
    Modyfikacja zawartości pliku theme.liquid na Shopify.
    """
    try:
        app.logger.info("Processing modify-theme request...")
        data = request.get_json()
        if not data:
            app.logger.error("Invalid JSON or missing Content-Type header")
            return jsonify({"error": "Invalid JSON or missing Content-Type header"}), 400

        prompt = data.get("prompt", "").lower()
        app.logger.info(f"Received prompt: {prompt}")
        asset_key = "layout/theme.liquid"
        new_content = ""

        if "change the background color to" in prompt:
            bg_color = prompt.split("to")[1].strip()
            app.logger.info(f"Changing background color to: {bg_color}")
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
            app.logger.error("Unsupported prompt")
            return jsonify({"error": "Unsupported prompt"}), 400

        theme_id = get_theme_id()
        if not theme_id:
            app.logger.error("Could not fetch theme ID")
            return jsonify({"error": "Could not fetch theme ID"}), 400

        asset_data = {
            "asset": {
                "key": asset_key,
                "value": new_content
            }
        }

        response = requests.put(BASE_URL + f"themes/{theme_id}/assets.json", json=asset_data, headers={
            "X-Shopify-Access-Token": PASSWORD
        })

        if response.status_code == 200:
            app.logger.info(f"Theme asset '{asset_key}' updated successfully!")
            return jsonify({"message": f"Theme asset '{asset_key}' updated successfully!"})
        else:
            app.logger.error(f"Error updating asset: {response.json()}")
            return jsonify({"error": response.json()}), 400
    except Exception as e:
        app.logger.error(f"Error in /modify-theme: {e}")
        return jsonify({"error": "Internal server error"}), 500

# Funkcja pomocnicza do pobierania ID głównego motywu
def get_theme_id():
    """
    Pobieranie ID głównego motywu z Shopify.
    """
    try:
        response = requests.get(BASE_URL + "themes.json", headers={
            "X-Shopify-Access-Token": PASSWORD
        })
        app.logger.info(f"Response from Shopify (themes): {response.status_code}, {response.text}")
        if response.status_code == 200:
            themes = response.json().get("themes", [])
            for theme in themes:
                if theme.get("role") == "main":
                    app.logger.info(f"Main theme found: {theme.get('id')}")
                    return theme.get("id")
        app.logger.error(f"Error fetching themes: {response.json()}")
        return None
    except Exception as e:
        app.logger.error(f"Error in get_theme_id: {e}")
        return None

# Uruchomienie aplikacji
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
