FROM tiangolo/uwsgi-nginx-flask:python3.6-alpine3.7

ENV UWSGI_INI /app/uwsgi.ini
ENV UWSGI_CHEAPER 4

COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

RUN cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtion \
    && echo "Asia/Shanghai" > /etc/timezone

