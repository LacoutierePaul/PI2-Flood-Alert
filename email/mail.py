from flask import Flask

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)

def send_email():
    # Email credentials
    sender_email = "paul.floodpi2@gmail.com"  # Your email address
    receiver_email = "paul.lacoutiere@gmail.com"  # Recipient email address
    password = "pngo ucww upqn ikga"  # Your email account password

    # Create message container
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = "Important : Flood Warning !"

    # Email body
    body = "Hello, this is an automated email from the Flood Warning System. sWe have detected a potential flood in your area. Please take necessary precautions."

    # Attach body to the email
    message.attach(MIMEText(body, 'plain'))

    # Connect to the SMTP server
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()  # Secure the connection
        server.login(sender_email, password)  # Login with your email and password
        text = message.as_string()
        server.sendmail(sender_email, receiver_email, text)  # Send the email

@app.route('/email')
def email_route():
    send_email()
    return "Email sent successfully!"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
