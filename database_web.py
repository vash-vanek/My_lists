import sqlite3, importlib
from fastapi import HTTPException
from pathlib import Path
from Lists import random_name
import uuid

def init_db():
    connection = sqlite3.connect("tracker.db")
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    cursor.execute("""CREATE TABLE IF NOT EXISTS categories(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT NOT NULL,
        UNIQUE (user_id, name)
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS entries(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT,
        user_id INTEGER,
        category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
        status TEXT DEFAULT 'planned',
        rating INTEGER CHECK (rating BETWEEN 1 AND 10),
        created_at TEXT DEFAULT (date('now'))
    )""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT NOT NULL UNIQUE, 
        password_hash TEXT NOT NULL,
        default_category_id INTEGER
    )""")
    connection.commit()
    connection.close()

# ===========================================================================================================================================================
# ---------------------------------------- ПОИСК ЗАМЕТКИ ----------------------------------------------------------------------------------------------------
def search(q, user_id):
    if not q:
        return []
    conn = sqlite3.connect("tracker.db")
    cursor = conn.cursor()
    cursor.execute("""SELECT e.id, e.title, e.content, e.category_id, e.status, e.rating, e.created_at, c.name FROM entries e LEFT JOIN categories c 
                   ON e.category_id = c.id WHERE (e.title LIKE ? OR e.content LIKE ?) AND e.user_id = ?""", ('%' + q + '%', '%' + q + '%', user_id))
    results = cursor.fetchall()
    conn.close()
    new_list = []
    for result in results:
        res = {"id":result[0], "title":result[1], "content":result[2], "category_id":result[3], 
               "status":result[4], "rating":result[5], "created_at":result[6], "name":result[7]}
        new_list.append(res)
    return new_list

# ===========================================================================================================================================================
# ---------------------------------------- ПОЛУЧЕНИЕ ВСЕХ ЗАМЕТОК -------------------------------------------------------------------------------------------
def get_all_notes(user_id, sort = "date_desc"):
    query = "SELECT id, title, content, created_at FROM entries WHERE user_id = ?"
    if sort == "date_desc":
        query += " ORDER BY created_at DESC"
    elif sort == "date_asc":
        query += " ORDER BY created_at ASC"
    else:
        query += " ORDER BY created_at DESC" 
    conn = sqlite3.connect("tracker.db")
    cursor = conn.cursor()
    cursor.execute(query, (user_id,))
    results = cursor.fetchall()
    conn.close()
    new_list = []
    for result in results:
        res = {"id":result[0], "title":result[1], "content":result[2], "created_at":result[3]}
        new_list.append(res)
    if sort == "title_asc":
            new_list.sort(key=lambda d: (d["title"].lower(), d["title"]))
    elif sort == "title_desc":
            new_list.sort(key=lambda d: (d["title"].lower(), d["title"]), reverse=True)
    return new_list

# ===========================================================================================================================================================
# ---------------------------------------- ПОЛУЧЕНИЕ ВСЕХ КАТЕГОРИЙ -----------------------------------------------------------------------------------------
def get_all_categories(user_id):
    conn = sqlite3.connect("tracker.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM categories WHERE user_id = ?", (user_id,))
    results = cursor.fetchall()
    conn.close()
    new_list = []
    for result in results:
        res = {"id":result[0], "name":result[1]}
        new_list.append(res)
    return new_list

# ===========================================================================================================================================================
# ---------------------------------------- ДОБАВЛЕНИЕ НОВОЙ ЗАМЕТКИ -----------------------------------------------------------------------------------------
def post_notes(title, content, category_id, user_id):
    conn = sqlite3.connect("tracker.db")
    cursor = conn.cursor()   
    cursor.execute("SELECT id FROM entries WHERE title = ? AND content = ? AND user_id = ?",(title, content, user_id))
    results = cursor.fetchone()
    if not results:
        cursor.execute("INSERT INTO entries (title, content, category_id, user_id) VALUES (?, ?, ?, ?)", (title, content, category_id, user_id))
        result = cursor.lastrowid
        conn.commit()
        conn.close()
        return {"status": "ok", "id": result}
    conn.commit()
    conn.close()
    return {"status": "duplicate"}

# ===========================================================================================================================================================
# ---------------------------------------- ПОЛУЧЕНИЕ ОДНОЙ ЗАМЕТКИ ПО ЕЕ АЙДИ -------------------------------------------------------------------------------
def get_one_notes(note_id, user_id):
    conn = sqlite3.connect("tracker.db")
    cursor = conn.cursor()
    cursor.execute("""SELECT e.id, e.title, e.content, e.category_id, e.status, e.rating, e.created_at, c.name FROM entries e 
                   LEFT JOIN categories c ON e.category_id = c.id WHERE e.id = ? AND e.user_id = ?""", (note_id, user_id))
    result = cursor.fetchone()
    conn.close()
    if result is None:
        raise HTTPException(status_code=404, detail="Не верный id")
    my_dict = {}
    my_dict["id"] = result[0]
    my_dict["title"] = result[1]
    my_dict["content"] = result[2]
    my_dict["category_id"] = result[3]
    my_dict["status"] = result[4]
    my_dict["rating"] = result[5]
    my_dict["created_at"] = result[6]
    my_dict["name"] = result[7]
    return my_dict

