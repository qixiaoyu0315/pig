from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from starlette import status
import datetime

from app.models.database import get_db, Pig, FeedingRecord, HealthRecord, Alert
from app.routes.auth import get_current_user

router = APIRouter(tags=["home"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """根路径重定向到登录页面"""
    return RedirectResponse(url="/login", status_code=status.HTTP_307_TEMPORARY_REDIRECT)

@router.get("/home", response_class=HTMLResponse)
async def home_page(request: Request, db: Session = Depends(get_db), user = Depends(get_current_user)):
    """主页"""
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    # 获取当天的日期
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + datetime.timedelta(days=1)
    
    # 获取猪只总数和各状态数量
    total_pigs = db.query(func.count(Pig.id)).scalar()
    pregnant_pigs = db.query(func.count(Pig.id)).filter(Pig.status == "妊娠").scalar()
    nursing_pigs = db.query(func.count(Pig.id)).filter(Pig.status == "哺乳").scalar()
    empty_pigs = db.query(func.count(Pig.id)).filter(Pig.status == "休息").scalar()
    
    # 获取健康状态统计
    healthy_pigs = db.query(func.count(Pig.id)).filter(Pig.health_status == "健康").scalar()
    observe_pigs = db.query(func.count(Pig.id)).filter(Pig.health_status == "待观察").scalar()
    treating_pigs = db.query(func.count(Pig.id)).filter(Pig.health_status == "治疗中").scalar()
    isolated_pigs = db.query(func.count(Pig.id)).filter(Pig.health_status == "隔离中").scalar()
    
    # 获取今日饲料消耗
    today_feed = db.query(func.sum(FeedingRecord.feed_amount)).filter(
        FeedingRecord.feed_time >= today,
        FeedingRecord.feed_time < tomorrow
    ).scalar() or 0
    
    # 获取本周饲料消耗
    week_start = today - datetime.timedelta(days=today.weekday())
    week_feed = db.query(func.sum(FeedingRecord.feed_amount)).filter(
        FeedingRecord.feed_time >= week_start,
        FeedingRecord.feed_time < tomorrow
    ).scalar() or 0
    
    # 获取本月饲料消耗
    month_start = today.replace(day=1)
    month_feed = db.query(func.sum(FeedingRecord.feed_amount)).filter(
        FeedingRecord.feed_time >= month_start,
        FeedingRecord.feed_time < tomorrow
    ).scalar() or 0
    
    # 剩余饲料统计（这里用一个固定值，实际应该有一个饲料库存表）
    remaining_feed = 680
    
    # 获取最近的报警
    recent_alerts = db.query(Alert).filter(
        Alert.status.in_(["未处理", "处理中"])
    ).order_by(desc(Alert.alert_time)).limit(2).all()
    
    # 获取最近活动
    recent_activities = []
    
    # 最近的喂食记录
    feeding_records = db.query(FeedingRecord).order_by(desc(FeedingRecord.feed_time)).limit(5).all()
    for record in feeding_records:
        pig = db.query(Pig).filter(Pig.id == record.pig_id).first()
        if pig:
            activity = {
                "time": record.feed_time,
                "type": "饲料投放",
                "subject": f"圈舍 {pig.pen_id}",
                "operator": "系统" if record.automatic else "管理员",
                "details": f"{'自动' if record.automatic else '手动'}投放 {record.feed_amount}kg"
            }
            recent_activities.append(activity)
    
    # 最近的健康记录
    health_records = db.query(HealthRecord).order_by(desc(HealthRecord.record_date)).limit(5).all()
    for record in health_records:
        pig = db.query(Pig).filter(Pig.id == record.pig_id).first()
        if pig:
            activity = {
                "time": record.record_date,
                "type": "健康检查",
                "subject": pig.ear_tag,
                "operator": record.vet_name or "系统",
                "details": f"{'无异常' if not record.symptoms else record.symptoms}"
            }
            recent_activities.append(activity)
    
    # 按时间排序并取前5条
    recent_activities = sorted(recent_activities, key=lambda x: x["time"], reverse=True)[:5]
    
    return templates.TemplateResponse("home.html", {
        "request": request, 
        "user": user,
        "page_title": "首页",
        "total_pigs": total_pigs,
        "pregnant_pigs": pregnant_pigs,
        "nursing_pigs": nursing_pigs,
        "empty_pigs": empty_pigs,
        "healthy_pigs": healthy_pigs,
        "observe_pigs": observe_pigs,
        "treating_pigs": treating_pigs,
        "isolated_pigs": isolated_pigs,
        "today_feed": today_feed,
        "week_feed": week_feed,
        "month_feed": month_feed,
        "remaining_feed": remaining_feed,
        "recent_alerts": recent_alerts,
        "recent_activities": recent_activities
    })
