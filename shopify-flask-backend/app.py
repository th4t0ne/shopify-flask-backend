from flask import Flask, request, jsonify
import requests
import os
import logging
from typing import Optional

# Konfiguracja loggera
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Konfiguracja aplikacji Flask
class Config:
    PASSWORD: str = os.environ.get("SHOPIFY_API_TOKEN", "")
    SHOP_NAME: str = os.environ.get("SHOP_NAME", "hhwh1d-2p.myshopify.com")
    API_VERSION: str = "2023-01"
    BASE_URL: str = f"https://{SHOP_NAME}/admin/api/{API_VERSION}/"

    @staticmethod
    def validate():
        if not Config.PASSWORD or not Config.SHOP_NAME:
            raise ValueError("Missing required environment variables: SHOPIFY_API_TOKEN or SHOP_NAME")

Config.validate()

app = Flask(__name__)

def get_theme_id() -> Optional[int]:
    """
    Pobiera ID głównego motywu z Shopify.
    """
    try:
        response = requests.get(
            Config.BASE_URL + "themes.json",
            headers={"X-Shopify-Access-Token": Config.PASSWORD}
        )
        response.raise_for_status()
        themes = response.json().get("themes", [])
        for theme in themes:
            if theme.get("role") == "main":
                return theme.get("id")
    except requests.RequestException as e:
        logger.error(f"Error fetching theme ID: {e}")
    return None

def fetch_theme_content(theme_id: int, asset_key: str) -> Optional[str]:
    """
    Pobiera zawartość pliku szablonu (np. theme.liquid).
    """
    try:
        response = requests.get(
            Config.BASE_URL + f"themes/{theme_id}/assets.json",
            params={"asset[key]": asset_key},
            headers={"X-Shopify-Access-Token": Config.PASSWORD}
        )
        response.raise_for_status()
        asset = response.json().get("asset", {})
        return asset.get("value", "")
    except requests.RequestException as e:
        logger.error(f"Error fetching asset content for '{asset_key}': {e}")
    return None

def update_theme_content(theme_id: int, asset_key: str, content: str) -> bool:
    """
    Aktualizuje zawartość pliku szablonu w Shopify.
    """
    try:
        response = requests.put(
            Config.BASE_URL + f"themes/{theme_id}/assets.json",
            json={"asset": {"key": asset_key, "value": content}},
            headers={"X-Shopify-Access-Token": Config.PASSWORD}
        )
        response.raise_for_status()
        return response.status_code == 200
    except requests.RequestException as e:
        logger.error(f"Error updating asset content for '{asset_key}': {e}")
    return False

def ensure_placeholder_in_content(content: str) -> str:
    """
    Upewnia się, że w szablonie znajdują się wymagane placeholdery.
    """
    if "{{ content_for_header }}" not in content:
        logger.info("Adding missing {{ content_for_header }} to the template.")
        content = content.replace(
            "<head>", "<head>\n    {{ content_for_header }}"
        )
    if "{{ content_for_layout }}" not in content:
        logger.info("Adding missing {{ content_for_layout }} to the template.")
        content = content.replace(
            "<body>", "<body>\n    {{ content_for_layout }}"
        )
    return content

@app.route('/modify-theme', methods=['POST'])
def modify_theme():
    """
    Modyfikuje zawartość pliku theme.liquid na Shopify.
    """
    try:
        data = request.get_json()
        if not data or "prompt" not in data:
            return jsonify({"error": "Invalid JSON or missing 'prompt' key"}), 400

        prompt = data["prompt"].lower()
        theme_id = get_theme_id()
        if not theme_id:
            return jsonify({"error": "Could not fetch theme ID"}), 400

        asset_key = "layout/theme.liquid"
        current_content = fetch_theme_content(theme_id, asset_key)
        if current_content is None:
            return jsonify({"error": "Could not fetch theme content"}), 400

        # Ensure required placeholders exist
        updated_content = ensure_placeholder_in_content(current_content)

        # Apply changes based on the prompt
        if "change the font to" in prompt:
            font = prompt.split("to")[1].strip()
            updated_content = updated_content.replace(
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

        # Update the theme content in Shopify
        if update_theme_content(theme_id, asset_key, updated_content):
            return jsonify({"message": f"Theme asset '{asset_key}' updated successfully!"}), 200
        else:
            return jsonify({"error": "Failed to update theme content"}), 500

    except Exception as e:
        logger.exception("Unexpected error during theme modification")
        return jsonify({"error": f"Internal server error: {e}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
