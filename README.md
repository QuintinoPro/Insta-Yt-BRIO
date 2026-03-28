# Insta → YT Pipeline — BlockchainRio

Pipeline de automação que coleta vídeos do Instagram (@blockchainrio) e os agenda automaticamente no YouTube.

## Como funciona

```
Instagram feed (API interna) → download local → YouTube Data API v3 (agendado)
```

1. **Coleta** — busca os últimos posts do perfil Instagram via API interna (sessionid cookie), baixa os vídeos (`.mp4`) e registra metadados localmente
2. **Upload** — envia os vídeos baixados ao YouTube com status `private` + `publishAt` (auto-publicação futura)
3. **Agendamento** — 1 vídeo/dia às 13h UTC, encadeados automaticamente

## Dashboard web

```bash
python server.py
# Acesse: http://localhost:8000
```

Interface com cards de status, botões de ação, log em tempo real (SSE) e tabela de todos os vídeos.

## Uso via terminal

```bash
# Ativar venv
.venv\Scripts\Activate.ps1   # Windows
source .venv/bin/activate    # Linux/Mac

python main.py               # Diagnóstico (o que fazer agora)
python main.py --collect     # Baixa novos vídeos do Instagram (até MAX_COLLECT_PER_RUN)
python main.py --upload      # Sobe para o YouTube (até MAX_UPLOADS_PER_RUN)
python main.py --status      # Resumo rápido
python main.py --report      # Relatório completo + exporta CSV
python main.py --sync-status # Marca como publicados os vídeos cuja data já passou
```

## Setup

### 1. Instalar dependências

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configurar `.env`

```bash
cp .env.example .env
# Edite o .env com suas credenciais
```

### 3. Credenciais do Instagram

1. Abra o Instagram no Chrome (logado com qualquer conta)
2. F12 → Application → Cookies → copie o valor de `sessionid`
3. Cole em `INSTAGRAM_SESSION_ID` no `.env`

### 4. Credenciais do YouTube

1. [Google Cloud Console](https://console.cloud.google.com) → novo projeto
2. Ative a **YouTube Data API v3**
3. Crie credenciais OAuth 2.0 (Desktop app) → baixe o JSON
4. Salve como `auth/client_secrets.json`
5. Autentique uma vez:
   ```bash
   python -m modules.youtube_auth
   ```
   Isso gera `auth/token.json` (salvo para uso futuro)

## Limites importantes

| Recurso | Limite |
|---------|--------|
| YouTube API quota | 10.000 unidades/dia |
| Custo por upload | ~1.600 unidades |
| Uploads/dia recomendado | **máximo 6** |
| Coleta Instagram | sem limite rígido (30/run padrão) |

## Estrutura

```
├── main.py                    # CLI principal
├── server.py                  # Dashboard FastAPI + SSE
├── config.py                  # Configurações via .env
├── requirements.txt
├── .env.example
├── modules/
│   ├── instagram_collector.py # Coleta via API interna Instagram
│   ├── youtube_uploader.py    # Upload + agendamento YouTube
│   ├── youtube_auth.py        # OAuth2 Google
│   ├── metadata_manager.py    # CRUD do videos.json
│   └── reporter.py            # Gera CSV + tabela terminal
├── static/
│   └── index.html             # Dashboard SPA (Tailwind + JS)
├── auth/                      # Credenciais Google (gitignored)
├── downloads/                 # Vídeos baixados (gitignored)
├── metadata/                  # videos.json + report.csv (gitignored)
└── logs/                      # Logs de execução (gitignored)
```

## Variáveis de ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `INSTAGRAM_SESSION_ID` | Cookie sessionid do Instagram | — |
| `TARGET_INSTAGRAM_PROFILE` | Perfil a coletar | `blockchainrio` |
| `YOUTUBE_CLIENT_SECRETS_FILE` | Caminho do client_secrets.json | `auth/client_secrets.json` |
| `MAX_COLLECT_PER_RUN` | Máx. vídeos a baixar por rodada | `30` |
| `MAX_UPLOADS_PER_RUN` | Máx. uploads ao YouTube por rodada | `6` |
| `UPLOAD_HOUR` | Hora de publicação (UTC) | `13` |
