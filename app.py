from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pandas as pd
import os
import random
import qrcode
import csv
import time
from sklearn.linear_model import LinearRegression
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import numpy as np
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from flask import send_file

app = Flask(__name__)
app.secret_key = "ghmc_secret_key"

otp_storage = {}
complaints = []

# ---------------- PATH SETTINGS ---------------- #

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATASET = os.path.join(BASE_DIR, "dataset")
DATA_FOLDER = os.path.join(BASE_DIR, "data")
QR_FOLDER = os.path.join("static", "qr_codes")
users_file = os.path.join(BASE_DIR, "data", "users.csv")
file_path = os.path.join(BASE_DIR, "data", "bins.csv")
alert_file = os.path.join("data", "alerts.csv")

os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)
os.makedirs("data", exist_ok=True)

COMPLAINT_FILE = os.path.join(DATASET, "complaints.csv")
DATASET_FILE = os.path.join(BASE_DIR, "dataset", "waste_main_dataset_2024_2026.csv")
BLOCKCHAIN_FILE = os.path.join(BASE_DIR, "dataset", "blockchain_ledger_dataset.csv")
ROUTE_FILE = os.path.join(BASE_DIR, "dataset", "route_optimization_logs.csv")
VEHICLE_FILE = os.path.join(BASE_DIR, "dataset", "vehicle_tracking_dataset.csv")
file_path = os.path.join(BASE_DIR, "dataset", "waste_collection_daily.csv")
BIN_FILE = os.path.join(DATA_FOLDER, "qr_bins_master.csv")
LOG_FILE = os.path.join(DATA_FOLDER, "collection_logs.csv")
IMAGE_FOLDER = os.path.join(BASE_DIR, "images")

def send_email_alert(bin_id, status, name, priority):
    print("📧 Email Alert Sent!")
    print("Bin ID:", bin_id)
    print("Status:", status)
    print("Name:", name)
    print("Priority:", priority)
    print()

if not os.path.exists(COMPLAINT_FILE):
    df = pd.DataFrame(columns=[
        "complaint_id",
        "area",
        "issue",
        "priority",
        "status",
        "date"
    ])
    df.to_csv(COMPLAINT_FILE, index=False)

THRESHOLD_FULL = 75
THRESHOLD_OVERFLOW = 90

def check_threshold(fill_percent):

    if fill_percent >= THRESHOLD_OVERFLOW:
        return "OVERFLOW", "Critical Overflow - Immediate Action Required"

    elif fill_percent >= THRESHOLD_FULL:
        return "FULL", "Collection Required Soon"

    else:
        return "NORMAL", "Operating Normally"


import smtplib
from email.mime.text import MIMEText

