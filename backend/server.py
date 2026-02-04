import os
import smtplib
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import uuid
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_url_path='') 
CORS(app)  # Enables the frontend to talk to this backend

# --- CONFIGURATION (FILL THESE IN) ---
SENDER_EMAIL = os.getenv("MAIL_ID")
SENDER_PASSWORD = os.getenv("APP_PASSWORD")


if not SENDER_EMAIL or not SENDER_PASSWORD:
    print("Error: Email credentials not found in .env file.")
# -------------------------------------

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def send_email(recipient_email, result_file_path):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = "Your Topsis Result"

        body = "Hello,\n\nPlease find attached the result file generated from your data.\n\nBest,\nTopsis Web Service"
        msg.attach(MIMEText(body, 'plain'))

        # Attach the result file
        with open(result_file_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(result_file_path)}")
            msg.attach(part)

        # Connect to Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, recipient_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False

@app.route('/upload', methods=['POST'])
def process_topsis():
    # 1. Check if file is present
    if 'file' not in request.files:
        return jsonify({"message": "No file uploaded"}), 400
    
    file = request.files['file']
    weights = request.form.get('weights')
    impacts = request.form.get('impacts')
    email = request.form.get('email')

    if not file or not weights or not impacts or not email:
        return jsonify({"message": "Missing data fields"}), 400

    # 2. Save Input File uniquely to avoid collision
    unique_id = str(uuid.uuid4())
    input_filename = f"data_{unique_id}.csv"
    output_filename = f"result_{unique_id}.csv"
    
    input_path = os.path.join(UPLOAD_FOLDER, input_filename)
    output_path = os.path.join(UPLOAD_FOLDER, output_filename)
    
    file.save(input_path)

    try:
        # 3. RUN THE COMMAND LINE PROMPT
        # Command format: topsis <InputDataFile> <Weights> <Impacts> <ResultFileName>
        command = [
            "topsis", 
            input_path, 
            weights, 
            impacts, 
            output_path
        ]
        
        print(f"Running command: {' '.join(command)}")
        
        # Execute the command
        result = subprocess.run(command, capture_output=True, text=True)

        # Check if the command failed (return code non-zero) or if output file missing
        if result.returncode != 0:
            return jsonify({"message": f"Topsis Error: {result.stderr}"}), 500
        
        if not os.path.exists(output_path):
            return jsonify({"message": "Processing failed, output file not generated."}), 500

        # 4. Email the result
        email_sent = send_email(email, output_path)

        if email_sent:
            return jsonify({"message": f"Success! Results sent to {email}"}), 200
        else:
            return jsonify({"message": "Processing done, but failed to send email."}), 500

    except Exception as e:
        return jsonify({"message": str(e)}), 500
    
    finally:
        # 5. Clean up files (optional, keeps server clean)
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    # Update port to utilize the environment's port or default to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