# ===========================================================================================================================================================
# ---------------------------------------- УДАЛЕНИЕ ЗАМЕТКИ -------------------------------------------------------------------------------------------------
def delete_note(note_id, user_id):
    conn = sqlite3.connect("tracker.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM entries WHERE id = ? AND user_id = ?", (note_id, user_id))
    result = cursor.rowcount
    if result == 0:
        raise HTTPException(status_code=404, detail="Не верный id")       
    conn.commit()
    conn.close()
    return {"status": "ok"}

# ===========================================================================================================================================================
# ---------------------------------------- РЕДАКТИРОВАНИЕ ЗАМЕТКИ -------------------------------------------------------------------------------------------
def edit_note(title, content, category_id, note_id, user_id):
    conn = sqlite3.connect("tracker.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE entries SET title = ?, content = ?, category_id = ? WHERE id = ? AND user_id = ?", (title, content, category_id, note_id, user_id))
    conn.commit()
    conn.close()
    return {"status": "ok"}

# ===========================================================================================================================================================
# ---------------------------------------- ДОБАВЛЕНИЕ КАТЕГОРИИ ---------------------------------------------------------------------------------------------
def create_one_category(name: str, user_id):
    conn = sqlite3.connect("tracker.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO categories (name, user_id) VALUES (?, ?)", (name, user_id))
    result = cursor.rowcount
    conn.commit()
    conn.close()
    return result > 0

# ===========================================================================================================================================================
# ---------------------------------------- СПИСОК ВСЕХ КАТЕГОРИЙ --------------------------------------------------------------------------------------------
def post_all_categories(user_id):
    conn = sqlite3.connect("tracker.db")
    cursor = conn.cursor()
    cursor.execute("SELECT c.id, c.name, COUNT(e.id) AS notes_count FROM categories c LEFT JOIN entries e ON e.category_id = c.id WHERE c.user_id = ? GROUP BY c.id", (user_id,))
    results = cursor.fetchall()
    conn.close()
    new_list = []
    for result in results:
        res = {"id":result[0], "name":result[1], "notes_count":result[2]}
        new_list.append(res)
    return new_list

# ===========================================================================================================================================================
# ---------------------------------------- ПОЛУЧЕНИЕ ОДНОЙ КАТЕГОРИИ ПО ЕЕ АЙДИ -----------------------------------------------------------------------------
def get_one_category(cat_id, user_id):
    conn = sqlite3.connect("tracker.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM categories WHERE id = ? AND user_id = ?", (cat_id, user_id))
    result = cursor.fetchone()
    conn.close()
    if result is None:
        raise HTTPException(status_code=404, detail="Не верный id")
    my_dict = {}
    my_dict["id"] = result[0]
    my_dict["name"] = result[1]
    return my_dict

# ===========================================================================================================================================================
# ---------------------------------------- ПОЛУЧЕНИЕ ВСЕХ ЗАМЕТОК ОДНОЙ КАТЕГОРИИ ---------------------------------------------------------------------------
def get_all_notes_in_category(cat_id, user_id):
    conn = sqlite3.connect("tracker.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, content, created_at FROM entries WHERE category_id = ? AND user_id = ?", (cat_id, user_id))
    results = cursor.fetchall()
    conn.close()
    new_list = []
    for result in results:
        res = {"id":result[0], "title":result[1], "content":result[2], "created_at":result[3]}
        new_list.append(res)
    return new_list

# ===========================================================================================================================================================
# ---------------------------------------- РЕДАКТИРОВАНИЕ КАТЕГОРИИ -----------------------------------------------------------------------------------------
def edit_category(id, name, user_id):
    conn = sqlite3.connect("tracker.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE categories SET name = ? WHERE id = ? AND user_id = ?", (name, id, user_id))
    conn.commit()
    conn.close()
    return {"status": "ok"}

# ===========================================================================================================================================================
# ---------------------------------------- УДАЛЕНИЕ КАТЕГОРИИ -----------------------------------------------------------------------------------------------
def delete_category(extra_cat_id, cat_id, user_id):
    conn = sqlite3.connect("tracker.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE entries SET category_id = ? WHERE category_id = ? AND user_id = ?", (extra_cat_id, cat_id, user_id))
    cursor.execute("DELETE FROM categories WHERE id = ? AND user_id = ?", (cat_id, user_id))
    result = cursor.rowcount
    if result == 0:
        raise HTTPException(status_code=404, detail="Не верный id")       
    conn.commit()
    conn.close()
    return {"status": "ok"}

