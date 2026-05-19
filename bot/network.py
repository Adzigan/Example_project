import aiohttp
from aiohttp_socks import ProxyConnector

TELEGRAM_API = "https://api.telegram.org"


def _session(proxy: str | None) -> aiohttp.ClientSession:
    if proxy and proxy.startswith("socks"):
        connector = ProxyConnector.from_url(proxy)
        return aiohttp.ClientSession(connector=connector)
    return aiohttp.ClientSession()


async def _probe(proxy: str | None) -> bool:
    try:
        async with _session(proxy) as session:
            async with session.get(
                TELEGRAM_API,
                proxy=None if proxy and proxy.startswith("socks") else proxy,
                timeout=aiohttp.ClientTimeout(total=12),
            ) as resp:
                return resp.status < 500
    except Exception:
        return False


async def ensure_telegram_reachable(proxy: str | None) -> None:
    if await _probe(proxy):
        return

    if proxy:
        raise RuntimeError(
            f"Не удаётся достучаться до Telegram через прокси {proxy}. "
            "Проверьте BOT_PROXY и что прокси реально слушает этот адрес."
        )

    raise RuntimeError(
        "Не удаётся подключиться к Telegram API. "
        "Проверьте сеть или задайте рабочий BOT_PROXY в .env."
    )
