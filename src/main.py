import json
import os
import smtplib
from fastapi import FastAPI, HTTPException
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

####################################################
# setup
####################################################
app = FastAPI()
# allow same origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HOST = os.getenv("HOST_ENVV", "localhost")
PORT = int(os.getenv("PORT_ENVV", "8888"))

####################################################
# functions
####################################################
def save_openapi_spec_to_file():
    with open("./docs/OAS.json", "w") as f:
        json.dump(app.openapi(), f , indent=2)

def setup_host_in_openapi_spec():
    openapi_schema = app.openapi()
    openapi_schema["servers"] = [{
        "url": f"http://localhost:{PORT}"
        # if docker debug and windows OS, use http://host.docker.internal to reach host machine
    }]

def setupOpenApi():
    setup_host_in_openapi_spec()
    save_openapi_spec_to_file()

def get_email_strategy(provider):
    if provider == "gmail":
        return GmailStrategy()
    elif provider == "outlook":
        return OutlookStrategy()
    else:
        raise HTTPException(status_code=400, detail="Invalid email provider")

####################################################
# interfaces
####################################################
class EmailStrategy:
    def send_email(self, to_email, subject, body):
        pass

####################################################
# classes
####################################################
class EmailConfig(BaseModel):
    provider: str
    to_email: str
    subject: str
    body: str
class GmailStrategy(EmailStrategy):
    def send_email(self, to_email, subject, body):
        try:
            gmail_username = os.getenv("GMAIL_USERNAME", "tosozteam@gmail.com")
            gmail_password = os.getenv("GMAIL_PASSWORD", "mxyf sfxg bwqw jlwa")

            # Create a connection to the Gmail SMTP server
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(gmail_username, gmail_password)

            # Create the email message
            msg = MIMEMultipart()
            msg['From'] = gmail_username
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            # Send the email
            server.sendmail(gmail_username, to_email, msg.as_string())

            # Quit the SMTP server
            server.quit()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

class OutlookStrategy(EmailStrategy):
    def send_email(self, to_email, subject, body):
        try:
            outlook_username = os.getenv("OUTLOOK_USERNAME", "your@outlook.com")
            outlook_password = os.getenv("OUTLOOK_PASSWORD", "your_password")

            # Create a connection to the Outlook SMTP server
            server = smtplib.SMTP("smtp.office365.com", 587)
            server.starttls()
            server.login(outlook_username, outlook_password)

            # Create the email message
            msg = MIMEMultipart()
            msg['From'] = outlook_username
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            # Send the email
            server.sendmail(outlook_username, to_email, msg.as_string())

            # Quit the SMTP server
            server.quit()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

####################################################
# routes
####################################################
@app.post("/send-email")
async def send_email(email_config: EmailConfig):
    email_strategy = get_email_strategy(email_config.provider)
    email_strategy.send_email(email_config.to_email, email_config.subject, email_config.body)
    return {"message": "Email sent successfully"}

####################################################
# main
####################################################
if __name__ == "__main__":
    setupOpenApi()
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
