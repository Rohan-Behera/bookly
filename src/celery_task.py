from celery import Celery
from src.mail import mail, create_message
from asgiref.sync import async_to_sync


""" 
Celery is a background worker
It does not support asynchronous calls. 
If we want it to add to our async code and behave accordingly we have to use ASGIREF package.
It provides many functions, so to perform synchronous calls inside async calls
"""
c_app = Celery()

c_app.config_from_object('src.config')

@c_app.task()
def send_email(recipients: list[str], subject:str, html_message: dict, template_name: str):
    message = create_message(
        recipient=recipients, subject=subject, template_body=html_message,
    )
    async_to_sync(mail.send_message(message=message, template_name="verify_email.html"))
    