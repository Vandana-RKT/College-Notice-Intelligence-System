import os
import uuid
import json
import secrets
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, send_from_directory, abort
)
from werkzeug.security import check_password_hash
from config import Config
from database import initialize_database, get_db_connection
from services.pdf_extractor import extract_text_from_pdf
from services.llm_service import analyse_notice

app = Flask(__name__)
app.config.from_object(Config)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False  # Set True only when deployed over HTTPS.
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

os.makedirs(os.path.join(app.root_path, "uploads"), exist_ok=True)
initialize_database()


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


def role_required(role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to continue.", "error")
                return redirect(url_for("login"))
            if session.get("role") != role:
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.get("_csrf_token")
        submitted = request.form.get("_csrf_token")
        if not token or not submitted or not secrets.compare_digest(token, submitted):
            abort(400, description="Your form session expired. Refresh the page and try again.")


@app.context_processor
def inject_template_values():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_urlsafe(32)
    return {"csrf_token": session["_csrf_token"]}


def fetch_notice(notice_id):
    conn = get_db_connection()
    try:
        return conn.execute(
            "SELECT * FROM notices WHERE notice_id = ?", (notice_id,)
        ).fetchone()
    finally:
        conn.close()


def parse_details(raw):
    try:
        data = json.loads(raw or "{}")
        return data if isinstance(data, dict) else {}
    except (TypeError, json.JSONDecodeError):
        return {}


@app.route("/")
def home():
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))
    if session.get("role") == "student":
        return redirect(url_for("student_dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("home"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        conn = get_db_connection()
        try:
            user = conn.execute(
                "SELECT * FROM users WHERE email = ?", (email,)
            ).fetchone()
        finally:
            conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["user_id"]
            session["name"] = user["name"]
            session["role"] = user["role"]
            session["_csrf_token"] = secrets.token_urlsafe(32)
            flash("Welcome back!", "success")
            return redirect(url_for("home"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You have logged out.", "success")
    return redirect(url_for("login"))


@app.route("/admin/dashboard")
@login_required
@role_required("admin")
def admin_dashboard():
    conn = get_db_connection()
    try:
        stats = {
            "total": conn.execute("SELECT COUNT(*) FROM notices").fetchone()[0],
            "pending": conn.execute(
                "SELECT COUNT(*) FROM notices WHERE status='pending'"
            ).fetchone()[0],
            "published": conn.execute(
                "SELECT COUNT(*) FROM notices WHERE status='published'"
            ).fetchone()[0],
            "students": conn.execute(
                "SELECT COUNT(*) FROM users WHERE role='student'"
            ).fetchone()[0],
        }
        recent = conn.execute(
            "SELECT notice_id,title,category,status,created_at "
            "FROM notices ORDER BY created_at DESC, notice_id DESC LIMIT 6"
        ).fetchall()
    finally:
        conn.close()
    return render_template("admin_dashboard.html", name=session["name"],
                           stats=stats, recent=recent)


@app.route("/admin/notices")
@login_required
@role_required("admin")
def admin_notices():
    status = request.args.get("status", "all")
    conn = get_db_connection()
    try:
        if status in ("pending", "published"):
            rows = conn.execute(
                "SELECT * FROM notices WHERE status=? "
                "ORDER BY created_at DESC, notice_id DESC", (status,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM notices ORDER BY created_at DESC, notice_id DESC"
            ).fetchall()
    finally:
        conn.close()
    return render_template("admin_notices.html", notices=rows, active_status=status)


@app.route("/admin/review/<int:notice_id>")
@login_required
@role_required("admin")
def review_notice(notice_id):
    notice = fetch_notice(notice_id)
    if not notice:
        abort(404)
    return render_template("notice_details.html", notice=notice,
                           details=parse_details(notice["extracted_details"]),
                           admin_view=True)


@app.route("/admin/publish/<int:notice_id>", methods=["POST"])
@login_required
@role_required("admin")
def publish_notice(notice_id):
    conn = get_db_connection()
    try:
        cur = conn.execute(
            "UPDATE notices SET status='published', published_at=CURRENT_TIMESTAMP "
            "WHERE notice_id=? AND status='pending'", (notice_id,)
        )
        conn.commit()
        if cur.rowcount:
            flash("Notice published. Students can now view it.", "success")
        else:
            flash("Notice was not found or is already published.", "error")
    finally:
        conn.close()
    return redirect(url_for("review_notice", notice_id=notice_id))


@app.route("/admin/keep-pending/<int:notice_id>", methods=["POST"])
@login_required
@role_required("admin")
def keep_pending(notice_id):
    notice = fetch_notice(notice_id)
    if not notice:
        abort(404)
    flash("Notice remains pending and is hidden from students.", "success")
    return redirect(url_for("review_notice", notice_id=notice_id))


@app.route("/admin/upload", methods=["GET", "POST"])
@login_required
@role_required("admin")
def upload_notice():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "General").strip()
        pdf_file = request.files.get("pdf_file")

        if not title or not pdf_file or not pdf_file.filename:
            flash("Enter a title and choose a PDF file.", "error")
            return redirect(url_for("upload_notice"))
        if not pdf_file.filename.lower().endswith(".pdf"):
            flash("Only PDF files are accepted.", "error")
            return redirect(url_for("upload_notice"))
        if pdf_file.stream.read(5) != b"%PDF-":
            flash("The selected file does not appear to be a valid PDF.", "error")
            return redirect(url_for("upload_notice"))
        pdf_file.stream.seek(0)

        filename = f"{uuid.uuid4().hex}.pdf"
        upload_dir = os.path.join(app.root_path, "uploads")
        path = os.path.join(upload_dir, filename)
        conn = None
        try:
            pdf_file.save(path)
            extracted_text = extract_text_from_pdf(path)
            if not extracted_text.strip():
                raise ValueError("No readable text was found in the PDF.")
            ai_details = analyse_notice(extracted_text)
            details_json = json.dumps(ai_details, ensure_ascii=False)
            summary = ai_details.get("summary", "Not available")
            conn = get_db_connection()
            conn.execute(
                """INSERT INTO notices
                (title, category, pdf_filename, extracted_text,
                 extracted_details, summary, status)
                VALUES (?, ?, ?, ?, ?, ?, 'pending')""",
                (title, category, filename, extracted_text, details_json, summary)
            )
            conn.commit()
            flash("PDF analysed successfully and sent for admin review.", "success")
            return redirect(url_for("admin_notices", status="pending"))
        except Exception as exc:
            app.logger.exception("Notice upload failed: %s", exc)
            if os.path.exists(path):
                os.remove(path)
            flash("Upload or AI analysis failed. Check the terminal for details.", "error")
            return redirect(url_for("upload_notice"))
        finally:
            if conn:
                conn.close()
    return render_template("upload.html")


@app.route("/student/dashboard")
@login_required
@role_required("student")
def student_dashboard():
    search = request.args.get("q", "").strip()
    conn = get_db_connection()
    try:
        if search:
            notices = conn.execute(
                """SELECT * FROM notices WHERE status='published'
                AND (title LIKE ? OR category LIKE ? OR summary LIKE ?)
                ORDER BY published_at DESC, notice_id DESC""",
                (f"%{search}%", f"%{search}%", f"%{search}%")
            ).fetchall()
        else:
            notices = conn.execute(
                "SELECT * FROM notices WHERE status='published' "
                "ORDER BY published_at DESC, notice_id DESC"
            ).fetchall()
        total = conn.execute(
            "SELECT COUNT(*) FROM notices WHERE status='published'"
        ).fetchone()[0]
    finally:
        conn.close()
    return render_template("student_dashboard.html", name=session["name"],
                           notices=notices, total=total, search=search)


@app.route("/student/notice/<int:notice_id>")
@login_required
@role_required("student")
def student_notice(notice_id):
    notice = fetch_notice(notice_id)
    if not notice or notice["status"] != "published":
        abort(404)
    details = parse_details(notice["extracted_details"])
    conn = get_db_connection()
    try:
        tasks = conn.execute(
            "SELECT * FROM checklist WHERE student_id=? AND notice_id=? ORDER BY task_id",
            (session["user_id"], notice_id)
        ).fetchall()
    finally:
        conn.close()
    return render_template("notice_details.html", notice=notice,
                           details=details, admin_view=False, tasks=tasks)


@app.route("/student/checklist/add/<int:notice_id>", methods=["POST"])
@login_required
@role_required("student")
def add_checklist_task(notice_id):
    notice = fetch_notice(notice_id)
    if not notice or notice["status"] != "published":
        abort(404)
    task = request.form.get("task_name", "").strip()
    if not task or len(task) > 180:
        flash("Enter a task of up to 180 characters.", "error")
    else:
        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT OR IGNORE INTO checklist (student_id,notice_id,task_name) VALUES (?,?,?)",
                (session["user_id"], notice_id, task)
            )
            conn.commit()
            flash("Checklist task added.", "success")
        finally:
            conn.close()
    return redirect(url_for("student_notice", notice_id=notice_id))


@app.route("/student/checklist/toggle/<int:task_id>", methods=["POST"])
@login_required
@role_required("student")
def toggle_checklist_task(task_id):
    conn = get_db_connection()
    try:
        conn.execute(
            """UPDATE checklist SET is_completed=CASE WHEN is_completed=1 THEN 0 ELSE 1 END
            WHERE task_id=? AND student_id=?""",
            (task_id, session["user_id"])
        )
        conn.commit()
        row = conn.execute(
            "SELECT notice_id FROM checklist WHERE task_id=? AND student_id=?",
            (task_id, session["user_id"])
        ).fetchone()
    finally:
        conn.close()
    if not row:
        abort(404)
    return redirect(url_for("student_notice", notice_id=row["notice_id"]))


@app.route("/student/checklist/delete/<int:task_id>", methods=["POST"])
@login_required
@role_required("student")
def delete_checklist_task(task_id):
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT notice_id FROM checklist WHERE task_id=? AND student_id=?",
            (task_id, session["user_id"])
        ).fetchone()
        if not row:
            abort(404)
        notice_id = row["notice_id"]
        conn.execute(
            "DELETE FROM checklist WHERE task_id=? AND student_id=?",
            (task_id, session["user_id"])
        )
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for("student_notice", notice_id=notice_id))


@app.route("/notice-pdf/<int:notice_id>")
@login_required
def notice_pdf(notice_id):
    notice = fetch_notice(notice_id)
    if not notice:
        abort(404)
    if session.get("role") != "admin" and notice["status"] != "published":
        abort(404)
    return send_from_directory(
        os.path.join(app.root_path, "uploads"),
        notice["pdf_filename"],
        as_attachment=False,
        download_name="college_notice.pdf"
    )


@app.errorhandler(413)
def too_large(_error):
    flash("File is too large. Maximum upload size is 10 MB.", "error")
    return redirect(url_for("upload_notice"))


if __name__ == "__main__":
    app.run(debug=True)
