# Probabili Euroleghe

A page for our Euroleghe fantasy league: everyone enters their own squad (CSV from Leghe Fantacalcio, or the names typed in by hand) and sees each player's team, opponent and % chance of starting, plus the suggested lineup by formation.

- Page: https://birbasan.github.io/euroleghe-probabili/
- Data: the [Euroleghe probable lineups from Fantacalcio.it](https://www.fantacalcio.it/probabili-formazioni-euro-leghe), downloaded by `aggiorna.py`.
- Updates: GitHub Actions runs `aggiorna.py` every day at 9:00 and 17:00 Italian time (`.github/workflows/aggiorna.yml`). To refresh right away: Actions tab → "Aggiorna probabili" → Run workflow.

Each person's squads stay saved only in their own browser.
