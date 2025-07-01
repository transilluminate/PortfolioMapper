# portfolio_mapper.app.py

# Copyright (c) Adrian Robinson 2025
# This software is dual-licensed under the MIT License (for NHS use only)
# and a Commercial License (for other use).
# For commercial licensing inquiries, please contact adrian.j.robinson@gmail.com

"""
Application launcher script.

This script allows the application to be run as a package, resolving
relative import issues. Run this file with Streamlit from the project root:

streamlit run run_app.py
"""

from src.portfolio_mapper.app import main

if __name__ == "__main__":
    main()

