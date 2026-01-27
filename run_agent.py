#!/usr/bin/env python
"""
Run the Curriculum Mapping AI Agent

Usage:
    python run_agent.py          # Web interface on port 5002
    python run_agent.py cli      # CLI interface
    python run_agent.py --port 5003
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

if __name__ == '__main__':
    from agent.__main__ import main
    main()
