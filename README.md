# LifeTwin AI — Complete Major Project Prototype

## What this is
A runnable Flask + SQLite + scikit-learn prototype implementing the Personal Digital Twin concept described in the project specification.

## Quick start
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```
Open `http://127.0.0.1:5000`.

Demo login: `demo` / `demo123`.

## Important
The first launch creates the database and 90 days of synthetic demonstration behavior. The application is designed so the synthetic data can later be replaced with consented real interaction data.

## ML
Random Forest is used for next-task classification and progress estimation; Isolation Forest provides a drift/anomaly signal. NetworkX represents the knowledge graph. The LLM layer is intentionally optional so the core project remains a measurable ML system.

## Future production work
Add secure authentication, encrypted storage, data export/deletion, HTTPS, CSRF protection, stronger validation, a real graph database/vector database, transformer sequence models, calibration, and a privacy-preserving data-collection layer.

## Important Flask configuration

The project keeps `templates/` and `static/` in the project root. `app/__init__.py` explicitly points Flask to those folders. If you move the folders, update `template_folder` and `static_folder` accordingly.

## If you see `jinja2.exceptions.TemplateNotFound`

1. Make sure you start the server from the `LifeTwin_AI` project root.
2. Make sure `templates/login.html` exists.
3. Do not rename the `templates` folder.
4. Run `python run.py` from inside `LifeTwin_AI`.

## Important template configuration

The Flask application is configured explicitly to use the project-level `templates/` and `static/` folders. This prevents `jinja2.exceptions.TemplateNotFound` errors when the application factory lives inside `app/`.

The analytics route passes the drift object as `drift`, matching the variable used by `templates/analytics.html`.

## New user registration

LifeTwin AI now includes a complete account-creation flow at `/register`.
New users can create a unique username and password, are securely password-hashed, automatically signed in after registration, and redirected to their own LifeTwin dashboard. Each account has isolated goals, memories, predictions, feedback, and interaction records.

The dashboard is safe for new accounts with no behavioral history: it shows an early-model state instead of inventing behavioral evidence. As activity is added, the twin can progressively personalize its predictions and analytics.