# ===========================================================================================================================================================
# ---------------------------------------- СОЗДАНИЕ ПОЛЬЗОВАТЕЛЯ --------------------------------------------------------------------------------------------
def create_user(username, password_hash):
    connection = sqlite3.connect('tracker.db')
    cursor = connection.cursor()
    display_name = random_name()
    default_avatar = "default.png"
    cursor.execute("INSERT OR IGNORE INTO users (username, password_hash, display_name, avatar) VALUES (?, ?, ?, ?)", 
                   (username, password_hash, display_name, default_avatar))
    if cursor.rowcount == 0:
        connection.close()
        return False
    user_id = cursor.lastrowid
    connection.commit()
    connection.close()
    if user_id:
        return user_id
    else:
        return False

# ===========================================================================================================================================================
# ---------------------------------------- ВХОД В АККАУНТ ---------------------------------------------------------------------------------------------------
def get_user_by_username(username):
    connection = sqlite3.connect('tracker.db')
    cursor = connection.cursor()
    cursor.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,))
    results = cursor.fetchone()
    connection.close()
    if not results:
        return None
    else: 
        return {"id": results[0], "username": results[1], "password_hash": results[2]}

# ===========================================================================================================================================================
# ---------------------------------------- СОЗДАНИЕ НУЛЕВОЙ КАТЕГОРИИ ---------------------------------------------------------------------------------------
def create_zero_category(user_id):
    connection = sqlite3.connect('tracker.db')
    cursor = connection.cursor()
    cursor.execute("INSERT INTO categories (name, user_id) VALUES (?, ?)", ('Без категории', user_id))
    cat_id = cursor.lastrowid
    cursor.execute("UPDATE users SET default_category_id = ? WHERE id = ?", (cat_id, user_id))
    connection.commit()
    connection.close()

# ===========================================================================================================================================================
# ---------------------------------------- СВЯЗЬ АЙДИ ЮЗЕРА И НУЛЕВОЙ КАТЕГОРИИ -----------------------------------------------------------------------------
def user_category_relationship(user_id):
    connection = sqlite3.connect('tracker.db')
    cursor = connection.cursor()
    cursor.execute("SELECT default_category_id FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    connection.close()
    if result is None:
        return None
    extra_cat = result[0]
    return extra_cat

# ===========================================================================================================================================================
# ---------------------------------------- СОЗДАНИЕ ТАБЛИЦЫ ВСЕХ ДОБАВЛЕННЫХ МИГРАЦИЙ -----------------------------------------------------------------------
def create_migrations_log_table(conn):
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS migrations_log(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        applied_at TEXT DEFAULT (datetime('now'))
        )""")
    conn.commit()

# ===========================================================================================================================================================
# -------------------------------------------------- ПРИМЕНЕНИЕ ВСЕХ МИГРАЦИЙ -------------------------------------------------------------------------------
def run_migrations():
    conn = sqlite3.connect("tracker.db")
    cursor = conn.cursor()
    create_migrations_log_table(conn)
    cursor.execute("SELECT name FROM migrations_log")
    result = cursor.fetchall()
    applied = []
    for res in result:
        applied.append(res[0])
    folder_path = Path("migrations")
    files_only = [item.stem for item in folder_path.glob("*.py")]
    for file in files_only:
        if file != "__init__":
            if file not in applied:
                module = importlib.import_module(f"migrations.{file}")
                module.upgrade(conn)
                cursor.execute("INSERT INTO migrations_log (name) VALUES (?)", (file,))
                conn.commit()
    conn.close()        

def get_user_profile(user_id):
    with sqlite3.connect("tracker.db") as conn:
        results = conn.execute("SELECT username, display_name, avatar FROM users WHERE id = ?", (user_id,)).fetchone()
        if results is None:
            return None
        avatar = results[2] or "default.png"
        display_name = results[1]
        if display_name is None:
            display_name = random_name()
            conn.execute("UPDATE users SET display_name = ? WHERE id = ?",(display_name, user_id))
        return {"username": results[0], "display_name": display_name, "avatar": avatar}

def post_user_profile(username, display_name, avatar, user_id):
    with sqlite3.connect("tracker.db") as conn:
        conn.execute("UPDATE users SET username = ?, display_name = ?, avatar = ? WHERE id = ?",(username, display_name, avatar, user_id))

def save_avatar(user_id, upload_file) -> str:
    extension = Path(upload_file.filename).suffix
    white_list = [".png", ".jpg", ".jpeg", ".gif", ".webp"]
    if extension.lower() not in white_list:
        raise HTTPException(400, "Не подходящий формат файла")
    file_name = (f"{user_id}_{uuid.uuid4()}{extension}")
    with open(f"static/avatars/{file_name}", "wb") as file:
        file.write(upload_file.file.read())
    return f"avatars/{file_name}"