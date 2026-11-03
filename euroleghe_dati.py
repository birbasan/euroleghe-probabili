"""Legge le probabili formazioni Euroleghe da Fantacalcio.it e le trasforma in dati.

Usato da euroleghe.py. Solo libreria standard di Python.
"""
import gzip
import html
import re
import urllib.request

URL = "https://www.fantacalcio.it/probabili-formazioni-euro-leghe"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")

# data-championship-id della pagina -> campionato
CAMPIONATI = {
    "8": "Premier League",
    "21": "Serie A",
    "22": "Bundesliga",
    "23": "LaLiga",
    "24": "Ligue 1",
}

LINK_RE = re.compile(
    r'href="https://www\.fantacalcio\.it/euroleghe/squadre/([^/"]+)/[^/"]+/(\d+)"[^>]*>'
    r'(?:\s*<img[^>]*>)?\s*<span>([^<]+)</span>', re.S)


def scarica(url=URL):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "it-IT,it;q=0.9",
        "Accept-Encoding": "gzip",
    })
    with urllib.request.urlopen(req, timeout=40) as r:
        dati = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            dati = gzip.decompress(dati)
    return dati.decode("utf-8", "ignore")


def pulisci(testo):
    testo = re.sub(r"<br\s*/?>", "\n", testo or "")
    testo = re.sub(r"<[^>]+>", "", testo)
    return re.sub(r"[ \t]+", " ", html.unescape(testo)).strip()


def _sezione(blocco, classe):
    m = re.search(r'<section class="%s">(.*?)</section>' % classe, blocco, re.S)
    return m.group(1) if m else ""


def _lista_con_note(sezione):
    """Giocatori di una sezione (infortunati, squalificati...) con la nota."""
    out = []
    for li in re.findall(r"<li>(.*?)</li>", sezione, re.S):
        m = LINK_RE.search(li)
        if not m:
            continue
        nota = re.search(r'<p class="description">(.*?)</p>', li, re.S)
        out.append({"slug": m.group(1), "id": m.group(2),
                    "nome": pulisci(m.group(3)),
                    "nota": pulisci(nota.group(1)) if nota else ""})
    return out


