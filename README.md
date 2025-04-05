# JustLearnIt History

A Flask-based web application for learning history through interactive lessons and tests.

## Features

- Landing page with attractive design
- Interactive lessons
- Practice tests
- Admin dashboard for content management
- Automatic weekly admin credential rotation

## Setup

1. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. Initialize the database and create the admin user:
```bash
python app.py
```

3. Set up the automatic credential rotation:
```bash
chmod +x utils/setup_cron.sh
./utils/setup_cron.sh
```

## Admin Credentials

The admin credentials are stored in the `credentials/admin_credentials.txt` file and are automatically rotated every week. The credentials are:

- Username: Randomly generated in the format `admin_XXXXXXXX`
- Password: Randomly generated string
- Email: Automatically generated based on the username

To view the current admin credentials:
```bash
cat credentials/admin_credentials.txt
```

To manually update the admin credentials:
```bash
python utils/update_credentials.py
```

## Running the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`.

## Project Structure

- `app.py`: Main Flask application
- `templates/`: HTML templates
- `static/`: CSS, JavaScript, and other static files
- `utils/`: Utility scripts for admin credential management
- `credentials/`: Directory for storing admin credentials 