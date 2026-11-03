"""Scarica le probabili formazioni Euroleghe da Fantacalcio.it e scrive dati.json.

Lo lancia GitHub Actions due volte al giorno (.github/workflows/aggiorna.yml).
Se il download fallisce, dati.json resta quello di prima.
"""
import datetime
import json
import os
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
import euroleghe_dati  # noqa: E402


def adesso():
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("Europe/Rome"))
    except Exception:
        return datetime.datetime.now()


def main():
    dati = euroleghe_dati.analizza(euroleghe_dati.scarica())
    if not dati["giocatori"]:
        sys.exit("La pagina di Fantacalcio.it non contiene giocatori: forse ha cambiato formato.")
    # Tolgo i loghi: la pagina non li usa
    for p in dati["partite"].values():
        p.pop("casaLogo", None)
        p.pop("fuoriLogo", None)
    for s in dati["squadre"].values():
        s.pop("logo", None)
    dati["scaricato"] = adesso().strftime("%d/%m/%Y alle %H:%M")
    dati["fonte"] = euroleghe_dati.URL
    with open(os.path.join(QUI, "dati.json"), "w", encoding="utf-8") as f:
        json.dump(dati, f, ensure_ascii=False, separators=(",", ":"))
    print(f"dati.json scritto: {len(dati['giocatori'])} giocatori, {len(dati['partite'])} partite.")


if __name__ == "__main__":
    main()
