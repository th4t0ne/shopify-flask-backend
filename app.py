from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Shopify API credentials
PASSWORD = os.environ.get("SHOPIFY_API_TOKEN")  # Admin API Access Token
SHOP_NAME = os.environ.get("SHOP_NAME", "hhwh1d-2p.myshopify.com")  # Default Shopify store name
API_VERSION = "2023-01"
BASE_URL = f"https://{SHOP_NAME}/admin/api/{API_VERSION}/"

@app.route('/')
def home():
    return "Welcome to the Shopify Flask Backend! Use /modify-theme or /get-theme to interact with Shopify.", 200

@app.route('/modify-theme', methods=['POST'])
def modify_theme():
    try:
        # Get JSON data from the request
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON or missing Content-Type header"}), 400

        prompt = data.get("prompt", "").lower()
        asset_key = "layout/theme.liquid"
        theme_id = get_theme_id()

        if not theme_id:
            return jsonify({"error": "Could not fetch theme ID"}), 400

        # Interpret prompts to generate the new content
        new_content = generate_content(prompt)
        if not new_content:
            return jsonify({"error": "Unsupported or invalid prompt"}), 400

        # Prepare data for Shopify API
        asset_data = {
            "asset": {
                "key": asset_key,
                "value": new_content
            }
        }

        # Send the request to update the theme
        response = requests.put(BASE_URL + f"themes/{theme_id}/assets.json", json=asset_data, headers={
            "X-Shopify-Access-Token": PASSWORD
        })

        if response.status_code == 200:
            return jsonify({"message": f"Theme asset '{asset_key}' updated successfully!"})
        else:
            app.logger.error(f"Error updating asset: {response.json()}")
            return jsonify({"error": response.json()}), 400

    except Exception as e:
        app.logger.error(f"Error in /modify-theme: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/get-theme', methods=['GET'])
def get_theme():
    """
    Fetch the current content of the theme.liquid file from Shopify.
    """
    try:
        theme_id = get_theme_id()  # Fetch the ID of the main theme
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
            app.logger.error(f"Error fetching asset: {response.json()}")
            return jsonify({"error": response.json()}), 400
    except Exception as e:
        app.logger.error(f"Error fetching theme.liquid: {e}")
        return jsonify({"error": "Internal server error"}), 500
