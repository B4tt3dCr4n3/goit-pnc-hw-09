#!/bin/sh

# Директорія для сертифікатів
DESTINATION=./ssl
CANAME=ca
WORKDIR=$DESTINATION/$CANAME
mkdir -p $WORKDIR

# Генерація CA (Кореневого сертифікату)
openssl genpkey -algorithm RSA -out $WORKDIR/$CANAME.key
openssl req -x509 -new -nodes -key $WORKDIR/$CANAME.key -days 1826 -out $WORKDIR/$CANAME.crt -subj '/C=UA/ST=Kyiv/L=Kyiv/O=Goit/OU=IT/CN=Test CA Cert'

# Функція для генерації сертифікатів
generate_cert() {
  SERVICE=$1
  WORKDIR=$DESTINATION/$SERVICE
  mkdir -p $WORKDIR
  openssl genpkey -algorithm RSA -out $WORKDIR/$SERVICE.key
  openssl req -new -nodes -key $WORKDIR/$SERVICE.key -out $WORKDIR/$SERVICE.csr -subj "/C=UA/ST=Kyiv/L=Kyiv/O=Goit/OU=IT/CN=Test Node Cert ($SERVICE)"
  cat > $WORKDIR/$SERVICE.v3.ext << EOF
basicConstraints=CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth, clientAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = $SERVICE
EOF
  openssl x509 -req -in $WORKDIR/$SERVICE.csr -CA $DESTINATION/$CANAME/$CANAME.crt -CAkey $DESTINATION/$CANAME/$CANAME.key -CAcreateserial -out $WORKDIR/$SERVICE.crt -days 730 -extfile $WORKDIR/$SERVICE.v3.ext
}

# Генерація сертифікатів для сервісів
generate_cert acra-client
generate_cert acra-server
generate_cert mysql

# Конвертація для MySQL
cp $DESTINATION/mysql/mysql.key $DESTINATION/mysql/mysql-key.pem
cp $DESTINATION/mysql/mysql.crt $DESTINATION/mysql/mysql-cert.pem
cp $DESTINATION/$CANAME/$CANAME.crt $DESTINATION/mysql/mysql-ca.pem

# Переконатися, що файли доступні
chmod 644 $DESTINATION/mysql/*.pem

# Запуск контейнера для генерації майстер-ключа
ACRA_DOCKER_IMAGE_TAG=0.95.0
docker run --rm -v $DESTINATION:/keys/ cossacklabs/acra-keymaker:${ACRA_DOCKER_IMAGE_TAG} --keystore=v1 --generate_master_key=/keys/master.key
sudo chown $(whoami) $DESTINATION/master.key

# Додавання ключа в .env
ACRA_MASTER_KEY=$(cat $DESTINATION/master.key | base64)
cp ./certificates/env.template ./.env
sed -i '' "s|^ACRA_SERVER_MASTER_KEY=.*|ACRA_SERVER_MASTER_KEY=${ACRA_MASTER_KEY}|" "./.env"