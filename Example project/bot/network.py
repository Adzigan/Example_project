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
            f"Прокси {proxy} не пускает на Telegram.\n"
            "В VPN-клиенте найдите «Локальный SOCKS/HTTP порт» (не порт подписки).\n"
            "Часто: http://127.0.0.1:7890 или socks5://127.0.0.1:10808\n"
            "Либо включите «Системный прокси» / TUN и уберите BOT_PROXY из .env"
        )

    raise RuntimeError(
        "api.telegram.org недоступен.\n\n"
        "В .env нет рабочего BOT_PROXY (или файл не сохранён — Ctrl+S).\n"
        "1. Включите VPN / прокси-клиент.\n"
        "2. Скопируйте локальный порт из настроек в .env:\n"
        "   BOT_PROXY=http://127.0.0.1:7890\n"
        "3. python -m bot.main"
    )
