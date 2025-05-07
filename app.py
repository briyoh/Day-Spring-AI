from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_from_directory
from flask_mysqldb import MySQL
import bcrypt
import pdfkit
import os
import pandas as pd
import PyPDF2
from datetime import datetime
import io

app = Flask(__name__)
app.secret_key = 'your_secret_key'


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'B31162298m#2002'
app.config['MYSQL_DB'] = 'medical_db'
mysql = MySQL(app)


dataset_path = "data/generated_disease_dataset_v2.csv"
df = pd.read_csv(dataset_path)
print("✅ Dataset loaded successfully!")

@app.route('/')
def index():
    if 'user_id' in session:
        return render_template('dashboard.html')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, password FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
            session['user_id'] = user[0]
            session['user_password'] = password  
            return redirect(url_for('index'))
        
        flash("Invalid credentials, please try again.", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()  
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_pw))
            mysql.connection.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
        except:
            mysql.connection.rollback()
            flash("Username already exists", "danger")
        finally:
            cur.close()
    return render_template('register.html')

@app.route('/appointments')
def appointments():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, date, time, reason FROM appointments WHERE patient_id = %s", (session['user_id'],))
    appointments = cur.fetchall()
    cur.close()
    
    return render_template('appointment.html', appointments=appointments)

@app.route('/book_appointment', methods=['POST'])
def book_appointment():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    date = data.get('date')
    time = data.get('time')
    reason = data.get('reason')

    if not all([date, time, reason]):
        return jsonify({'error': 'Missing required fields'}), 400

    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "INSERT INTO appointments (patient_id, date, time, reason) VALUES (%s, %s, %s, %s)",
            (session['user_id'], date, time, reason)
        )
        mysql.connection.commit()
        return jsonify({'message': 'Appointment booked successfully'}), 200
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        username = request.form['username']
        new_password = request.form['new_password']
        hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        cur = mysql.connection.cursor()
        try:
            cur.execute("UPDATE users SET password = %s WHERE username = %s", (hashed_pw, username))
            mysql.connection.commit()
            flash("Password updated successfully!", "success")
            return redirect(url_for('login'))
        except:
            mysql.connection.rollback()
            flash("Error updating password", "danger")
        finally:
            cur.close()
    return render_template('reset_password.html')

@app.route('/chat', methods=['POST'])
def chat():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    user_input = data.get("message", "").lower().strip()
    user_symptoms = [s.strip() for s in user_input.split(",")]

    cur = mysql.connection.cursor()
    cur.execute("SELECT username FROM users WHERE id = %s", (session['user_id'],))
    user = cur.fetchone()
    cur.close()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404

    username = user[0]
    matched_rows = df[df['Symptoms'].str.contains('|'.join(user_symptoms), case=False, na=False)]

    if not matched_rows.empty:
        disease = matched_rows.iloc[0]["Disease Name"]
        medicine = matched_rows.iloc[0]['Medicine Name']
        dosage = matched_rows.iloc[0]['Dosage Instructions']
        notes = matched_rows.iloc[0].get('Notes', 'Take as directed')

        prescription_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Medical Prescription</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .container {{ width: 80%; margin: auto; border: 2px solid #000; padding: 20px; }}
                .header {{ text-align: center; margin-bottom: 20px; }}
                .clinic-name {{ font-size: 24px; font-weight: bold; }}
                .prescription-title {{ font-size: 20px; margin: 10px 0; }}
                .patient-info {{ margin-bottom: 15px; }}
                .diagnosis-info {{ margin-bottom: 15px; }}
                .medication-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                .medication-table, .medication-table th, .medication-table td {{
                    border: 1px solid black; padding: 8px; text-align: left;
                }}
                .doctor-notes {{ margin-top: 15px; }}
                .footer {{ margin-top: 20px; text-align: center; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="clinic-name">MEDICAL PRESCRIPTION</div>
                    <div class="prescription-title">Day Spring Health Centre</div>
                </div>
                
                <div class="patient-info">
                    <p><strong>Patient:</strong> {username}</p>
                    <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
                </div>
                
                <div class="diagnosis-info">
                    <p><strong>Diagnosis:</strong> {disease}</p>
                    <p><strong>Symptoms:</strong> {', '.join(user_symptoms)}</p>
                </div>
                
                <table class="medication-table">
                    <tr>
                        <th>Medication</th>
                        <th>Dosage</th>
                    </tr>
                    <tr>
                        <td>{medicine}</td>
                        <td>{dosage}</td>
                    </tr>
                </table>
                
                <div class="doctor-notes">
                    <p><strong>Doctor's Notes:</strong> {notes}</p>
                </div>
                
                <div class="footer">
                    <p>Generated by Day Spring Health Centre AI</p>
                    <p>This is an automated prescription. Consult your doctor if symptoms persist.</p>
                </div>
            </div>
        </body>
        </html>
        """

        config = pdfkit.configuration(wkhtmltopdf=r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
        pdf_bytes = pdfkit.from_string(prescription_content, False, configuration=config)
        filename = f"prescription_{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        filepath = os.path.join('static/prescriptions', filename)
        os.makedirs('static/prescriptions', exist_ok=True)

        with open(filepath, 'wb') as f:
            f.write(pdf_bytes)

        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        writer = PyPDF2.PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(session['user_password'])
        with open(filepath, "wb") as f:
            writer.write(f)
        
        return jsonify({
            "diagnosis": disease,
            "prescription": f"{medicine} - {dosage}",
            "download_link": f"/download_prescription/{filename}"
        })
    else:
        return jsonify({
            "diagnosis": "Unknown illness",
            "prescription": "Consult a doctor for proper diagnosis."
        })

@app.route('/download_prescription/<filename>')
def download_prescription(filename):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not filename.startswith(f"prescription_{session['user_id']}_"):
        return jsonify({'error': 'Unauthorized file access'}), 403
    
    return send_from_directory('static/prescriptions', filename, as_attachment=True, mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True, extra_files=['templates/*']) 