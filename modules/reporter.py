"""
Gera relatório do pipeline em CSV e exibe tabela no terminal.

CSV salvo em: metadata/report.csv
Atualizado automaticamente após cada comando do main.py.
"""

import csv
from datetime import datetime, timezone

import config
from modules import metadata_manager


def _fmt_date(iso: str | None) -> str:
    if not iso:
        return ""
    return iso[:10]


def _fmt_datetime(iso: str | None) -> str:
    if not iso:
        return ""
    return iso[:16].replace("T", " ")


def _caption_preview(caption: str, max_len: int = 60) -> str:
    text = caption.replace("\n", " ").strip()
    return text[:max_len] + "…" if len(text) > max_len else text


def generate_csv() -> None:
    """Gera/atualiza metadata/report.csv com todos os vídeos."""
    records = metadata_manager.get_all()
    if not records:
        return

    config.REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "shortcode",
        "instagram_date",
        "status",
        "youtube_video_id",
        "youtube_publish_at",
        "uploaded_at",
        "caption_preview",
    ]

    with open(config.REPORT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in sorted(records, key=lambda x: x.get("instagram_date", ""), reverse=True):
            writer.writerow({
                "shortcode": r.get("shortcode", ""),
                "instagram_date": _fmt_date(r.get("instagram_date")),
                "status": r.get("status", ""),
                "youtube_video_id": r.get("youtube_video_id") or "",
                "youtube_publish_at": _fmt_datetime(r.get("youtube_publish_at")),
                "uploaded_at": _fmt_datetime(r.get("uploaded_at")),
                "caption_preview": _caption_preview(r.get("caption", "")),
            })


def print_report() -> None:
    """Exibe relatório completo no terminal."""
    records = metadata_manager.get_all()

    if not records:
        print("Nenhum vídeo registrado ainda.")
        return

    from collections import Counter
    counts = Counter(r["status"] for r in records)

    # ── Cabeçalho ──
    print(f"\n{'═'*70}")
    print(f"  RELATÓRIO DO PIPELINE — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'═'*70}")

    # ── Resumo por status ──
    status_labels = {
        "downloaded": "Baixados (aguardando upload)",
        "scheduled":  "Agendados no YouTube",
        "uploaded":   "Publicados",
        "error":      "Erros",
    }
    print(f"\n  {'STATUS':<30} {'QTD':>5}")
    print(f"  {'─'*35}")
    for status in ["downloaded", "scheduled", "uploaded", "error"]:
        n = counts.get(status, 0)
        if n:
            print(f"  {status_labels[status]:<30} {n:>5}")
    print(f"  {'─'*35}")
    print(f"  {'TOTAL':<30} {len(records):>5}")

    # ── Agendados ──
    scheduled = [r for r in records if r["status"] == "scheduled"]
    if scheduled:
        print(f"\n{'─'*70}")
        print(f"  AGENDADOS NO YOUTUBE ({len(scheduled)} vídeos)")
        print(f"{'─'*70}")
        print(f"  {'SHORTCODE':<15} {'PUBLICA EM (UTC)':<20} {'YOUTUBE ID':<15} {'INSTA DATE'}")
        print(f"  {'─'*65}")
        for r in sorted(scheduled, key=lambda x: x.get("youtube_publish_at", "")):
            print(
                f"  {r['shortcode']:<15} "
                f"{_fmt_datetime(r.get('youtube_publish_at')):<20} "
                f"{r.get('youtube_video_id', ''):<15} "
                f"{_fmt_date(r.get('instagram_date'))}"
            )

    # ── Pendentes de upload ──
    pending = [r for r in records if r["status"] == "downloaded"]
    if pending:
        print(f"\n{'─'*70}")
        print(f"  PENDENTES DE UPLOAD ({len(pending)} vídeos)")
        print(f"{'─'*70}")
        for r in pending:
            print(f"  {r['shortcode']:<15} {_fmt_date(r.get('instagram_date'))}")

    # ── Publicados ──
    uploaded = [r for r in records if r["status"] == "uploaded"]
    if uploaded:
        print(f"\n{'─'*70}")
        print(f"  PUBLICADOS ({len(uploaded)} vídeos)")
        print(f"{'─'*70}")
        for r in sorted(uploaded, key=lambda x: x.get("uploaded_at", ""), reverse=True):
            print(
                f"  {r['shortcode']:<15} "
                f"publicado em {_fmt_date(r.get('uploaded_at'))} | "
                f"YouTube: {r.get('youtube_video_id', '')}"
            )

    print(f"\n{'═'*70}")
    print(f"  CSV salvo em: {config.REPORT_FILE}")
    print(f"{'═'*70}\n")
