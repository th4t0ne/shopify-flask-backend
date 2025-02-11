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

@app.route('/')
def home():
    """
    Strona główna aplikacji.
    """
    return "Welcome to the Shopify Flask Backend!", 200

@app.route('/get-theme', methods=['GET'])
def get_theme():
    """
    Pobieranie zawartości pliku theme.liquid z Shopify.
    """
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

@app.route('/modify-theme', methods=['POST'])
def modify_theme():
    """
    Modyfikacja zawartości pliku theme.liquid na Shopify.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON or missing Content-Type header"}), 400

        prompt = data.get("prompt", "").lower()
        asset_key = "layout/theme.liquid"
        theme_id = get_theme_id()

        if not theme_id:
            return jsonify({"error": "Could not fetch theme ID"}), 400

        # Pobierz bieżącą zawartość pliku theme.liquid
        response = requests.get(BASE_URL + f"themes/{theme_id}/assets.json", params={
            "asset[key]": asset_key
        }, headers={
            "X-Shopify-Access-Token": PASSWORD
        })

        if response.status_code != 200:
            return jsonify({"error": response.json()}), 400

        current_content = response.json().get("asset", {}).get("value", "")

        # Tworzenie nowej zawartości na podstawie promptu
        new_content = current_content
        if "change the font to" in prompt:
            font = prompt.split("to")[1].strip()
            new_content = current_content.replace(
                "{{ content_for_header }}",
                f"""
                {{% comment %}} Custom styles injected {{% endcomment %}}
                {{ content_for_header }}
                <style>
                    body {{
                        font-family: {font}, sans-serif;
                    }}
                </style>
                """
            )
        elif "change the background color to" in prompt:
            bg_color = prompt.split("to")[1].strip()
            new_content = current_content.replace(
                "{{ content_for_layout }}",
                f"""
                <style>
                    body {{
                        background-color: {bg_color};
                    }}
                </style>
                {{ content_for_layout }}
                """
            )
        else:
            return jsonify({"error": "Unsupported prompt"}), 400

        # Zapisz zmienioną zawartość do Shopify
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
            return jsonify({"message": f"Theme asset '{asset_key}' updated successfully!"}), 200
        else:
            return jsonify({"error": response.json()}), 400

    except Exception as e:
        return jsonify({"error": f"Internal server error: {e}"}), 500

def get_theme_id():
    """
    Pobieranie ID głównego motywu z Shopify.
    """
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
