from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


from database_web import (init_db, search, get_all_notes, get_all_categories, post_notes, 
get_one_notes, delete_note, edit_note, create_one_category, post_all_categories, 
get_one_category, get_all_notes_in_category, edit_category, delete_category,
create_user, get_user_by_username, create_zero_category, user_category_relationship,
run_migrations, get_user_profile, post_user_profile, save_avatar) 

from auth import (hash_password, verify_password, create_token, get_user_id_from_token)

init_db()
run_migrations()
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
def read_root():
    return RedirectResponse(url="/main_page", status_code=303)

# --------------------- Выход-------------------------------------------
@app.get("/logout")
def logout():
    response = RedirectResponse("/login_page", status_code=303)
    response.delete_cookie("token")
    return response

# --------------------- Не строгая привязка -----------------------------
def get_current_user_optional(request: Request):
    token = request.cookies.get("token")
    if not token:
        return None
    user_id = get_user_id_from_token(token)
    if user_id is None:
        return None
    return user_id

# --------------------- Строгая привязка --------------------------------
def get_current_user(request: Request):
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(
            status_code=303,
            headers={"Location": "/login_page"})
    user_id = get_user_id_from_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=303,
            headers={"Location": "/login_page"})
    return user_id

# --------------------- Вход -------------------------------------------
@app.get("/login_page", response_class=HTMLResponse)
def login_get(request: Request, error: str = None):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": error})
    
    
@app.post("/login_page")
def login_post(username: str = Form(...), password: str = Form(...)):
    user = get_user_by_username(username)
    if not user:
        return RedirectResponse ("/login_page?error=invalid")
    password_hash = user["password_hash"]
    result = verify_password(password, password_hash)
    if not result:
        return RedirectResponse ("/login_page?error=invalid")
    token = create_token(user["id"])
    response = RedirectResponse("/main_page", status_code=303)
    response.set_cookie(key="token", value=token, httponly=True)
    return response

# --------------------- Регистрация -------------------------------------------
@app.get("/register_page", response_class=HTMLResponse)
def register_get(request: Request, error: str = None):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"error": error})

@app.post("/register_page")
def register_post(username: str = Form(...), password: str = Form(...)):
    if len(password) < 8:
        return RedirectResponse("/register_page?error=short", status_code=303)
    if len(password) > 64:
        return RedirectResponse("/register_page?error=long", status_code=303)
    hash = hash_password(password)
    user_id = create_user(username, hash)
    if user_id: 
        create_zero_category(user_id)
        return RedirectResponse("/login_page", status_code=303)
    else:
        return RedirectResponse("/register_page?error=exists", status_code=303)

# --------------------- Поиск -------------------------------------------
@app.get("/search_page", response_class=HTMLResponse)
def search_page_get(request: Request, q: str = "", user_id : int = Depends(get_current_user)):
    q = q.strip()
    searched = q != ""          
    results = search(q, user_id) if searched else []
    return templates.TemplateResponse(
        request=request,
        name="search_page.html",
        context={"results": results, "searched": searched}
    )
# --------------------- Главная страница -------------------------------------------
@app.get("/main_page", response_class=HTMLResponse)
def main_page(request: Request, user_id : int = Depends(get_current_user_optional)):
    logged_in = user_id is not None
    return templates.TemplateResponse(
    request=request,
    name="main.html",
    context={"logged_in": logged_in})

# --------------------- Редактировать категорию -------------------------------------------
@app.get("/edit_category_page/{cat_id}", response_class=HTMLResponse)
def edit_category_get(cat_id: int, request: Request, user_id : int = Depends(get_current_user)):
    notes = get_all_notes_in_category(cat_id, user_id)
    category = get_one_category(cat_id, user_id)
    return templates.TemplateResponse(
    request=request,
    name="category_detail.html",
    context={"category": category, "notes": notes})

@app.post("/edit_category_page/{cat_id}")
def edit_category_post(cat_id: int, name: str = Form(...), user_id : int = Depends(get_current_user)):
    extra_cat = user_category_relationship(user_id)
    if extra_cat == cat_id:
        return RedirectResponse(f"/edit_category_page/{cat_id}", status_code=303)
    name = name.strip()
    if not name:
        return RedirectResponse(f"/edit_category_page/{cat_id}", status_code=303)
    edit_category(cat_id, name, user_id)
    return RedirectResponse("/all_categories_page", status_code=303)

# --------------------- Удалить категорию -------------------------------------------
@app.post("/delete_category_page/{cat_id}")
def delete_one_category(cat_id: int, user_id : int = Depends(get_current_user)):
    extra_cat_id = user_category_relationship(user_id)
    if extra_cat_id == cat_id:
        return RedirectResponse(f"/edit_category_page/{cat_id}", status_code=303)
    delete_category(extra_cat_id, cat_id, user_id)
    return RedirectResponse("/all_categories_page", status_code=303)

