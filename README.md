# Marketeye

Crypto market screener and (eventually) signal service. **Phase 1**: altcoin screener vs BTC + BTC dominance data, using the [LiveCoinWatch API](https://livecoinwatch.github.io/lcw-api-docs/).

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env   # then put your key in LCW_API_KEY
python main.py      # CLI: print tables + save CSV
python app.py       # Web UI at http://127.0.0.1:8000
```

## Web UI
- **Refresh data** fetches the market (~3 credits) and saves a CSV to `output/`.
- **Screen settings** (volume floor, long/short ranges) are saved to `config.yaml` with comments preserved, and re-screen the last fetch for free. Lowering the volume floor below the last fetch shows a hint to refresh.
- Charts: coins by 24h % vs BTC (dot size = volume) and 30-day BTC dominance. Tables sort by any column.
- Runs on localhost only; the API key never leaves the server.

## Layout
| File | Purpose |
|---|---|
| `config.yaml` | Volume threshold, long/short % ranges (placeholders), exclusions, API limits |
| `config.py` | Loads `config.yaml` and the API key from `.env` |
| `clients/livecoinwatch.py` | API wrapper: errors, timeouts, call counter, volume-aware pagination |
| `screener.py` | Volume filter, delta → %, bucketing into long / short / outliers |
| `dominance.py` | Current BTC dominance + N-day history |
| `regime.py` | Stub: 6-regime → action mapping; classification rules TBD |
| `pipeline.py` | One screening run, shared by the CLI and the web app; CSV export |
| `main.py` | CLI: prints tables, writes `output/screen_<UTC timestamp>.csv` |
| `app.py` + `web/index.html` | Flask server and single-page UI |
| `report/` | Template for the shareable Phase 1 report |

## Credits
Each API request costs 1 credit (daily allowance, resets 00:00 UTC). A run uses ~1–3 `coins/list` pages (stops once volume falls below the threshold) + 2 dominance calls.

## Later phases (not built)
Regime rules, chart triggers, Telegram/Gmail notifications, signal storage/dedup, scheduling, Docker.

## Live site (GitHub Pages)
`.github/workflows/site.yml` runs every 30 minutes (and on every push to `main`, or by hand from the Actions tab):
it runs `export_site.py`, which fetches fresh data (~3 credits, ~150/day) and publishes `web/index.html` + `data.json` to GitHub Pages.

- The page detects it is static: no Refresh button, and settings are saved in the visitor's browser only. Defaults come from `config.yaml` in the repo.
- Setup: add the repository secret `LCW_API_KEY`, and set Settings → Pages → Source to "GitHub Actions".
- GitHub pauses scheduled workflows after 60 days without repository activity; it emails you first, and one click re-enables them.
