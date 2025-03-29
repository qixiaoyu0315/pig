from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.routes.home import get_current_user

router = APIRouter(prefix="/pig")
templates = Jinja2Templates(directory="app/templates")

@router.get("/management", response_class=HTMLResponse)
async def pig_management(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse("pig/management.html", {
        "request": request,
        "user": user,
        "page_title": "母猪管理"
    })

@router.get("/feeding", response_class=HTMLResponse)
async def feeding_info(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse("pig/feeding.html", {
        "request": request,
        "user": user,
        "page_title": "采食信息"
    })

@router.get("/feeding-settings", response_class=HTMLResponse)
async def feeding_settings(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse("pig/feeding_settings.html", {
        "request": request,
        "user": user,
        "page_title": "下料设置"
    })

@router.get("/daily-summary", response_class=HTMLResponse)
async def daily_summary(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse("pig/daily_summary.html", {
        "request": request,
        "user": user,
        "page_title": "每日汇总"
    })

@router.get("/alerts", response_class=HTMLResponse)
async def alerts(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse("pig/alerts.html", {
        "request": request,
        "user": user,
        "page_title": "报警信息"
    })

@router.get("/control", response_class=HTMLResponse)
async def control_panel(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse("pig/control.html", {
        "request": request,
        "user": user,
        "page_title": "控制界面"
    }) 