def send_email_alert(bin_id, status, name, priority):

    sender = "pushyasaini5@gmail.com"
    password = "egyvzwllyrsckojt"
    receiver = "pushyasaini58@gmail.com"

    subject = f"🚨 Waste Alert - {bin_id}"

    body = f"""
Bin ID: {bin_id}
Status: {status}
Reported By: {name}
Priority: {priority}
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender, password)
    server.sendmail(sender, receiver, msg.as_string())
    server.quit()

    print("✅ Real Email Sent!")
    
# ==========================
# HOME PAGE
# ==========================

@app.route("/")
def home():
    return render_template("home.html")


# ==========================
# CITIZEN LOGIN
# ==========================

from werkzeug.security import check_password_hash
import pandas as pd
import os

@app.route("/citizen_login", methods=["GET", "POST"])
def citizen_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        # ✅ Correct file path
        users_file = os.path.join(BASE_DIR, "data", "users.csv")

        # Check file exists
        if not os.path.exists(users_file):
            return "No users found. Please signup first."

        # Read CSV
        df = pd.read_csv(users_file)

        # Find user
        user = df[df["username"] == username]

        if user.empty:
            return "Invalid Username ❌"

        # ✅ IMPORTANT FIX
        stored_password = str(user.iloc[0]["password"])

        # ✅ Password check
        if check_password_hash(stored_password, password):
            session["role"] = user.iloc[0]["role"]
            session["username"] = username
            return redirect("/citizen_dashboard")
        else:
            return "Invalid Password ❌"
        
    print("Reading from:", "USERS_FILE")
   

    return render_template("citizen_login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        users_file = os.path.join(BASE_DIR, "data", "users.csv")

        # Create file if not exists
        if not os.path.exists(users_file):
            os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
            with open(users_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["username", "password", "role"])

        # 🔐 Hash password
        hashed_password = generate_password_hash(password)

        # Save user
        with open(users_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([username, hashed_password, "citizen"])

        return "Signup Successful ✅ Go to Login"

    return render_template("signup.html")

@app.route("/admin_users")
def admin_users():

    if session.get("role") != "admin":
        return redirect("/")

    df = pd.read_csv("users.csv")

    users = df.to_dict(orient="records")

    return render_template("admin_users.html", users=users)

@app.route("/delete_user/<username>")
def delete_user(username):

    df = pd.read_csv("users.csv")

    df = df[df["username"] != username]

    df.to_csv("users.csv", index=False)

    return redirect("/admin_users")

# ==========================
# ADMIN LOGIN
# ==========================

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "1234":
            session["role"] = "admin"
            return redirect("/admin_dashboard")
    return render_template("admin_login.html")

@app.route("/send_otp", methods=["POST"])
def send_otp():

    mobile = request.form["mobile"]

    otp = str(random.randint(100000, 999999))
    otp_storage[mobile] = otp

    print(f"OTP for {mobile}: {otp}")

    return render_template("verify_otp.html", mobile=mobile)

@app.route("/verify_otp", methods=["POST"])
def verify_otp():

    mobile = request.form["mobile"]
    user_otp = request.form["otp"]

    if otp_storage.get(mobile) == user_otp:
        session["role"] = "citizen"
        return redirect("/citizen_dashboard")
    else:
        return "<h3>❌ Invalid OTP</h3>"
    
# ==========================
# CITIZEN DASHBOARD
# ==========================

@app.route("/citizen_dashboard")
def citizen_dashboard():

    if "username" not in session:
        return redirect("/public_login")

    username = session["username"]

    # Load complaints
    if os.path.exists(COMPLAINT_FILE):
        df = pd.read_csv(COMPLAINT_FILE)
    else:
        df = pd.DataFrame()

    # Filter only this user's complaints (optional)
    user_df = df[df["area"].notna()] if not df.empty else df

    total = len(user_df)
    resolved = len(user_df[user_df["status"] == "Resolved"])
    pending = len(user_df[user_df["status"] == "Pending"])

    # Recent complaints
    recent = user_df.tail(5).to_dict(orient="records") if not df.empty else []

    return render_template(
        "citizen_dashboard.html",
        username=username,
        total=total,
        resolved=resolved,
        pending=pending,
        recent=recent
    )
    
@app.route("/scan_qr", methods=["GET", "POST"])
def scan_qr():
    data = request.get_json(silent=True)
    if data:
       bin_id = data.get("bin_id")
    else:
        bin_id = None
    return render_template("scan_qr.html")       
    

# ==========================
# ADMIN DASHBOARD
# ==========================

@app.route("/admin_dashboard")
def admin_dashboard():

    if session.get("role") != "admin":
        return redirect("/")

    # ===============================
    # Waste Data
    # ===============================
    waste_df = pd.read_csv(DATASET_FILE)
    route_df = pd.read_csv(ROUTE_FILE)

    waste_df["fill_level"] = pd.to_numeric(waste_df["fill_level"], errors="coerce")

    total_bins = waste_df["bin_id"].nunique()
    high_alerts = waste_df[waste_df["fill_level"] >= 80].shape[0]

    area_avg = (
        waste_df.groupby("area")["fill_level"]
        .mean()
        .round(2)
        .to_dict()
    )

    route_efficiency = {}
    if "route_efficiency_score" in route_df.columns:
        route_efficiency = (
            route_df.groupby("route_efficiency_score")["route_efficiency_score"]
            .mean()
            .round(2)
            .to_dict()
        )

    # ===============================
    # Complaint Data
    # ===============================
    complaint_df = pd.read_csv(COMPLAINT_FILE)

    total_complaints = len(complaint_df)

    high = len(complaint_df[complaint_df["priority"] == "High"])
    medium = len(complaint_df[complaint_df["priority"] == "Medium"])
    low = len(complaint_df[complaint_df["priority"] == "Low"])

    resolved = len(complaint_df[complaint_df["status"] == "Resolved"])
    pending = len(complaint_df[complaint_df["status"] == "Pending"])
    complaints = complaint_df.to_dict(orient="records")

    # ===============================
    # Render Dashboard
    # ===============================
    return render_template(
    "admin_dashboard.html",
      
    total_bins=total_bins,
    high_alerts=high_alerts,
    area_avg=area_avg,
    route_efficiency=route_efficiency,

    total=total_complaints,
    high=high,
    medium=medium,
    low=low,
    resolved=resolved,
    pending=pending,

    complaints=complaints
)
       
@app.route("/complaint_status")
def complaint_status():
    if session.get("role") != "citizen":
        return redirect("/")

    if os.path.exists(COMPLAINT_FILE):
        df = pd.read_csv(COMPLAINT_FILE)
        complaints = df.to_dict(orient="records")
    else:
        complaints = []

    return render_template("complaint_status.html", complaints=complaints)

@app.route("/export_complaints")
def export_complaints():
    return send_file(COMPLAINT_FILE, as_attachment=True)

@app.route("/file_complaint", methods=["GET", "POST"])
def file_complaint():

    if session.get("role") != "citizen":
        return redirect("/citizen_login")

    if request.method == "POST":

        area = request.form["area"]
        issue = request.form["issue"]

        issue_text = issue.lower()

        if "overflow" in issue_text or "urgent" in issue_text:
            priority = "High"
        elif "smell" in issue_text or "delay" in issue_text:
            priority = "Medium"
        else:
            priority = request.form["priority"]

        complaint_id = str(datetime.now().timestamp())
        date = datetime.now().strftime("%Y-%m-%d")

        new_data = pd.DataFrame([[
            complaint_id,
            area,
            issue,
            priority,
            "Pending",
            date
        ]], columns=[
            "complaint_id",
            "area",
            "issue",
            "priority",
            "status",
            "date"
        ])

        df = pd.read_csv(COMPLAINT_FILE)
        df = pd.concat([df, new_data], ignore_index=True)
        df.to_csv(COMPLAINT_FILE, index=False)

        return redirect("/citizen_dashboard")

    # 👉 THIS IS IMPORTANT
    return render_template("file_complaint.html")

@app.route("/complaint_analytics")
def complaint_analytics():
    if os.path.exists(COMPLAINT_FILE):
        df = pd.read_csv(COMPLAINT_FILE)
        priority_count = df["priority"].value_counts().to_dict()
    else:
        priority_count = {}

    return render_template("complaint_analytics.html", data=priority_count)

@app.route("/manage_complaints")
def manage_complaints():
    if session.get("role") != "admin":
        return redirect("/admin_login")

    if os.path.exists(COMPLAINT_FILE):
        df = pd.read_csv(COMPLAINT_FILE)
        complaints = df.to_dict(orient="records")
    else:
        complaints = []

    return render_template("manage_complaints.html", complaints=complaints)

@app.route("/generate_report")
def generate_report():
    file_path = "waste_report.pdf"
    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()

    elements = []
    elements.append(Paragraph("GHMC Waste Management Report", styles['Title']))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Generated Successfully", styles['Normal']))

    doc.build(elements)
    return send_file(file_path, as_attachment=True)

# ==========================
# ADMIN QR BIN SYSTEM
# ==========================

@app.route("/admin/qr-bins")
def admin_qr_bins():

    if session.get("role") != "admin":
        return redirect("/")

    bins = []

    if os.path.exists(BIN_FILE):
        with open(BIN_FILE, newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                bins.append(row)

    return render_template("admin_qr_bins.html", bins=bins)


# -----------------------------
# Generate QR
# -----------------------------

@app.route("/admin_generate_qr/<bin_id>")
def admin_generate_qr(bin_id):

    if session.get("role") != "admin":
        return redirect("/")

    qr_url =BASE_URL = "https://waste-management-kq9c.onrender.com"
    qr_path = os.path.join(QR_FOLDER, f"{bin_id}.png")

    qr = qrcode.make(qr_url)
    qr.save(qr_path)

    return render_template("qr_display.html",
                           qr_image=f"qr_codes/{bin_id}.png",
                           bin_id=bin_id)


# -----------------------------
# Scan Page
# -----------------------------

@app.route("/admin_scan_bin/<bin_id>")
def admin_scan_bin(bin_id):

    if session.get("role") != "admin":
        return redirect("/")

    return render_template("update_bin.html", bin_id=bin_id)


# -----------------------------
# Update Bin Fill %
# -----------------------------

@app.route("/public_report_bin/<bin_id>", methods=["GET", "POST"])
def public_report_bin(bin_id):
    
    if request.method == "POST":
        name = request.form.get("name")
        priority = request.form.get("priority")
        status = request.form.get("status")
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ✅ CREATE FOLDER IF NOT EXISTS
        os.makedirs("data", exist_ok=True)

        alert_file = os.path.join("data", "alerts.csv")

        # ✅ CREATE FILE IF NOT EXISTS
        if not os.path.exists(alert_file):
            with open(alert_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["bin_id", "status", "name", "priority", "time"])

        # 💾 SAVE DATA
        with open(alert_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([bin_id, status, name, priority, time_now])

        # 📧 EMAIL
        send_email_alert(bin_id, status, name)

        return render_template("report_success.html",
                               bin_id=bin_id,
                               status=status,
                               username=name,
                               priority=priority,
                               time=time_now)

    return render_template("select_status.html", bin_id=bin_id)

@app.route("/select_status/<bin_id>", methods=["GET", "POST"])
def select_status(bin_id):

    if request.method == "POST":
        try:
            name = request.form.get("name")
            status = request.form.get("status")
            priority = request.form.get("priority")

            print("DEBUG:", name, status, priority)

            # Save alert
            with open("data/alerts.csv", "a") as f:
                f.write(f"{bin_id},{status},{name},{priority},{datetime.now()}\n")

            return redirect("/thank_you")

        except Exception as e:
            print("ERROR:", e)
            return "Something went wrong: " + str(e)

    return render_template("select_status.html", bin_id=bin_id)

@app.route("/take_action/<bin_id>", methods=["GET", "POST"])
def take_action(bin_id):
    return render_template("assign_vehicle.html", bin_id=bin_id)

@app.route("/assign_vehicle/<bin_id>", methods=["POST"])
def assign_vehicle(bin_id):

    vehicle = request.form.get("vehicle")
    driver = request.form.get("driver")

    print(f"{bin_id} assigned to {vehicle} - {driver}")
    
    
    gps_link = request.form.get("gps_link")

    return f"""
