from flask import Flask
from dashboard import create_dashboard
from config import CATEGORY_BUDGETS, CATEGORY_COLOR, SECRET_KEY
from auth import setup_auth


def create_app():
    # Create Flask server
    server = Flask(__name__)
    server.secret_key = SECRET_KEY

    # Setup authentication
    setup_auth(server)

    # Create and configure dashboard
    create_dashboard(server, CATEGORY_BUDGETS, CATEGORY_COLOR)

    return server


server = create_app()

if __name__ == "__main__":
    server.run(
        debug=True,
        host="0.0.0.0",
        port=5001,
    )
