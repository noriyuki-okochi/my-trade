#
# my function-library
#
from datetime import datetime
import smtplib
from smtplib import SMTPException
import ssl
from email.mime.text import MIMEText
from email.header import Header
from email.mime.multipart import MIMEMultipart
#
# send gmail
#
USER = 'noriyuki.okochi@gmail.com'
PASS = 'zgdhvxouunmdcdzc'

def send_gmail(to_address="", subject="", body="", from_address=USER, password=PASS):
    cset = 'utf-8'
#    message = MIMEMultipart("alternative")
    message = MIMEText(body, "plain", cset)
    message["Subject"] = Header(subject, cset)
    message["From"] = from_address
    message["To"] = to_address

    #part1 = MIMEText(text, "plain", cset)
    #part2 = MIMEText(html, "html", cset)
    #message.attach(part1)
    #message.attach(part2)

    smtp_host ='smtp.gmail.com'
    smtp_port = 465

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as con:
            #con.set_debuglevel(2)
            con.set_debuglevel(0)
            con.login(from_address, password)
            con.sendmail(from_address, to_address, message.as_string())
            #con.quit()
    except SMTPException as e:
        print(e.strerror)
#
# return the escape-sequences to set colored text.
#
def colored_16(style,fg,bg,text):
    return f"\033[{style};{fg};{bg}m{text}"
#
# return the escape-sequences to reset colored one.
#
def colored_reset():
    return '\033[0;0m'
#
# return formated time-stamp
#
def time_stamp():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