def analizza(pagina):
    blocchi = re.split(r'(?=<li class="match match-item)', pagina)[1:]
    partite, giocatori, squadre = [], {}, {}

    for b in blocchi:
        b = re.sub(r"<script.*?</script>", "", b, flags=re.S)
        mid = re.search(r'data-match-id="(\d+)"', b).group(1)
        camp = re.search(r'data-championship-id="(\d+)"', b)
        camp = CAMPIONATI.get(camp.group(1) if camp else "", "")
        giornata = re.search(r'<div class="matchweek">\s*(\d+)', b)
        casa = re.search(r'itemprop="homeTeam".*?<meta itemprop="name" content="([^"]+)".*?src="([^"]+)"', b, re.S)
        fuori = re.search(r'itemprop="awayTeam".*?<meta itemprop="name" content="([^"]+)".*?src="([^"]+)"', b, re.S)
        quando = re.search(r'<div class="match-info">\s*<div class="match-date">([^<]*)<', b)
        stadio = re.search(r'<div class="match-stadium">([^<]*)<', b)
        partita = {
            "id": mid,
            "campionato": camp,
            "giornata": giornata.group(1) if giornata else "",
            "casa": html.unescape(casa.group(1)) if casa else "?",
            "casaLogo": casa.group(2) if casa else "",
            "fuori": html.unescape(fuori.group(1)) if fuori else "?",
            "fuoriLogo": fuori.group(2) if fuori else "",
            "quando": pulisci(quando.group(1)) if quando else "",
            "stadio": pulisci(stadio.group(1)) if stadio else "",
            "aggiornato": [pulisci(x) for x in re.findall(r'last-update[^>]*>.*?<span class="date">([^<]+)', b, re.S)],
            "squadre": [],
        }

        # Schede squadra: titolari e panchina con percentuale
        schede = re.findall(r'<div class="card team-card[^"]*">(.*?)(?=<div class="card team-card|<div class="label label-dark last-update|$)', b, re.S)
        for scheda in schede:
            nome_sq = pulisci(re.search(r'<h3 class="h6 team-name">(.*?)</h3>', scheda, re.S).group(1))
            modulo = re.search(r'<div class="h6 team-formation">(.*?)</div>', scheda, re.S)
            casa_sq = nome_sq == partita["casa"]
            avversario = partita["fuori"] if casa_sq else partita["casa"]
            logo = partita["casaLogo"] if casa_sq else partita["fuoriLogo"]
            partita["squadre"].append(nome_sq)
            squadre[nome_sq] = {"nome": nome_sq, "logo": logo, "campionato": camp,
                                "modulo": pulisci(modulo.group(1)) if modulo else "",
                                "commento": "", "partita": mid}
            for gruppo, stato in (("starters", "titolare"), ("reserves", "panchina")):
                lista = re.search(r'<ul class="player-list %s">(.*?)</ul>' % gruppo, scheda, re.S)
                if not lista:
                    continue
                for li in re.findall(r'<li class="player-item[^"]*"(.*?)</li>', lista.group(1), re.S):
                    m = LINK_RE.search(li)
                    if not m:
                        continue
                    ruolo = re.search(r'class="role" data-value="(\w)"', li)
                    perc = re.search(r'aria-valuenow="(\d+)"', li)
                    giocatori[m.group(2)] = {
                        "id": m.group(2), "nome": pulisci(m.group(3)),
                        "slug": m.group(1), "squadra": nome_sq,
                        "ruolo": (ruolo.group(1) if ruolo else "").upper(),
                        "perc": int(perc.group(1)) if perc else None,
                        "stato": stato, "casa": casa_sq, "avversario": avversario,
                        "partita": mid, "avvisi": [], "ballottaggio": None,
                    }

        # Commento della redazione per squadra
        for nome_sq, testo in re.findall(r'<h4 class="h6">([^<]+)</h4>\s*<div class="comment[^"]*">(.*?)</div>', b, re.S):
            nome_sq = pulisci(nome_sq)
            if nome_sq in squadre:
                squadre[nome_sq]["commento"] = pulisci(testo)

        slug_squadra = {g["slug"]: g["squadra"] for g in giocatori.values() if g["partita"] == mid}

        # Ballottaggi
        for ballot in re.findall(r'<ul class="ballot-list">(.*?)</ul>', b, re.S):
            voci = [(m.group(2), pulisci(m.group(3)), int(p))
                    for m, p in zip(LINK_RE.finditer(ballot), re.findall(r'class="percentage">(\d+)%', ballot))]
            for pid, nome, p in voci:
                altri = [{"nome": n, "perc": q} for i2, n, q in voci if i2 != pid]
                if pid in giocatori:
                    giocatori[pid]["ballottaggio"] = {"perc": p, "con": altri}

        # Squalificati, diffidati, infortunati, in dubbio
        for classe, tipo in (("suspendeds", "Squalificato"), ("cautioneds", "Diffidato"),
                             ("injureds", "Infortunato"), ("(?:dubts|doubts)", "In dubbio")):
            for voce in _lista_con_note(_sezione(b, classe)):
                g = giocatori.get(voce["id"])
                if g is None:
                    nome_sq = slug_squadra.get(voce["slug"], "")
                    casa_sq = nome_sq == partita["casa"]
                    g = giocatori[voce["id"]] = {
                        "id": voce["id"], "nome": voce["nome"], "slug": voce["slug"],
                        "squadra": nome_sq, "ruolo": "", "perc": 0, "stato": "fuori",
                        "casa": casa_sq,
                        "avversario": partita["fuori"] if casa_sq else partita["casa"],
                        "partita": mid, "avvisi": [], "ballottaggio": None,
                    }
                g["avvisi"].append({"tipo": tipo, "nota": voce["nota"]})

        partite.append(partita)

    return {"partite": {p["id"]: p for p in partite},
            "squadre": squadre,
            "giocatori": sorted(giocatori.values(), key=lambda g: g["nome"])}


if __name__ == "__main__":
    import json
    import sys
    pagina = open(sys.argv[1], encoding="utf-8").read() if len(sys.argv) > 1 else scarica()
    d = analizza(pagina)
    print(len(d["partite"]), "partite,", len(d["squadre"]), "squadre,", len(d["giocatori"]), "giocatori")
    for nome in ["Courtois", "Gutierrez", "Miranda J.", "Vuskovic", "Emerson P.", "Svensson D.", "Ruben Dias", "Van De Ven"]:
        trovati = [g for g in d["giocatori"] if g["nome"].lower() == nome.lower()]
        print(nome, "->", json.dumps(trovati, ensure_ascii=False)[:400])
