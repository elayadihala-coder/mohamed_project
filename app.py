from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "change-this-secret-key-in-production"

DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")

# بيانات الأدمن (في مشروع حقيقي يجب تشفير كلمة المرور)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL
        )
    """)
    # إضافة بيانات أولية إذا كانت القاعدة فارغة
    count = conn.execute("SELECT COUNT(*) FROM announcements").fetchone()[0]
    if count == 0:
        conn.execute(
            "INSERT INTO announcements (title, content) VALUES (?, ?)",
            ("مرحباً بكم", "هذا أول إعلان في الموقع. يمكن للأدمن تعديله أو حذفه."),
        )
    conn.commit()
    conn.close()


def is_logged_in():
    return session.get("logged_in", False)


@app.route("/")
def index():
    conn = get_db()
    announcements = conn.execute(
        "SELECT * FROM announcements ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return render_template("index.html", announcements=announcements, logged_in=is_logged_in())


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            flash("تم تسجيل الدخول بنجاح", "success")
            return redirect(url_for("admin"))
        else:
            flash("اسم المستخدم أو كلمة المرور غير صحيحة", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("تم تسجيل الخروج", "success")
    return redirect(url_for("index"))


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not is_logged_in():
        flash("يجب تسجيل الدخول أولاً", "error")
        return redirect(url_for("login"))

    conn = get_db()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "add":
            title = request.form.get("title", "").strip()
            content = request.form.get("content", "").strip()
            if title and content:
                conn.execute(
                    "INSERT INTO announcements (title, content) VALUES (?, ?)",
                    (title, content),
                )
                conn.commit()
                flash("تمت إضافة الإعلان", "success")

        elif action == "edit":
            ann_id = request.form.get("id")
            title = request.form.get("title", "").strip()
            content = request.form.get("content", "").strip()
            if title and content:
                conn.execute(
                    "UPDATE announcements SET title = ?, content = ? WHERE id = ?",
                    (title, content, ann_id),
                )
                conn.commit()
                flash("تم تعديل الإعلان", "success")

        elif action == "delete":
            ann_id = request.form.get("id")
            conn.execute("DELETE FROM announcements WHERE id = ?", (ann_id,))
            conn.commit()
            flash("تم حذف الإعلان", "success")

        conn.close()
        return redirect(url_for("admin"))

    announcements = conn.execute(
        "SELECT * FROM announcements ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return render_template("admin.html", announcements=announcements)


init_db()  # تشغيل قاعدة البيانات عند استيراد الملف (يحتاجه gunicorn)

if __name__ == "__main__":
    app.run(debug=True)
