#!/usr/bin/env python
"""
Curriculum Mapping Service - Quick Start Runner

Usage:
    python run_integration.py
    python run_integration.py --port 5002
    python run_integration.py --debug
"""

import os
import sys
import argparse


def main():
    parser = argparse.ArgumentParser(description='Run Curriculum Mapping Service')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5001, help='Port to run on')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--env-file', default='.env', help='Path to .env file')

    args = parser.parse_args()

    # Check if .env exists
    if not os.path.exists(args.env_file):
        if os.path.exists('.env.example'):
            print("[WARNING] No .env file found!")
            print("Please create one by copying .env.example:")
            print("  cp .env.example .env")
            print("Then edit .env with your Azure OpenAI credentials.")
            sys.exit(1)
        else:
            print("[ERROR] No .env or .env.example found!")
            sys.exit(1)

    # Set environment variables for config
    os.environ['HOST'] = args.host
    os.environ['PORT'] = str(args.port)
    os.environ['DEBUG'] = str(args.debug).lower()

    # Import and run
    try:
        from integration import create_app, get_config

        config = get_config(args.env_file)
        config.host = args.host
        config.port = args.port
        config.debug = args.debug

        app = create_app(config)
        app.run(
            host=config.host,
            port=config.port,
            debug=config.debug
        )

    except ImportError as e:
        print(f"[ERROR] Failed to import integration package: {e}")
        print("\nMake sure you have installed the requirements:")
        print("  pip install -r requirements.txt")
        sys.exit(1)

    except Exception as e:
        print(f"[ERROR] Failed to start service: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
