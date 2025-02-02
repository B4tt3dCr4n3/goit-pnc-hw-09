FROM python:3.12-alpine

RUN apk update \
    && apk add --no-cache bash python3 py3-pip py3-psycopg2 \
    && pip3 install --no-cache-dir --upgrade pip

RUN mkdir /app.requirements /app.test-data
COPY ./python/requirements.txt /app.requirements/
RUN pip3 install --no-cache-dir --break-system-packages -r /app.requirements/requirements.txt

RUN mkdir /ssl 
COPY ./ssl/acra-client/acra-client.crt /ssl/acra-client.crt
COPY ./ssl/acra-client/acra-client.key /ssl/acra-client.key
COPY ./ssl/mysql/mysql-ca.pem /ssl/ca.crt

RUN chmod 0600 -R /ssl/

COPY ./python/entry.sh /entry.sh
RUN chmod +x /entry.sh

VOLUME /app.acrakeys
VOLUME /app

WORKDIR /app
ENTRYPOINT ["/entry.sh"]
