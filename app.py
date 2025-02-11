import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import openai
import logging

# Load environment variables from .env file
load_dotenv()

# Flask app initialization
app = Flask(__name__)

# Shopify API credentials
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_API_TOKEN")
SHOP_NAME = os.getenv("SHOP_NAME")
SHOPIFY_API_VERSION = "2023-01"
BASE_URL = f"https://{SHOP_NAME}/admin/api/{SHOPIFY_API_VERSION}"

# OpenAI API credentials
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

# Verify required environment variables
REQUIRED_ENV_VARS = ["SHOPIFY_ACCESS_TOKEN", "SHOP_NAME", "OPENAI_API_KEY"]
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    raise EnvironmentError(f"Brakujące klucze środowiskowe: {', '.join(missing_vars)}")


# Endpoint to modify the Shopify theme based on user input
@app.route('/modify-theme', methods=['POST'])
def modify_theme():
    """
    Endpoint for modifying Shopify theme based on user input.
    """
    try:
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({"error": "Missing 'prompt' in request data"}), 400

        prompt = data['prompt']
        logger.info(f"Received prompt: {prompt}")

        # Process the prompt with GPT to generate changes
        gpt_response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"Given the Shopify theme context, implement the following: {prompt}",
            max_tokens=500
        )
        new_content = gpt_response['choices'][0]['text'].strip()

        logger.info("GPT generated content successfully")

        # Update Shopify theme.liquid
        asset_key = "layout/theme.liquid"
        response = requests.put(
            f"{BASE_URL}/themes/<YOUR_THEME_ID>/assets.json",
            json={
                "asset": {
                    "key": asset_key,
                    "value": new_content
                }
            },
            headers={
                "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
                "Content-Type": "application/json"
            }
        )

        if response.status_code == 200:
            logger.info("Theme updated successfully")
            return jsonify({"success": "Theme updated successfully"}), 200
        else:
            logger.error(f"Failed to update theme: {response.text}")
            return jsonify({"error": response.json()}), response.status_code

    except Exception as e:
        logger.exception(f"Error modifying theme: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


# Endpoint to retrieve logs
@app.route('/logs', methods=['GET'])
def get_logs():
    """
    Retrieve application logs.
    """
    try:
        with open("app.log", "r") as log_file:
            logs = log_file.readlines()
        return jsonify({"logs": logs}), 200
    except FileNotFoundError:
        return jsonify({"error": "No logs found"}), 404
    except Exception as e:
        logger.exception(f"Error retrieving logs: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


# Endpoint to test Shopify API and GPT integration
@app.route('/test-integration', methods=['POST'])
def test_integration():
    """
    Test the Shopify API and GPT integration.
    """
    try:
        # Test Shopify API
        response = requests.get(
            f"{BASE_URL}/themes.json",
            headers={"X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN}
        )
        if response.status_code != 200:
            logger.error("Shopify API test failed")
            return jsonify({"error": "Shopify API test failed"}), response.status_code

        # Test OpenAI API
        gpt_response = openai.Completion.create(
            engine="text-davinci-003",
            prompt="This is a test prompt",
            max_tokens=10
        )
        logger.info("OpenAI API test succeeded")

        return jsonify({"success": "Integration test passed"}), 200
    except Exception as e:
        logger.exception(f"Integration test failed: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
