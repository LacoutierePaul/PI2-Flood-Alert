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
    message['Subject'] = "Subject of the Email"

    # Email body
    body = "This is the body of the email."

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

if __name__ == "__main__":
    app.run()
