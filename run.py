#!/usr/bin/env python3
"""Run the Art Studio Companion application."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app import create_app
from app.models import init_db

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    # Initialize the database
    init_db()

    # Get configuration from environment
    debug = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))

    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║           Art Studio Companion                             ║
    ║           Your AI-Powered Art Studio Manager               ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  Server running at: http://{host}:{port}                    ║
    ║  Debug mode: {debug}                                        ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    app.run(host=host, port=port, debug=debug)
