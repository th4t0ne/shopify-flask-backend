import os
import requests
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

# Inicjalizacja aplikacji Flask
app = Flask(__name__)

# Konfiguracja Shopify API
PASSWORD = os.environ.get("SHOPIFY_API_TOKEN")
SHOP_NAME = os.environ.get("SHOP_NAME", "hhwh1d-2p.myshopify.com")
API_VERSION = "2023-01"
BASE_URL = f"https://{SHOP_NAME}/admin/api/{API_VERSION}/"
UPLOAD_FOLDER = "uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Endpoint: Strona główna
@app.route('/')
def home():
    return "Welcome to the Shopify Flask Backend!", 200

# Endpoint: Pobieranie treści pliku theme.liquid
@app.route('/get-theme', methods=['GET'])
def get_theme():
    try:
        theme_id = get_theme_id()
        if not theme_id:
            return jsonify({"error": "Could not fetch theme ID"}), 400

        asset_key = "layout/theme.liquid"
        response = requests.get(
            BASE_URL + f"themes/{theme_id}/assets.json", 
            params={"asset[key]": asset_key}, 
            headers={"X-Shopify-Access-Token": PASSWORD}
        )

        if response.status_code == 200:
            asset_content = response.json().get("asset", {}).get("value", "")
            return jsonify({"theme_content": asset_content}), 200
        else:
            return jsonify({"error": response.json()}), 400
    except Exception as e:
        return jsonify({"error": f"Internal server error: {e}"}), 500

# Endpoint: Modyfikacja pliku theme.liquid
@app.route('/modify-theme', methods=['POST'])
def modify_theme():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON or missing Content-Type header"}), 400

        prompt = data.get("prompt", "").lower()
        theme_id = get_theme_id()
        if not theme_id:
            return jsonify({"error": "Could not fetch theme ID"}), 400

        # Pobranie bieżącej zawartości pliku theme.liquid
        asset_key = "layout/theme.liquid"
        response = requests.get(
            BASE_URL + f"themes/{theme_id}/assets.json", 
            params={"asset[key]": asset_key}, 
            headers={"X-Shopify-Access-Token": PASSWORD}
        )

        if response.status_code != 200:
            return jsonify({"error": response.json()}), 400

        current_content = response.json().get("asset", {}).get("value", "")

        # Dodanie brakujących placeholderów, jeśli ich brakuje
        if "{{ content_for_header }}" not in current_content:
            current_content = current_content.replace(
                "<head>",
                "<head>\n    {{ content_for_header }}"
            )
        if "{{ content_for_layout }}" not in current_content:
            current_content = current_content.replace(
                "<body>",
                "<body>\n    {{ content_for_layout }}"
            )

        # Aktualizacja zawartości na podstawie promptu
        if "change the font to" in prompt:
            font = prompt.split("to")[1].strip()
            new_content = current_content.replace(
                "{{ content_for_header }}",
                f"""
                {{% comment %}} Custom font style added {{% endcomment %}}
                {{ content_for_header }}
                <style>
                    body {{
                        font-family: {font}, sans-serif;
                    }}
                </style>
                """
            )
        else:
            return jsonify({"error": "Unsupported prompt"}), 400

        # Zapisanie zmienionej zawartości w Shopify
        asset_data = {
            "asset": {
                "key": asset_key,
                "value": new_content
            }
        }

        response = requests.put(
            BASE_URL + f"themes/{theme_id}/assets.json", 
            json=asset_data, 
            headers={"X-Shopify-Access-Token": PASSWORD}
        )

        if response.status_code == 200:
            return jsonify({"message": f"Theme asset '{asset_key}' updated successfully!"}), 200
        else:
            return jsonify({"error": response.json()}), 400

    except Exception as e:
        return jsonify({"error": f"Internal server error: {e}"}), 500

# Endpoint: Wgrywanie zdjęcia
@app.route('/upload-image', methods=['POST'])
def upload_image():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Upload zdjęcia do Shopify
        with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'rb') as f:
            response = requests.post(
                BASE_URL + "images.json",
                headers={"X-Shopify-Access-Token": PASSWORD},
                files={"image": f}
            )

        if response.status_code == 200:
            return jsonify({"message": "Image uploaded successfully!", "data": response.json()}), 200
        else:
            return jsonify({"error": response.json()}), 400

    except Exception as e:
        return jsonify({"error": f"Internal server error: {e}"}), 500

# Funkcja: Pobieranie ID motywu
def get_theme_id():
    try:
        response = requests.get(
            BASE_URL + "themes.json", 
            headers={"X-Shopify-Access-Token": PASSWORD}
        )
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
