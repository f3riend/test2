from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .logger import auto_logger
import smtplib

logger = auto_logger()

class MailManager:
    def __init__(self, sender, receiver, password, subject, body):
        self.sender = sender
        self.receiver = receiver
        self.password = password
        self.subject = subject
        self.body = body

        try:
            # Create the email message
            self.message = MIMEMultipart()
            self.message['From'] = self.sender
            self.message['To'] = self.receiver
            self.message['Subject'] = self.subject
            self.message.attach(MIMEText(self.body, 'plain'))
        except Exception as e:
            logger.info("❌ Error while creating the message object:", e)

    def send(self):
        """
        Notes for Gmail users:
        - Two-factor authentication must be enabled on the sender's account.
        - A 16-digit App Password must be used instead of the regular account password.
        """
        try:
            # Use SMTP_SSL for Gmail on port 465
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.ehlo()  # Identify yourself to the server
                server.login(self.sender, self.password)
                server.sendmail(self.sender, self.receiver, self.message.as_string())

            logger.info("✅ Email sent successfully!")
        except Exception as e:
            logger.warning("❌ Error sending email:", e)
            logger.info("Make sure you are using a 16-digit Gmail App Password and 2FA is enabled.")
