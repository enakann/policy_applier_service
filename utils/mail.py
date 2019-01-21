import smtplib
from email.mime.text import MIMEText


class Notify:
    def __init__(self, sender, receivers, subject):
        # sender    -> the sender's email address
        # receivers -> list of recipient's email address(es)
        # subject   -> mail subject
        self.sender = sender
        self.receivers = receivers
        self.subject = subject

    def send_mail(self, body):
        try:
            # Create a text/html message
            msg = MIMEText (body, 'html')
            msg['Subject'] = self.subject
            msg['From'] = self.sender
            msg['To'] = ', '.join (self.receivers)
            # Send the message via our own SMTP server, but don't include the
            # envelope header.
            s = smtplib.SMTP ('127.0.0.1')
            print
            msg.as_string()
            # s.set_debuglevel(1)
            s.sendmail(None, self.receivers, msg.as_string())
            s.quit ()

        except smtplib.SMTPException:
            raise


if __name__ == '__main__':
    mail = Alert ("navaneetha.k.kannan@oracle.com", ['navaneetha.k.kannan@oracle.com'], "test")
    mail.send_mail ("test")