# --------------------- Все категории -------------------------------------------
@app.get("/all_categories_page", response_class=HTMLResponse)
def all_categories_get(request: Request, user_id : int = Depends(get_current_user)):
    categories = post_all_categories(user_id)
    return templates.TemplateResponse(
    request=request,
    name="all_categories.html",
    context={"categories": categories})
    
# --------------------- Создать категорию -------------------------------------------
@app.get("/create_category", response_class=HTMLResponse)
def create_new_category(request: Request, user_id : int = Depends(get_current_user)):
    return templates.TemplateResponse(
    request=request,
    name="add_category.html")
    
@app.post("/create_category")
def create_category(name: str = Form(...), user_id : int = Depends(get_current_user)):
    name = name.strip()
    if not name:
        return RedirectResponse("/create_category", status_code=303)
    if not create_one_category(name, user_id):
        return RedirectResponse("/create_category?error=exists", status_code=303)
    return RedirectResponse("/all_categories_page", status_code=303)

# --------------------- Все заметки -------------------------------------------
@app.get("/page", response_class=HTMLResponse)
def read_page(request: Request, sort: str = "date_desc", user_id: int = Depends(get_current_user)):
    notes = get_all_notes(user_id, sort)
    return templates.TemplateResponse(
    request=request,
    name="index.html",
    context={"notes": notes, "sort": sort})
    
# --------------------- Добавить заметку -------------------------------------------
@app.get("/add_note_page", response_class=HTMLResponse)
def add_one_note(request: Request, error: str = None, user_id: int = Depends(get_current_user)):
    categories = get_all_categories(user_id)
    return templates.TemplateResponse(
        request=request,
        name="add_note.html",
        context={"categories": categories, "error": error})

@app.post("/add_note_page")
def post_one_note(title: str = Form(...), content: str = Form(...), category_id: int = Form(...), user_id: int = Depends(get_current_user)):
    title = title.strip()
    content = content.strip()
    if not title or not content:
        return RedirectResponse("/add_note_page", status_code=303)
    result = post_notes(title, content, category_id, user_id)
    if result["status"] == "duplicate":
        return RedirectResponse("/add_note_page?error=duplicate", status_code=303)
    return RedirectResponse("/page", status_code=303)

# --------------------- Редактировать заметку -------------------------------------------
@app.get("/edit_note_page/{note_id}", response_class=HTMLResponse)
def edit_one_note(note_id:int, request: Request, user_id : int = Depends(get_current_user)):
    note = get_one_notes(note_id, user_id)
    categories = get_all_categories(user_id)
    return templates.TemplateResponse(
        request=request,
        name="note_detail.html",
        context={"categories": categories, "note": note})

@app.post("/edit_note_page/{note_id}")
def edit_one_note(note_id:int, title:str = Form(...), content:str = Form(...), category_id:int = Form(...), user_id : int = Depends(get_current_user)):
    title = title.strip()
    if not title:
        return RedirectResponse(f"/edit_note_page/{note_id}", status_code=303)
    content = content.strip()
    if not content:
        return RedirectResponse(f"/edit_note_page/{note_id}", status_code=303)
    edit_note(title, content, category_id, note_id, user_id)
    return RedirectResponse("/page", status_code=303)

# --------------------- Удалить заметку -------------------------------------------------
@app.post("/delete_note_page/{note_id}")
def delete_note_post(note_id:int, user_id : int = Depends(get_current_user)):
    delete_note(note_id, user_id)
    return RedirectResponse("/page", status_code=303)



@app.get("/settings_page", response_class=HTMLResponse)
def get_settings_page(request: Request, user_id : int = Depends(get_current_user)):
    user_profile = get_user_profile(user_id)
    if user_profile is None:
        return RedirectResponse ("/login_page?error=invalid")
    return templates.TemplateResponse(
        request=request,
        name="settings_page.html",
        context={"user": user_profile})

@app.post("/settings_page")
def post_settings_page(username:str = Form(...), display_name:str = Form(...), user_id : int = Depends(get_current_user), upload_file: UploadFile | None = File(None)):
    if not upload_file or not upload_file.filename:
        user_profile = get_user_profile(user_id)
        if user_profile is None:
            raise HTTPException(404, "Пользователь не найден")
        avatar = user_profile["avatar"] 
    else:
        avatar = save_avatar(user_id, upload_file)    
    post_user_profile(username, display_name, avatar, user_id)
    return RedirectResponse("/main_page", status_code=303)
    

