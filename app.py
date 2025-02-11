# Funkcja do pobierania ID głównego motywu
def get_theme_id():
    """
    Fetch the ID of the main theme from Shopify API.
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

# Funkcja do pobierania zawartości theme.liquid
@app.route('/get-theme', methods=['GET'])
def get_theme():
    """
    Fetch the current content of the theme.liquid file from Shopify.
    """
    try:
        app.logger.info("Fetching theme ID...")
        theme_id = get_theme_id()  # Fetch the ID of the main theme
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
