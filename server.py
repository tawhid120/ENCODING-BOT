import logging
import os
import asyncio
from collections import deque
from html import escape

import dns.resolver
from aiohttp import web
from pyrogram import idle

from VideoEncoder import app, log

# ---------------------------------------------------------------------------
# In-memory log handler
# ---------------------------------------------------------------------------
MAX_LOG_LINES = 500
log_buffer: deque[str] = deque(maxlen=MAX_LOG_LINES)

class WebLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            log_buffer.append(self.format(record))
        except Exception:
            self.handleError(record)

_handler = WebLogHandler()
_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                      datefmt="%d-%b-%y %H:%M:%S")
)
logging.getLogger().addHandler(_handler)

LOGGER = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Simple aiohttp web application
# ---------------------------------------------------------------------------
HTML_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Encoding Bot – Live Logs</title>
  <meta http-equiv="refresh" content="10">
  <style>
    body {{
      background: #1e1e2e; color: #cdd6f4; font-family: monospace;
      padding: 1rem; margin: 0;
    }}
    h1 {{ color: #89b4fa; }}
    pre {{
      background: #11111b; padding: 1rem; border-radius: 8px;
      overflow-x: auto; white-space: pre-wrap; word-break: break-all;
      max-height: 85vh; overflow-y: auto;
    }}
  </style>
</head>
<body>
  <h1>&#128225; Encoding Bot – Live Logs</h1>
  <p>Showing last {max_lines} log lines (auto-refreshes every 10 s)</p>
  <pre>{logs}</pre>
</body>
</html>
"""

async def handle_index(request: web.Request) -> web.Response:
    logs_text = "\n".join(escape(line) for line in log_buffer) or "No logs yet …"
    html = HTML_TEMPLATE.format(max_lines=MAX_LOG_LINES, logs=logs_text)
    return web.Response(text=html, content_type="text/html")

async def handle_health(request: web.Request) -> web.Response:
    return web.Response(text="OK")

def create_web_app() -> web.Application:
    webapp = web.Application()
    webapp.router.add_get("/", handle_index)
    webapp.router.add_get("/health", handle_health)
    return webapp

# ---------------------------------------------------------------------------
# Main entry-point (Runs both Bot & Web Server safely)
# ---------------------------------------------------------------------------
async def main() -> None:
    # 1. DNS setup
    dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
    dns.resolver.default_resolver.nameservers = ["8.8.8.8"]

    # 2. Start Bot
    await app.start()
    LOGGER.info("Bot started! @%s", (await app.get_me()).username)
    await app.send_message(
        chat_id=log,
        text=f"<b>Bot Started! @{(await app.get_me()).username}</b>",
    )

    # 3. Start Web Server
    port = int(os.environ.get("PORT", 8080))
    webapp = create_web_app()
    runner = web.AppRunner(webapp)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    LOGGER.info("Starting web server on port %s …", port)

    # 4. Keep running and listen for Telegram messages
    await idle()

    # 5. Shutdown gracefully
    LOGGER.info("Shutting down...")
    await app.stop()
    await runner.cleanup()

if __name__ == "__main__":
    # pyrogram এর নিজস্ব loop ব্যবহার করে মূল ফাংশনটি রান করানো হচ্ছে
    app.loop.run_until_complete(main())
