# -*- coding: utf-8 -*-
# @Author: dmq
# @Time: 19-6-4 下午4:58
from flask_mail import Message

from app import mail
from app.user.confirm import auth
from config import Config


# 邮件发送
def send_mail(to, subject, **kwargs):
    msg = Message(Config.FLASKY_MAIL_SUBJECT_PREFIX + subject,
                  sender=Config.FLASKY_MAIL_SENDER, recipients=[to])

    msg.html = auth.format(kwargs["user"], kwargs["code"])
    mail.send(msg)
