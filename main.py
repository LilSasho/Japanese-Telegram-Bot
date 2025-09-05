#!/usr/bin/env python3
"""
Japanese Learning Telegram Bot - Root Entry Point

This is a convenience entry point that delegates to the main application.
The actual application logic is in app/main.py
"""

if __name__ == "__main__":
    from app.main import main
    import asyncio
    import logging
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Bot stopped by user")
    except Exception as e:
        logging.getLogger(__name__).error(f"Fatal error: {e}")
        import sys
        sys.exit(1)