<h3>✅ Vehicle Assigned</h3>
<p>{vehicle} - {driver}</p>

<a href="{gps_link}" target="_blank">
📍 Track Live Location
</a>
"""
      
@app.route("/admin_collect_bin/<bin_id>")
def admin_collect_bin(bin_id):

    if session.get("role") != "admin":
        return redirect("/")

    now = datetime.now().strftime("%Y-%m-%d")
    rows = []

    with open(BIN_FILE, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["bin_id"] == bin_id:
                vehicle = row["assigned_vehicle"]
                row["current_fill_percent"] = 0
                row["status"] = "Active"
                row["last_collected_date"] = now

                # Log entry
                with open(LOG_FILE, "a", newline="") as log:
                    writer = csv.writer(log)
                    writer.writerow([bin_id, now, vehicle, "Collected Successfully"])

            rows.append(row)

    with open(BIN_FILE, "w", newline="") as file:
        fieldnames = rows[0].keys()
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return redirect("/admin_qr_bins")

@app.route("/get_bins_data")
def get_bins_data():

    import pandas as pd

    df = pd.read_csv("upload.csv")

    bins = []

    for _, row in df.iterrows():

        bins.append({
            "bin_id": row["bin_id"],
            "lat": row["latitude"],
            "lng": row["longitude"],
            "fill": row["fill_level"]
        })

    return {"bins": bins}

@app.route("/waste_forecast")
def waste_forecast():

    try:
      
        file_path = os.path.join(BASE_DIR, "dataset", "waste_collection_daily.csv")

        print("Looking for file at:", file_path)  # Debug line

        df = pd.read_csv(file_path)

        X = df[["complaints_count"]]
        y = df["total_waste_kg"]

        model = LinearRegression()
        model.fit(X, y)

        future_complaints = np.array([[35]])
        prediction = model.predict(future_complaints)

        predicted_waste = int(prediction[0])

        return render_template("waste_forecast.html",
                               waste=predicted_waste)

    except Exception as e:
        return f"Forecast Error: {str(e)}"

@app.route("/route_optimization")
def route_optimization():
    routes = ["Route A - Secunderabad",
              "Route B - Kukatpally",
              "Route C - LB Nagar"]
    return render_template("route_optimization.html", routes=routes)

@app.route("/live_map")
def live_map():

    import folium

    try:
        df = pd.read_csv(DATASET_FILE)

        # ✅ Filter only required areas
        df = df[df["area"].isin(["Nizampet", "Kukatpally"])]

    except Exception as e:
        return f"Error loading dataset: {str(e)}"

    # ✅ Create map
    m = folium.Map(location=[17.4948, 78.3996], zoom_start=13)

    # =========================
    # 🚛 Truck Icon
    # =========================
    truck_icon = folium.CustomIcon(
        icon_image="https://cdn-icons-png.flaticon.com/512/743/743131.png",
        icon_size=(40, 40)
    )

    folium.Marker(
        [17.495, 78.405],
        popup="🚛 Truck - TS09AB1234",
        icon=truck_icon
    ).add_to(m)

    # =========================
    # 🗑 Bin Markers with STATUS COLORS
    # =========================
    for _, row in df.iterrows():

        fill = row.get("fill_level", 0)

        # 🎯 Smart color logic
        if fill >= 90:
            color = "red"
            status = "Overflow"
        elif fill >= 70:
            color = "orange"
            status = "Full"
        else:
            color = "green"
            status = "Normal"

        folium.Marker(
            [row["latitude"], row["longitude"]],
            popup=f"""
            <b>Bin ID:</b> {row['bin_id']}<br>
            <b>Area:</b> {row['area']}<br>
            <b>Status:</b> {status}<br>
            <b>Fill Level:</b> {fill}%
            """,
            icon=folium.Icon(color=color, icon="trash", prefix="fa")
        ).add_to(m)

    # =========================
    # 📌 Convert map to HTML
    # =========================
    map_html = m._repr_html_()

    return render_template("map.html", map_html=map_html)

@app.route("/get_vehicle_position")
def get_vehicle_position():

    lat = 17.3850 + random.uniform(-0.01, 0.01)
    lng = 78.4867 + random.uniform(-0.01, 0.01)

    return jsonify({"lat": lat, "lng": lng})

@app.route("/get_dashboard_data")
def get_dashboard_data():

    waste_df = pd.read_csv(DATASET_FILE)

    overflow = waste_df[waste_df["fill_level"] >= 90].shape[0]
    full = waste_df[(waste_df["fill_level"] >= 75) & (waste_df["fill_level"] < 90)].shape[0]
    normal = waste_df[waste_df["fill_level"] < 75].shape[0]

    return jsonify({
        "total": waste_df["bin_id"].nunique(),
        "overflow": overflow,
        "full": full,
        "normal": normal
    })

# ---------------- IMAGE UPLOAD ---------------- #

@app.route("/upload", methods=["POST"])
def upload():

    if "user" not in session:
        return redirect("/login")

    if "image" not in request.files:
        return redirect("/dashboard")

    file = request.files["image"]

    if file.filename == "":
        return redirect("/dashboard")

    filename = datetime.now().strftime("%Y%m%d%H%M%S_") + file.filename

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    file.save(filepath)

    return redirect("/dashboard")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

print(app.url_map)

# ---------------- RUN SERVER ---------------- #

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
