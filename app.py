from flask import Flask, render_template, request, redirect, session
import mysql.connector
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "12345678"

DB_CONFIG = {
    "host": "192.168.1.150",
    "user": "root",
    "password": "1904",
    "database": "Expense_App",
    "auth_plugin": "mysql_native_password"
}

def get_conn():
    return mysql.connector.connect(**DB_CONFIG)

# ===== REGISTER =====
@app.route("/register", methods=["GET", "POST"])
def register():
    msg = ""
    if request.method == "POST":
        u = request.form["username"]
        e = request.form["email"]
        c = request.form["contact"]
        p = request.form["password"]

        conn = get_conn()
        cur = conn.cursor()

        cur.execute("SELECT id FROM users WHERE username=%s", (u,))
        if cur.fetchone():
            msg = "Username already exists!"
        else:
            cur.execute("""
                INSERT INTO users(username,email,contact_no,password)
                VALUES(%s,%s,%s,%s)
            """, (u,e,c,p))
            conn.commit()
            msg = "Registration Successful!"

        cur.close()
        conn.close()

    return render_template("register.html", message=msg)

# ===== LOGIN =====
@app.route("/", methods=["GET", "POST"])
def login():
    msg = ""
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = get_conn()
        cur = conn.cursor()

        cur.execute("SELECT id FROM users WHERE username=%s AND password=%s", (u,p))
        user = cur.fetchone()

        if user:
            session["user"] = u
            return redirect("/dashboard")
        else:
            msg = "Invalid username or password!"

        cur.close()
        conn.close()

    return render_template("login.html", message=msg)

# ===== DASHBOARD =====
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    conn = get_conn()
    cur = conn.cursor()
    
    # IMPORTANT: fetch all fields in correct order
    cur.execute("""
        SELECT 
            username, date, task_assigned_by, work_assignment, assigned_to_person,
            task_description, work_done_today, task_status, work_plan_next_day,
            expense_purpose, other_purpose, amount
        FROM tasks 
        WHERE username=%s
        ORDER BY date DESC
    """, (session["user"],))

    tasks = cur.fetchall()
    cur.close()
    conn.close()

    total_tasks = len(tasks)
    total_expense = sum([float(t[11]) for t in tasks]) if tasks else 0

    return render_template(
        "dashboard.html",
        tasks=tasks,
        total_tasks=total_tasks,
        total_expense=total_expense,
        username=session["user"]
    )

# ===== ADD TASK =====
@app.route("/add", methods=["GET", "POST"])
def add_task():
    if "user" not in session:
        return redirect("/")

    msg = ""
    if request.method == "POST":
        date = request.form["date"]
        assigned_by = request.form["assigned_by"]
        assignment = request.form["assignment"]
        assigned_to = request.form.get("assigned_to", "")
        desc = request.form["desc"]
        done = request.form["done"]
        status = request.form["status"]
        next_day = request.form["next_day"]

        # MULTI SELECT TAGS
        tags = []
        if "exp_travelling" in request.form: tags.append("travelling")
        if "exp_mobile" in request.form: tags.append("mobile")
        if "exp_food" in request.form: tags.append("food")
        if "exp_other" in request.form: tags.append("other")

        expense_purpose = ", ".join(tags) if tags else "none"

        other_purpose = request.form.get("other_purpose", "")
        amount = request.form["amount"]  # auto total

        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO tasks(
                username, date, task_assigned_by, work_assignment, assigned_to_person,
                task_description, work_done_today, task_status, work_plan_next_day,
                expense_purpose, other_purpose, amount
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            session["user"], date, assigned_by, assignment, assigned_to,
            desc, done, status, next_day, expense_purpose, other_purpose, amount
        ))

        conn.commit()
        cur.close()
        conn.close()

        return redirect("/dashboard")   # ⬅⬅⬅ Redirect after saving

    return render_template("add_task.html", message=msg)

# ===== LOGOUT =====
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
