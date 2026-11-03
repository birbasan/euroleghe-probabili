"""Scarica le probabili formazioni Euroleghe da Fantacalcio.it e scrive dati.json.
Legge anche le rose della lega dall'Excel nella cartella rose/ e scrive squadre.json.

Lo lancia GitHub Actions due volte al giorno e quando si carica un nuovo Excel
(.github/workflows/aggiorna.yml). Se il download fallisce, dati.json resta quello di prima.
"""
import datetime
import json
import os
import sys
import xml.etree.ElementTree as ET
import zipfile

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
import euroleghe_dati  # noqa: E402

CARTELLA_ROSE = os.path.join(QUI, "rose")
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def adesso():
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("Europe/Rome"))
    except Exception:
        return datetime.datetime.now()


def _celle_xlsx(percorso):
    """Prima scheda dell'Excel come {(riga, colonna): testo}. Solo libreria standard."""
    z = zipfile.ZipFile(percorso)
    condivise = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(NS + "si"):
            condivise.append("".join(t.text or "" for t in si.iter(NS + "t")))
    fogli = sorted(n for n in z.namelist() if n.startswith("xl/worksheets/sheet"))
    celle = {}
    for c in ET.fromstring(z.read(fogli[0])).iter(NS + "c"):
        rif = c.get("r")
        lettere = "".join(ch for ch in rif if ch.isalpha())
        col = 0
        for ch in lettere:
            col = col * 26 + ord(ch.upper()) - 64
        riga = int(rif[len(lettere):])
        v = c.find(NS + "v")
        if c.get("t") == "s" and v is not None:
            testo = condivise[int(v.text)]
        elif c.get("t") == "inlineStr":
            testo = "".join(t.text or "" for t in c.iter(NS + "t"))
        else:
            testo = v.text if v is not None else ""
        celle[(riga, col)] = (testo or "").strip()
    return celle


def ruolo_da_riga(riga):
    # Nell'Excel della lega: righe 2-4 portieri, 5-12 difensori, 13-20 centrocampisti, poi attaccanti
    return "P" if riga <= 4 else "D" if riga <= 12 else "C" if riga <= 20 else "A"


def leggi_rose():
    """Rose della lega dall'ultimo Excel in rose/. Ogni squadra: nome in riga 1, giocatori sotto, fino a "totale"."""
    if not os.path.isdir(CARTELLA_ROSE):
        return []
    excel = sorted(f for f in os.listdir(CARTELLA_ROSE) if f.lower().endswith(".xlsx") and not f.startswith("~$"))
    if not excel:
        return []
    celle = _celle_xlsx(os.path.join(CARTELLA_ROSE, excel[-1]))
    squadre = []
    for (riga, col), testo in sorted(celle.items(), key=lambda x: x[0][1]):
        if riga != 1 or not testo or testo.lower() == "costo":
            continue
        rosa = []
        r = 2
        while True:
            nome = celle.get((r, col), "")
            if not nome or nome.lower().startswith("totale"):
                break
            rosa.append({"nome": nome, "ruolo": ruolo_da_riga(r)})
            r += 1
        if rosa:
            slug = "".join(ch if ch.isalnum() else "-" for ch in testo.lower()).strip("-")
            squadre.append({"id": slug, "nome": testo, "rosa": rosa})
    return squadre


def main():
    squadre = leggi_rose()
    if squadre:
        with open(os.path.join(QUI, "squadre.json"), "w", encoding="utf-8") as f:
            json.dump({"squadre": squadre}, f, ensure_ascii=False, indent=1)
        print(f"squadre.json scritto: {len(squadre)} squadre.")

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
