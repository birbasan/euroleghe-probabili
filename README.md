# Probabili Euroleghe

A page for our Euroleghe fantasy league: everyone picks their own team from the league's 8 and sees each player's team, opponent and % chance of starting, plus the suggested lineup by formation.

- Page: https://birbasan.github.io/euroleghe-probabili/
- Probable lineups: the [Euroleghe probable lineups from Fantacalcio.it](https://www.fantacalcio.it/probabili-formazioni-euro-leghe), downloaded by `aggiorna.py` every day at 9:00 and 17:00 Italian time.
- League squads: from the Excel file in the `rose/` folder (team name in row 1, players below until "totale").

## Updating the squads after the transfer market
1. Open the `rose` folder on GitHub.
2. **Add file → Upload files**, drag in the new Excel and press **Commit changes**. You can leave the old one: the page uses the most recent file (the last one in alphabetical order, and Leghe Fantacalcio's filenames include the date).
3. Within a couple of minutes the page shows the new squads.

To refresh the probable lineups right away: Actions tab → "Aggiorna probabili" → Run workflow.
