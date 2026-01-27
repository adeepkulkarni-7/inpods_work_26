"""
Main entry point for the agent module.

Usage:
    python -m agent          # Run web interface (default)
    python -m agent web      # Run web interface
    python -m agent cli      # Run CLI interface
"""

import sys
import argparse


def main():
    parser = argparse.ArgumentParser(
        description='Curriculum Mapping AI Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m agent              # Start web interface
    python -m agent web          # Start web interface
    python -m agent cli          # Start CLI interface
    python -m agent web --port 5002
    python -m agent cli --debug
        """
    )

    parser.add_argument(
        'mode',
        nargs='?',
        default='web',
        choices=['web', 'cli'],
        help='Interface mode: web (default) or cli'
    )

    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host for web server (default: 0.0.0.0)'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=5002,
        help='Port for web server (default: 5002)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )

    args = parser.parse_args()

    if args.mode == 'web':
        from .web import run_server
        run_server(host=args.host, port=args.port, debug=args.debug)
    else:
        from .cli import main as cli_main
        cli_main()


if __name__ == '__main__':
    main()
