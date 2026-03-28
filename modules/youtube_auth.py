"""
Gerencia autenticação OAuth2 para a YouTube Data API v3.

Na primeira execução abre o browser para autorização.
O token é salvo em auth/token.json e renovado automaticamente.

Como configurar:
1. Acesse console.cloud.google.com
2. Crie um projeto → ative a YouTube Data API v3
3. APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client IDs
4. Tipo: Desktop app
5. Faça download do JSON e salve em auth/client_secrets.json
6. Em OAuth consent screen, adicione sua conta como "Test user"
"""

import json
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from loguru import logger

import config


def get_credentials() -> Credentials:
    """
    Retorna credenciais válidas do YouTube.
    Faz refresh automático se o token estiver expirado.
    Abre o browser para autorização na primeira execução.
    """
    creds = _load_token()

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        logger.info("Token expirado — renovando automaticamente...")
        creds.refresh(Request())
        _save_token(creds)
        logger.success("Token renovado.")
        return creds

    # Primeira vez: fluxo de autorização interativo
    if not config.YOUTUBE_CLIENT_SECRETS_FILE.exists():
        raise FileNotFoundError(
            f"Arquivo de credenciais não encontrado: {config.YOUTUBE_CLIENT_SECRETS_FILE}\n"
            "Consulte as instruções no topo deste arquivo para obter o client_secrets.json."
        )

    logger.info("Iniciando fluxo de autorização OAuth2 (abrindo browser)...")
    flow = InstalledAppFlow.from_client_secrets_file(
        str(config.YOUTUBE_CLIENT_SECRETS_FILE),
        scopes=config.YOUTUBE_SCOPES,
    )
    creds = flow.run_local_server(port=0)
    _save_token(creds)
    logger.success("Autorização concluída e token salvo.")
    return creds


def _load_token() -> Credentials | None:
    if not config.YOUTUBE_TOKEN_FILE.exists():
        return None
    try:
        return Credentials.from_authorized_user_file(
            str(config.YOUTUBE_TOKEN_FILE),
            scopes=config.YOUTUBE_SCOPES,
        )
    except Exception as e:
        logger.warning(f"Falha ao carregar token salvo: {e}")
        return None


def _save_token(creds: Credentials) -> None:
    config.YOUTUBE_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(config.YOUTUBE_TOKEN_FILE, "w") as f:
        f.write(creds.to_json())


if __name__ == "__main__":
    from loguru import logger
    logger.info("Testando autenticação YouTube...")
    creds = get_credentials()
    logger.success(f"Autenticado com sucesso. Token válido: {creds.valid}")
