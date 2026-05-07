# Renter Browser Clipper

The browser clipper is the fastest safe way to capture rental listings while browsing. It is a bookmarklet that runs only when you click it, packages the current page URL plus selected text, and sends that user-captured payload to the local FastAPI app.

It is not a scraper. It does not crawl listing sites, bypass CAPTCHA, rotate proxies, use hidden automation, fetch protected pages server-side, or claim live Zillow/Redfin/etc. integrations exist.

## Install

1. Start the app with `uv run python -m app.main`.
2. Open `http://127.0.0.1:8000`.
3. Find the `Browser Clipper` panel.
4. Drag the `Clip to Renter` bookmarklet link to your browser bookmarks bar.
5. If dragging is blocked, copy the `Bookmarklet code` textarea and create a new bookmark whose URL is that copied code.

The dashboard generates the bookmarklet from [static/js/bookmarklet.js](static/js/bookmarklet.js), so the bookmarklet code shown in the UI stays aligned with the source file.

## Use

1. Visit a rental listing in your normal browser.
2. Select useful listing text: rent, bedrooms, baths, square footage, address, backyard, garage, parking, pets, laundry, AC, and any notes.
3. Click `Clip to Renter` in the bookmarks bar.
4. Add an optional note when prompted.
5. Return to the dashboard and review the imported listing, score breakdown, source URL, and evidence snippets.

If no text is selected, the bookmarklet captures a limited page-text fallback from the visible document text. Selecting text is preferred because it gives cleaner evidence and avoids storing irrelevant page content.

## Captured Data

The clip payload contains:

- `source_url`: current page URL
- `page_title`: browser document title
- `selected_text`: highlighted text, when present
- `page_text`: limited visible text fallback when no selection exists
- `source_domain`: current hostname
- `user_notes`: optional note entered by the user
- `captured_at`: timestamp from the browser

The server sanitizes clipped text and stores it as plain text. The frontend renders clipped text with HTML escaping.

## Direct Import vs Fallback

The bookmarklet first attempts:

```text
POST http://127.0.0.1:8000/api/import/clip
```

Some sites or browsers can still block direct cross-origin requests. When that happens, the bookmarklet copies structured JSON to your clipboard and opens:

```text
http://127.0.0.1:8000/#browser-clip=<encoded payload>
```

The dashboard reads that hash, fills the fallback textarea, and lets you click `Import Browser Clip`. If opening the app is blocked, paste the copied JSON into the `Fallback clipped JSON` box manually.

## Parsing and Scoring

Browser clips use the same deterministic parser as paste import. When present, the parser extracts:

- monthly price
- bedrooms
- bathrooms
- square feet
- address
- city
- state
- ZIP
- backyard status and evidence
- garage status and evidence
- parking details
- pet policy
- laundry
- air conditioning

Ambiguous or missing evidence stays `unknown` and creates needs-review prompts. A clip should never be treated as authoritative until backyard and garage evidence is checked against the source page.

## Duplicate Behavior

- Exact source URL match updates the existing listing instead of creating a duplicate.
- Older notes and decision workflow state are preserved on exact URL updates.
- Possible matches by normalized address or title plus city plus price are still imported, but marked `needs_review` with a warning.

## Troubleshooting

### The bookmarklet says the direct import failed

Use the fallback JSON flow. This is expected on some sites because browser security controls cross-origin requests from bookmarklets.

### The fallback textarea is empty

Check your clipboard. The bookmarklet copies the JSON payload before opening the dashboard fallback URL.

### The parser missed a field

Select a cleaner block of listing text and clip again, or use paste/manual import. The parser is conservative and preserves raw evidence for review.

### The listing imported with `needs_review`

That usually means price, bed, bath, backyard, garage, or duplicate signals need manual verification.

### The app is not reachable

Start it locally:

```bash
uv run python -m app.main
```

Then open `http://127.0.0.1:8000`.

## Security Notes

- The server does not fetch the listing URL.
- Clipped HTML/script is stripped and stored as text.
- Payload sizes are limited.
- The feature is designed for local use on `127.0.0.1:8000`.
- Do not add background scraping, CAPTCHA bypass, stealth automation, or proxy evasion to this workflow.
