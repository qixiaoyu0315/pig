from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from starlette import status
import secrets
from datetime import datetime, timedelta

from app.models.database import get_db, User
from app.utils.password import verify_password

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="app/templates")

# 会话存储
sessions = {}

def get_current_user(request: Request, db: Session = Depends(get_db)):
    """获取当前登录用户"""
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        return None
    
    # 获取会话中存储的用户ID
    user_id = sessions[session_id]
    
    # 查询用户信息
    user = db.query(User).filter(User.id == user_id).first()
    return user

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """登录页面"""
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """用户登录"""
    # 查询用户
    user = db.query(User).filter(User.username == username).first()
    
    # 验证密码
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": "用户名或密码错误"}
        )
    
    # 创建会话
    session_id = secrets.token_hex(16)
    sessions[session_id] = user.id
    
    # 更新最后登录时间
    user.last_login = datetime.now()
    db.commit()
    
    # 创建响应并设置cookie
    response = RedirectResponse(url="/home", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="session_id", 
        value=session_id,
        httponly=True,
        max_age=3600  # 1小时过期
    )
    
    return response

@router.get("/logout")
async def logout(request: Request):
    """用户退出登录"""
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        del sessions[session_id]
    
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="session_id")
    
    return response

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """注册页面"""
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    """用户注册"""
    # 检查两次密码是否一致
    if password != confirm_password:
        return templates.TemplateResponse(
            "register.html", 
            {"request": request, "error": "两次输入的密码不一致"}
        )
    
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        return templates.TemplateResponse(
            "register.html", 
            {"request": request, "error": "用户名已存在"}
        )
    
    # 检查邮箱是否已存在
    existing_email = db.query(User).filter(User.email == email).first()
    if existing_email:
        return templates.TemplateResponse(
            "register.html", 
            {"request": request, "error": "邮箱已被注册"}
        )
    
    # 创建新用户
    from app.utils.password import get_password_hash
    new_user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password)
    )
    db.add(new_user)
    db.commit()
    
    # 注册成功后自动登录
    session_id = secrets.token_hex(16)
    sessions[session_id] = new_user.id
    
    response = RedirectResponse(url="/home", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="session_id", 
        value=session_id,
        httponly=True,
        max_age=3600  # 1小时过期
    )
    
    return response
