import csv
import io
import json
import os
import re
from datetime import datetime
from functools import wraps
from threading import Lock

from flask import (
    Flask, Response, flash, redirect,
    render_template, request, session, url_for
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "campusloop-demo-secret")

DATA_FILE = "registrations.json"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
file_lock = Lock()

SOURCES = {
    "whatsapp", "club", "referral",
    "email", "social", "other"
}


def read_registrations():
    with file_lock:
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []


def save_registrations(data):
    with file_lock:
        temp_file = DATA_FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, DATA_FILE)


def clean(value, limit=120):
    return (value or "").strip()[:limit]


def admin_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("login"))
        return function(*args, **kwargs)
    return wrapper


@app.route("/")
def index():
    referral_code = clean(request.args.get("ref"), 32).upper()
    source = clean(request.args.get("source"), 32).lower()
    if source not in SOURCES:
        source = "referral" if referral_code else "other"
    return render_template(
        "index.html",
        referral_code=referral_code,
        source=source
    )


@app.route("/register", methods=["POST"])
def register():
    name = clean(request.form.get("name"), 80)
    email = clean(request.form.get("email"), 160).lower()
    college = clean(request.form.get("college"), 120)
    year_text = clean(request.form.get("graduation_year"), 4)
    interest = clean(request.form.get("interest"), 60)
    source = clean(request.form.get("source"), 32).lower()
    referral_code = clean(
        request.form.get("referral_code"), 32
    ).upper()

    if source not in SOURCES:
        source = "other"

    if not name or not college:
        flash("Please fill in all required fields.", "error")
        return redirect(url_for("index"))

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        flash("Please enter a valid email address.", "error")
        return redirect(url_for("index"))

    try:
        year = int(year_text)
    except ValueError:
        year = 0

    current_year = datetime.now().year
    if not current_year <= year <= current_year + 6:
        flash("Please select a valid graduation year.", "error")
        return redirect(url_for("index"))

    valid_interests = {
        "AI/ML",
        "Software Development",
        "Data Analytics",
        "Other"
    }
    if interest not in valid_interests:
        interest = "Other"

    registrations = read_registrations()
    if any(r.get("email") == email for r in registrations):
        flash("This email is already registered.", "error")
        return redirect(url_for("index"))

    registration = {
        "id": len(registrations) + 1,
        "name": name,
        "email": email,
        "college": college,
        "graduation_year": year,
        "interest": interest,
        "source": source,
        "referral_code": referral_code,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    registrations.append(registration)
    save_registrations(registrations)

    return render_template("success.html", name=name)


@app.route("/admin/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("dashboard"))
        flash("Incorrect password.", "error")
    return render_template("login.html")


@app.route("/admin/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/admin")
@admin_required
def dashboard():
    registrations = read_registrations()
    source_counts = {}
    referral_counts = {}
    for registration in registrations:
        source = registration.get("source", "other")
        code = registration.get("referral_code") or "(no code)"
        source_counts[source] = source_counts.get(source, 0) + 1
        referral_counts[code] = referral_counts.get(code, 0) + 1

    registrations = list(reversed(registrations))
    return render_template(
        "admin.html",
        registrations=registrations[:25],
        total=len(registrations),
        target=500,
        remaining=max(0, 500 - len(registrations)),
        progress=min(100, round(len(registrations) / 500 * 100, 1)),
        source_counts=source_counts,
        referral_counts=referral_counts
    )


@app.route("/admin/export.csv")
@admin_required
def export_csv():
    registrations = read_registrations()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Name", "Email", "College", "Graduation Year",
        "Interest", "Source", "Referral Code", "Registered At"
    ])
    for r in registrations:
        writer.writerow([
            r.get("name", ""),
            r.get("email", ""),
            r.get("college", ""),
            r.get("graduation_year", ""),
            r.get("interest", ""),
            r.get("source", ""),
            r.get("referral_code", ""),
            r.get("created_at", "")
        ])
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=campusloop_registrations.csv"
        }
    )


if __name__ == "__main__":
    app.run(debug=True)