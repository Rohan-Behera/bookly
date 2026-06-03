from fastapi_mail import FastMail, ConnectionConfig, MessageSchema, MessageType
from src.config import Config
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

mail_config = ConnectionConfig(
    MAIL_USERNAME = Config.MAIL_USERNAME,
    MAIL_PASSWORD = Config.MAIL_PASSWORD,
    MAIL_PORT = Config.MAIL_PORT,
    MAIL_SERVER = Config.MAIL_SERVER,
    MAIL_FROM = Config.MAIL_FROM,
    MAIL_FROM_NAME = Config.MAIL_FROM_NAME,
    MAIL_STARTTLS = Config.MAIL_STARTTLS,
    MAIL_SSL_TLS = Config.MAIL_SSL_TLS,
    USE_CREDENTIALS = Config.USE_CREDENTIALS,
    VALIDATE_CERTS = Config.VALIDATE_CERTS,
    TEMPLATE_FOLDER = Path(BASE_DIR, 'templates')
)


mail = FastMail(config=mail_config)

def create_message(recipient: list[str], subject:str, template_body: dict):
    message = MessageSchema(
        recipients=recipient,
        subject=subject,
        template_body=template_body,
        subtype=MessageType.html,        
    )

    return message