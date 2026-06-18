import qrcode
import pandas as pd
import os

# 📁 Get project path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 📄 CSV file path
file_path = os.path.join(BASE_DIR, "data", "bins.csv")

# 📊 Read data
df = pd.read_csv(file_path)

# 📂 Folder to save QR codes
output_folder = os.path.join(BASE_DIR, "static", "qr_codes")
os.makedirs(output_folder, exist_ok=True)

# 🌐 Your IP address (IMPORTANT)
BASE_URL = f"https://waste-management-kq9c.onrender.com"
# 🔁 Generate QR codes
for index, row in df.iterrows():

    bin_id = row["bin_id"]

    # ✅ Correct QR URL
    qr_data = f"{BASE_URL}/public_report_bin/{bin_id}"

    # Create QR
    qr = qrcode.make(qr_data)

    # Save QR
    save_path = os.path.join(output_folder, f"{bin_id}.png")
    qr.save(save_path)

    print(f"✅ QR Created for {bin_id}")

print("🎉 All QR Codes Generated Successfully!")