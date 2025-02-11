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
  
