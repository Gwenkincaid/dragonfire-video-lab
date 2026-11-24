DRAGONFIRE VIDEO LAB — experimental separate Streamlit app

1. Extract this ZIP. Create a NEW GitHub repository (private recommended).
2. Upload app.py, video_importer.py, workbook_update.py, power_icon.png,
   requirements.txt and packages.txt to its root. Do not upload this ZIP or
   overwrite the files in the existing Fire Gremlins dashboard repository.
3. In share.streamlit.io create a new app from that repository, branch main,
   main file app.py. In Advanced settings > Secrets enter:
   ADMIN_PASSWORD = "choose-your-own-password"
   Deploy. No OpenAI key required. packages.txt installs Tesseract on Linux.
4. Unlock the app. Upload the included progress.xlsx (or the latest compatible
   master workbook). Select Westerlands / FERA, day 6, 50 members, and actual
   capture date/time in UTC. Select Video and upload the FERA recording.
5. Extract, compare row images to the editable table, correct every error,
   verify count, tick confirmation, then Build updated workbook and download.
   Alternatively select Reviewed CSV and use FERA_video_reviewed.csv; verify
   its two uncertain special-character names first.
6. For every subsequent alliance use the MOST RECENT downloaded workbook as
   the input. Export after each alliance. Keep backups. Nothing saves to GitHub
   automatically. Use the replace checkbox only when intentionally replacing
   an entire alliance/day snapshot. Never use it on a partial recording.
7. MOON already has Day 6 power in the starting workbook; keep that historical
   snapshot or intentionally replace it using the reviewed MOON CSV and the
   recording's capture time. Do not treat it as an additional report on Day 6.

LIMITATIONS: This is an import-only test app, not the replacement for the live
analytics dashboard. Existing Overview is historical and not refreshed; the
Alliance Directory totals are updated for imports, and Snapshot Log records
per-alliance UTC timestamps. Membership transfers are deliberately blocked
when a matching player belongs to another alliance; resolve manually after
backing up and design membership history before changing affiliations. Name
matching is exact ignoring case; edit a renamed player's existing row before
importing. OCR can miss or merge players and misread digits or special glyphs.
The prototype is calibrated to landscape member-list recordings of the tested
layout. Record slowly with overlaps; compare expected count and every row.
The included workbook is the existing server tracker, not a newly populated
master. FERA and MOON reviewed CSVs are separate test data. The legacy dashboard
and screenshot importer have not been updated for server-wide comparisons.
Python syntax and workbook update tested locally with both CSVs; Streamlit
cloud deployment and UI not executed in this environment.
