FROM mariadb:11.6.2

RUN apt-get update && apt-get install -y gettext-base

ENV MYSQL_USER=${MYSQL_USER}
ENV MYSQL_PASSWORD=${MYSQL_PASSWORD}

# Original init script expects empty /var/lib/mysql so we initially place
# certificates to the intermediate directory
COPY ./ssl/mysql/mysql.crt /tmp.ssl/mysql.crt
COPY ./ssl/mysql/mysql.key /tmp.ssl/mysql.key
COPY ./ssl/mysql/mysql-ca.pem /tmp.ssl/mysql-ca.pem
RUN chown -R mysql:mysql /tmp.ssl && chmod 0400 /tmp.ssl/mysql.key

COPY ./mysql/mariadb-ssl.cnf /etc/mysql/mariadb.conf.d/

COPY ./mysql/init-databases.template /docker-entrypoint-initdb.d/init-databases.template
CMD envsubst < /docker-entrypoint-initdb.d/init-databases.template > /docker-entrypoint-initdb.d/init-databases.sql && exec docker-entrypoint.sh mariadbd
