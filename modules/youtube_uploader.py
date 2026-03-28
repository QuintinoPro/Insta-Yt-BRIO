"""
Upload de vídeos para o YouTube com agendamento via YouTube Data API v3.

O vídeo é enviado imediatamente mas fica privado com publishAt no futuro.
O YouTube publica automaticamente na data/hora agendada.

Limitações de quota:
- 10.000 unidades/dia (cota padrão do Google Cloud)
- Cada upload consome ~1.600 unidades → máximo ~6 uploads/dia
"""

from datetime import timezone
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from loguru import logger

import config
from modules import metadata_manager
from modules.youtube_auth import get_credentials


_YOUTUBE_API_SERVICE = "youtube"
_YOUTUBE_API_VERSION = "v3"
_MAX_TITLE_LEN = 100


def _build_client():
    creds = get_credentials()
    return build(_YOUTUBE_API_SERVICE, _YOUTUBE_API_VERSION, credentials=creds)


def _make_title(record: dict) -> str:
    """Gera título a partir da caption ou da data do post."""
    caption = record.get("caption", "").strip()
    if caption:
        # Primeira linha da caption, sem hashtags, truncado
        first_line = caption.split("\n")[0]
        title = " ".join(w for w in first_line.split() if not w.startswith("#"))
        title = title[:_MAX_TITLE_LEN].strip()
        if title:
            return title

    # Fallback: usa a data do post
    date_str = record.get("instagram_date", "")[:10]  # YYYY-MM-DD
    return f"BlockchainRio – {date_str}"


def upload_one(record: dict) -> bool:
    """
    Faz upload de um vídeo e o agenda no YouTube.
    Atualiza o metadata_manager com o resultado.
    Retorna True em caso de sucesso.
    """
    shortcode = record["shortcode"]
    video_path = Path(record["filename"])

    if not video_path.is_absolute():
        video_path = config.BASE_DIR / video_path if hasattr(config, "BASE_DIR") else Path(record["filename"])

    # Tenta caminho relativo ao diretório de downloads
    if not video_path.exists():
        video_path = config.DOWNLOAD_DIR.parent / record["filename"]

    if not video_path.exists():
        logger.error(f"Arquivo não encontrado: {record['filename']}")
        metadata_manager.update_status(shortcode, "error")
        return False

    # Calcula o slot de publicação
    scheduled = metadata_manager.get_scheduled()
    publish_at = metadata_manager.next_publish_slot(scheduled)
    publish_at_iso = publish_at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    title = _make_title(record)
    description = record.get("caption", "")

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": "25",  # News & Politics (ajuste conforme necessário)
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": publish_at_iso,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
        chunksize=8 * 1024 * 1024,  # 8 MB chunks
    )

    logger.info(f"Iniciando upload: {shortcode} → agendado para {publish_at_iso}")

    try:
        youtube = _build_client()
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                logger.debug(f"Upload {shortcode}: {pct}%")

        video_id = response["id"]
        metadata_manager.update_status(
            shortcode,
            status="scheduled",
            youtube_video_id=video_id,
            youtube_publish_at=publish_at_iso,
        )
        logger.success(
            f"Upload concluído: {shortcode} → YouTube ID {video_id} | publicação: {publish_at_iso}"
        )
        return True

    except Exception as e:
        logger.error(f"Erro no upload de {shortcode}: {e}")
        metadata_manager.update_status(shortcode, "error")
        return False


def upload_queue(max_uploads: int = 6) -> tuple[int, int]:
    """
    Processa até `max_uploads` vídeos com status 'downloaded'.
    Retorna (sucessos, falhas).
    """
    pending = metadata_manager.get_pending_upload()

    if not pending:
        logger.info("Nenhum vídeo pendente para upload.")
        return 0, 0

    batch = pending[:max_uploads]
    remaining = len(pending) - len(batch)
    logger.info(f"{len(pending)} vídeo(s) na fila — processando {len(batch)} agora (limite: {max_uploads}).")
    if remaining > 0:
        logger.info(f"{remaining} vídeo(s) ficarão para a próxima rodada.")

    success, failed = 0, 0

    for record in batch:
        if upload_one(record):
            success += 1
        else:
            failed += 1

    return success, failed
