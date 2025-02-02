# goit-pnc-hw-09

## Опис проекту
Цей проект демонструє криптографічний захист баз даних на прикладі MySQL та Acra. У ньому використовується SSL для захищеного підключення до MySQL, а також Acra для шифрування та захисту даних.

---
## Розгортання

### 1. Клонування репозиторію
```sh
git clone https://github.com/B4tt3dCr4n3/goit-pnc-hw-09.git
cd ./goit-pnc-hw-09
```

### 2. Генерація SSL-сертифікатів та Acra master-key
```sh
./certificates/ssl_gen.sh
```

### 3. Збірка та запуск проекту
```sh
chmod -R 700 ./acra-server
docker compose up --build --force-recreate
```

### 4. Вирішення проблем із запуском
Якщо виникають проблеми, спробуй перезапустити контейнер:
```sh
docker compose down -v
docker compose up --build --force-recreate
```

---
## Використання

### 1. Деплой бази даних `TestDB1`
```sh
mariadb -h127.0.0.1 -u test-user -p -P3306 \
    --ssl \
    --ssl-ca=ssl/mysql/mysql-ca.pem \
    --ssl-cert=ssl/mysql/mysql-cert.pem \
    --ssl-key=ssl/mysql/mysql-key.pem \
    --database=TestDB1 < ./test-data/TestDB1.sql
```

### 2. Деплой бази даних `TestDB2`
```sh
docker exec goit-pnc-hw-09-python-1 python /app/main.py --db_name TestDB2 --port 9393 --import_dump /app/test-data/TestDB2.sql
```

### 3. Отримання розшифрованих даних із `TestDB2`
```sh
docker exec goit-pnc-hw-09-python-1 python /app/main.py --db_name TestDB2 --port 9393 --print
```

---
## Вимоги
- Docker & Docker Compose
- MariaDB або MySQL
- Python (для роботи зі скриптами)