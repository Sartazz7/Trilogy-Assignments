#! /bin/bash -x

# Install pyenv and python 3.9.5
sudo apt-get update -y

sudo apt-get install --assume-yes make build-essential libssl-dev zlib1g-dev \
 libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev\
 libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python-openssl\
 gitgnupg apt-utils gnupg2 curl gcc

curl https://pyenv.run | bash

pyenv install 3.9.5
pyenv local 3.9.5

# Install MySQL
sudo apt-get install --assume-yes mysql-server-8.0
sudo usermod -d /var/lib/mysql mysql
sudo mkdir -p /var/run/mysqld
sudo chown -R mysql: /var/run/mysqld

# Install MongoDB
echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

wget -qO - https://www.mongodb.org/static/pgp/server-4.2.asc | sudo apt-key add -
echo "deb [ arch=amd64 ] https://repo.mongodb.org/apt/ubuntu bionic/mongodb-org/4.2 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.2.list
sudo apt-get update
sudo apt-get install -y mongodb-org

sudo mkdir -p /data/db
sudo chown -R $USER:$USER /data/db

# BIND TO ALL ADAPTERS IN CONTAINER
sed -i "s,\\(^[[:blank:]]*bindIp:\\) .*,\\1 0.0.0.0," /etc/mongod.conf

# Start MySql
sudo mysqld_safe --skip-grant-tables &
sleep 2
sudo mysql -e "FLUSH PRIVILEGES"
sudo mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'admin'"
sudo service mysql start
sleep 2
sudo service mysql restart
sleep 2
sudo mysql -u root --password=admin -e "create database db"

# Start mongo
#/usr/bin/mongod --port 27017 --dbpath /data/db
sudo /usr/bin/mongod --port 27017 --dbpath /data/db >/dev/null 2>&1 &
ps aux | grep mongo
sleep 5
wget https://codejudge-starter-repo-artifacts.s3.ap-south-1.amazonaws.com/backend-project/database/mongo-database.js
mongo < mongo-database.js
