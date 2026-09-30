# Local Business Reviews

A small Flask + SQLite web app where people can browse local businesses, add new ones, and post star-rated reviews.

## Features
- Browse businesses ranked by average rating
- Search by name, address or keyword, and filter by category
- Add a new business
- Post reviews with a 1-5 rating
- Sample data is created automatically on first run

## Project structure
```
local-business-reviews/
├── app.py              # Flask app, routes and database code
├── requirements.txt
├── Procfile            # for hosting (gunicorn)
├── templates/          # HTML pages
└── static/style.css    # styling
```

## Run locally
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

The SQLite database (`reviews.db`) is created automatically the first time you run the app.

## Configuration
- `SECRET_KEY` - set this environment variable in production.
- `FLASK_DEBUG=1` - enables debug mode while developing.

## Deploy
Any host that supports Python works (Render, Railway, PythonAnywhere). Start command: `gunicorn app:app`.

## License
MIT
