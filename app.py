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
    return "Welcome to the Shopify Flask Backend! Use /modify-theme to send requests.", 200

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


def generate_content(prompt):
    """
    Generate Liquid template content based on the user's prompt.
    """
    try:
        if "change the background color to" in prompt:
            bg_color = prompt.split("to")[1].strip()
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                {{% content_for_header %}}
                <style>
                    body {{
                        background-color: {bg_color};
                    }}
                </style>
            </head>
            <body>
                {{% content_for_layout %}}
            </body>
            </html>
            """
        elif "add custom header" in prompt:
            header_content = prompt.split("header")[1].strip()
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                {{% content_for_header %}}
                <style>
                    header {{
                        background-color: #000;
                        color: #fff;
                        padding: 10px;
                        text-align: center;
                    }}
                </style>
            </head>
            <body>
                <header>{header_content}</header>
                {{% content_for_layout %}}
            </body>
            </html>
            """
        else:
            return None
    except Exception as e:
        app.logger.error(f"Error in generate_content: {e}")
        return None


def get_theme_id():
    """
    Fetch the ID of the main theme from Shopify API.
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
        app.logger.error(f"Error fetching theme ID: {response.json()}")
        return None
    except Exception as e:
        app.logger.error(f"Error fetching theme ID: {e}")
        return None


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
