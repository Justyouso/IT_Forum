FROM tiangolo/uwsgi-nginx-flask:python3.6-alpine3.7

ENV UWSGI_INI /app/uwsgi.ini
ENV UWSGI_CHEAPER 4

WORKDIR /app

# 换源
COPY ./pip.conf /root/.pip/pip.conf
COPY requirements.txt /app

RUN pip install -r requirements.txt

COPY . /app



RUN cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtion \
    && echo "Asia/Shanghai" > /etc/timezone

