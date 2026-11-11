# My Lists (Трекер заметок)

Учебный проект — бэкенд для трекера заметок на FastAPI.

## Стек
- Python 3.15
- FastAPI
- SQLite (собственная система миграций)
- Jinja2 (шаблоны)
- JWT (python-jose), bcrypt
- PyTest

## Функционал
- Регистрация и вход (JWT в cookie)
- CRUD заметок и категорий
- Поиск и сортировка
- Настройки профиля (смена имени, загрузка аватарки)

## Как запустить локально
1. Клонируйте репозиторий: `git clone https://github.com/vash-vanek/My_lists.git`
2. Создайте и активируйте виртуальное окружение.
3. Установите зависимости: `pip install -r requirements.txt`
4. Создайте файл `.env` на основе `.env.example` и впишите свой `SECRET_KEY`.
5. Запустите сервер: `uvicorn MAIN_web:app --reload`
