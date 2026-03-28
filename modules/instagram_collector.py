"""
Coleta vídeos do perfil público @blockchainrio via API interna do Instagram.

Usa requests direto na API mobile do Instagram com cookie sessionid.

Como obter o sessionid correto:
1. Abra o Instagram no Chrome (logado com qualquer conta)
2. F12 → Network → filtre por "web_profile_info"
3. Faça uma busca qualquer no Instagram para gerar requests
4. Ou: Application → Cookies → sessionid (o valor longo alfanumérico)
"""

import time
from pathlib import Path

import requests
from loguru import logger

import config
from modules import metadata_manager

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "X-IG-App-ID": "936619743392459",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.instagram.com/",
    "Origin": "https://www.instagram.com",
}


def _make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(_HEADERS)

    session_id = config.INSTAGRAM_SESSION_ID.strip().strip('"')
    if session_id:
        s.cookies.set("sessionid", session_id, domain=".instagram.com")
        logger.info("Cookie sessionid configurado.")
    else:
        logger.warning("INSTAGRAM_SESSION_ID vazio — tentando sem autenticação.")

    return s


def _get_user_id(session: requests.Session, username: str) -> str | None:
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        user_id = data["data"]["user"]["id"]
        logger.info(f"User ID de @{username}: {user_id}")
        return user_id
    except Exception as e:
        logger.error(f"Falha ao obter user ID de @{username}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Status: {e.response.status_code} | Body: {e.response.text[:300]}")
        return None


def _get_posts(session: requests.Session, user_id: str, max_posts: int = 200) -> list[dict]:
    """Busca posts com paginação até atingir max_posts."""
    all_items: list[dict] = []
    next_max_id: str | None = None
    page = 1

    while len(all_items) < max_posts:
        url = f"https://www.instagram.com/api/v1/feed/user/{user_id}/?count=12"
        if next_max_id:
            url += f"&max_id={next_max_id}"

        try:
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"Falha ao obter posts (página {page}): {e}")
            break

        items = data.get("items", [])
        if not items:
            break

        all_items.extend(items)
        logger.info(f"Página {page}: {len(items)} posts — total acumulado: {len(all_items)}")

        next_max_id = data.get("next_max_id")
        if not next_max_id:
            logger.info("Sem mais páginas — fim do feed.")
            break

        page += 1
        time.sleep(0.5)  # Delay entre páginas para evitar rate limit

    logger.info(f"Total de posts obtidos: {len(all_items)} (em {page} página(s))")
    return all_items[:max_posts]


def _download_file(url: str, dest: Path, session: requests.Session) -> bool:
    try:
        resp = session.get(url, stream=True, timeout=60)
        resp.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
        return True
    except Exception as e:
        logger.error(f"Erro ao baixar arquivo: {e}")
        return False


def _extract_video_url(item: dict) -> str | None:
    """Extrai a URL do vídeo de um item da API."""
    # Post de vídeo simples
    if item.get("media_type") == 2:
        return item.get("video_versions", [{}])[0].get("url")
    # Carrossel — procura vídeo dentro
    if item.get("media_type") == 8:
        for child in item.get("carousel_media", []):
            if child.get("media_type") == 2:
                return child.get("video_versions", [{}])[0].get("url")
    return None


def collect(max_videos: int = config.MAX_COLLECT_PER_RUN) -> list[dict]:
    profile_name = config.TARGET_INSTAGRAM_PROFILE
    session = _make_session()
    downloaded = []

    user_id = _get_user_id(session, profile_name)
    if not user_id:
        return []

    posts = _get_posts(session, user_id, max_posts=200)
    if not posts:
        logger.warning("Nenhum post encontrado.")
        return []

    count_already = 0
    count_not_video = 0
    logger.info(f"{len(posts)} posts encontrados em @{profile_name}")

    for item in posts:
        if len(downloaded) >= max_videos:
            break

        shortcode = item.get("code", "")
        if not shortcode:
            continue

        if metadata_manager.exists(shortcode):
            count_already += 1
            continue

        video_url = _extract_video_url(item)
        if not video_url:
            count_not_video += 1
            continue

        caption = ""
        cap_obj = item.get("caption")
        if cap_obj and isinstance(cap_obj, dict):
            caption = cap_obj.get("text", "")

        taken_at = item.get("taken_at", 0)
        from datetime import datetime, timezone
        instagram_date = datetime.fromtimestamp(taken_at, tz=timezone.utc).isoformat() if taken_at else ""

        post_dir = config.DOWNLOAD_DIR / profile_name / shortcode
        post_dir.mkdir(parents=True, exist_ok=True)
        video_path = post_dir / "video.mp4"

        logger.info(f"Baixando: {shortcode}")
        if not _download_file(video_url, video_path, session):
            continue

        (post_dir / "caption.txt").write_text(caption, encoding="utf-8")

        record = {
            "shortcode": shortcode,
            "filename": str(video_path.relative_to(config.BASE_DIR)),
            "caption": caption,
            "instagram_date": instagram_date,
            "status": "downloaded",
            "youtube_video_id": None,
            "youtube_publish_at": None,
            "uploaded_at": None,
        }

        metadata_manager.add(record)
        downloaded.append(record)
        logger.success(f"Baixado: {shortcode} ({instagram_date[:10]})")
        time.sleep(2)

    logger.info(f"Resultado: {len(downloaded)} baixado(s) | {count_already} já registrado(s) | {count_not_video} não são vídeo (foto/carrossel sem vídeo)")
    logger.info(f"Coleta concluída: {len(downloaded)} vídeo(s) novos.")
    return downloaded
