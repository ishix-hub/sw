# Dalki child nutrition dashboard

Companion tool for the social work group project "From farm to feeding: household food access, caregiving and young children's dietary diversity, Dalki village, Jhinkpani, West Singhbhum."

## Run locally
    pip install -r requirements.txt
    streamlit run app.py

## Deploy free
Push to GitHub, then connect the repo at share.streamlit.io and select `app.py`.

## Files
- app.py: the dashboard
- menu.csv: transcribed from the menu posted at the centre; food-group tags are the team's reading
- places.csv: study locations (fill in missing coordinates)
- evidence.csv: what evidence each research question rests on

## Data and ethics
- No child names, heights or weights are stored here.
- The recall tool stores nothing server-side. Use pseudonymous codes and consent only.
- The simulator uses placeholder assumptions and does not report findings.

## AI disclosure
Code drafted with AI assistance (Claude) and reviewed by the team.
