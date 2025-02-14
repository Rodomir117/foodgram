[![Main Foodgram workflow](https://github.com/rodomir117/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/rodomir117/foodgram/actions/workflows/main.yml)
# Проект: [Foodgram](https://foodgram.ddnsking.com/)
### Выпускной проект *Яндекс.Практикум* курса Python-разработчик(backend)

Проект Foodgram дает возможность пользователям создавать и хранить рецепты на онлайн-платформе. Кроме того, можно скачать список продуктов, необходимых для приготовления блюда, просмотреть рецепты друзей и добавить любимые рецепты в список избранных.


## Технологии
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![Django REST Framework](https://img.shields.io/badge/Django%20REST%20Framework-092E20?style=for-the-badge&logo=django&logoColor=white)
![Djoser](https://img.shields.io/badge/Djoser-092E20?style=for-the-badge&logo=django&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Postman](https://img.shields.io/badge/Postman-FF6C37?style=for-the-badge&logo=postman&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Gunicorn](https://img.shields.io/badge/Gunicorn-499848?style=for-the-badge&logo=gunicorn&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)

## [API документация](https://foodgram.ddnsking.com/redoc/)

## [Администрирование](https://foodgram.ddnsking.com/admin/)

    Email: admin@ya.ru
    Password: pianino1


## Запуск проекта на удаленном сервере

1. Установить docker compose на сервер:
```bash
sudo apt update
```
```bash
sudo apt install curl
```
```bash
curl -fSL https://get.docker.com -o get-docker.sh
```
```bash
sudo sh ./get-docker.sh
```
```bash    
sudo apt-get install docker-compose-plugin
```

2. Скачать файл [docker-compose.production.yml](https://github.com/rodomir117/foodgram/blob/main/docker-compose.production.yml) на свой сервер.

3. На сервере в директории с файлом **docker-compose.production.yml** создать файл  **.env**:
``` bash    
POSTGRES_DB=имя базы
POSTGRES_USER=владелец базы
POSTGRES_PASSWORD=пароль базы
DB_HOST=db
DB_PORT=5432
SECRET_KEY=ключ приложения django
DEBUG=True/False
ALLOWED_HOSTS=разрешенные хосты(your.domain.com)
```        
4. Запустить Docker compose:
``` bash
sudo docker compose -f docker-compose.production.yml up -d
```
5. На сервере настроить и запустить Nginx:
- открыть файлы конфигурации
    ``` bash
    sudo nano /etc/nginx/sites-enabled/default
    ```
- внести изменения, заменив **<your.domain.com>** на свое доменное имя
    ``` bash 
    server {
        listen 80;
        server_name <your.domain.com>;

        location / {
            proxy_set_header Host $http_host;        
            proxy_pass http://127.0.0.1:7070;
            client_max_body_size 5M;
            
        }
    }
    ``` 
- убедиться, что в файле конфигурации нет ошибок
    ``` bash
    sudo nginx -t
    ```
- перезагрузить конфигурацию
    ``` bash
    sudo service nginx reload
    ```

## Автор проекта [**Виталий Васюков**](https://github.com/Rodomir117)