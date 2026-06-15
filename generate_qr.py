import qrcode
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

file_path = os.path.join(BASE_DIR, "data", "bins.csv")

df = pd.read_csv(file_path)

# 📂 Folder to save QR codes
output_folder = "static/qr_codes"
os.makedirs(output_folder, exist_ok=True)

# 🔁 Generate QR for each bin
for index, row in df.iterrows():

    bin_id = row["bin_id"]

    # 🔗 What QR will store
    qr_data = qr_data = "https://waste-management-kq9c.onrender.com/select_status/" + bin_id
    
    # Create QR
    qr = qrcode.make(qr_data)

    # Save image
    file_path = os.path.join(output_folder, f"{bin_id}.png")
    qr.save(file_path)

    print(f"QR Created for {bin_id}")

print("✅ All QR Codes Generated")