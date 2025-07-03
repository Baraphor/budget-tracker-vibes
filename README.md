# Expense Tracker - Python Flask App

A simple expense tracking web application built with:

* **Python Flask**
* **Bootstrap** for styling
* **Jinja templating**
* **SQLite** database (local)
* **Docker & Docker Compose** for easy deployment

---

## Features

* Upload, categorize, and search transactions
* Visualize expenses with pie charts and heatmaps
* Set and track budgets by category
* Responsive web interface

---

## Prerequisites

* [Docker](https://www.docker.com/) installed and running
* [Docker Compose](https://docs.docker.com/compose/install/)
* [Git](https://git-scm.com/) to clone the project

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/Baraphor/budget-tracker-vibes.git
cd budget-tracker-vibes
```

### 2. Run the app with Docker Compose

```bash
docker-compose up --build
```

Access the app at: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## Stopping the App

```bash
docker-compose down
```
OR
CRTL+C

---

## Usage

Use the provided sample_transactions.csv to populate data.

---

## Development Notes

* **Backend:** `app.py` (Flask routes), `storage.py` (SQL logic)
* **HTML:** Bootstrap & Jinja in `templates/`
* **Static assets:** JS & CSS in `static/`
* **Database:** Stored inside the Docker container (SQLite)
* **Docker Compose:** Manages app container and future services

---

## Troubleshooting

**Port already in use**
Stop other services on port `5000` or modify the port mapping in `docker-compose.yml`:

```yaml
ports:
  - "8080:5000"
```

**Rebuild containers after code changes**

```bash
docker-compose up --build
```

---

## Notes

* All configurations are handled via Docker Compose
* No `.env` or manual setup required
* Data is persisted in the data/ folder using a Docker volume
