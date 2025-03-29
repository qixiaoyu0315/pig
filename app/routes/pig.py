from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional, List
import datetime
import json
from starlette import status

from app.models.database import get_db, PigHouse, PigPen, Pig, FeedingRecord, FeedSetting, HealthRecord, BreedingRecord, EnvironmentRecord, Alert
from app.routes.auth import get_current_user

router = APIRouter(
    prefix="/pig",
    tags=["pig"],
    responses={404: {"description": "Not found"}},
)

templates = Jinja2Templates(directory="app/templates")

@router.get("/management", response_class=HTMLResponse)
async def pig_management(request: Request, db: Session = Depends(get_db), user = Depends(get_current_user)):
    """母猪管理页面"""
    # 获取猪舍数据
    pig_houses = db.query(PigHouse).all()
    
    # 获取猪圈数据
    pig_pens = db.query(PigPen).all()
    
    # 获取猪只数据，按状态统计
    pigs = db.query(Pig).all()
    
    # 统计各种状态的猪只数量
    status_counts = {}
    for status in ["正常", "妊娠", "哺乳", "分娩", "休息", "治疗", "淘汰"]:
        status_counts[status] = len([p for p in pigs if p.status == status])
    
    # 统计健康状态
    health_counts = {}
    for status in ["健康", "待观察", "治疗中", "隔离中"]:
        health_counts[status] = len([p for p in pigs if p.health_status == status])
    
    # 获取最近添加的猪只
    recent_pigs = sorted(pigs, key=lambda x: x.entry_date, reverse=True)[:5]
    
    return templates.TemplateResponse("pig/management.html", {
        "request": request,
        "user": user,
        "page_title": "母猪管理",
        "pig_houses": pig_houses,
        "pig_pens": pig_pens,
        "pigs": pigs,
        "status_counts": status_counts,
        "health_counts": health_counts,
        "recent_pigs": recent_pigs,
        "total_count": len(pigs)
    })

@router.get("/feeding", response_class=HTMLResponse)
async def feeding_info(
    request: Request, 
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db), 
    user = Depends(get_current_user)
):
    """采食信息页面"""
    # 设置默认日期范围为过去7天
    if not start_date:
        start_date = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    start_datetime = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end_datetime = datetime.datetime.strptime(end_date, "%Y-%m-%d") + datetime.timedelta(days=1)
    
    # 获取指定日期范围内的喂食记录
    feeding_records = db.query(FeedingRecord).filter(
        FeedingRecord.feed_time >= start_datetime,
        FeedingRecord.feed_time < end_datetime
    ).order_by(FeedingRecord.feed_time.desc()).all()
    
    # 按日期统计每日喂食量
    daily_feed_amount = {}
    for record in feeding_records:
        date_key = record.feed_time.strftime("%Y-%m-%d")
        if date_key not in daily_feed_amount:
            daily_feed_amount[date_key] = 0
        daily_feed_amount[date_key] += record.feed_amount
    
    # 统计各喂食状态的比例
    status_counts = {}
    for status in ["正常", "少食", "拒食", "过量"]:
        status_counts[status] = len([r for r in feeding_records if r.feed_status == status])
    
    total_records = len(feeding_records)
    status_percents = {status: count / total_records * 100 if total_records > 0 else 0 
                      for status, count in status_counts.items()}
    
    # 获取有喂食记录的猪的信息
    pig_ids = set(record.pig_id for record in feeding_records)
    pigs_with_records = db.query(Pig).filter(Pig.id.in_(pig_ids)).all()
    pig_map = {pig.id: pig for pig in pigs_with_records}
    
    # 为每条记录添加猪的信息
    for record in feeding_records:
        record.pig_info = pig_map.get(record.pig_id)
    
    return templates.TemplateResponse("pig/feeding.html", {
        "request": request,
        "user": user,
        "page_title": "采食信息",
        "feeding_records": feeding_records,
        "daily_feed_amount": daily_feed_amount,
        "status_counts": status_counts,
        "status_percents": status_percents,
        "start_date": start_date,
        "end_date": end_date,
        "total_amount": sum(record.feed_amount for record in feeding_records),
        "total_records": total_records
    })

@router.get("/feeding-settings", response_class=HTMLResponse)
async def feeding_settings(request: Request, db: Session = Depends(get_db), user = Depends(get_current_user)):
    """下料设置页面"""
    # 获取所有猪圈
    pig_pens = db.query(PigPen).all()
    
    # 获取所有下料设置
    feed_settings = db.query(FeedSetting).all()
    
    # 将JSON时间段转换为Python列表
    for setting in feed_settings:
        setting.time_slots_list = json.loads(setting.time_slots)
        
        # 查找对应的猪圈
        setting.pen = db.query(PigPen).filter(PigPen.id == setting.pen_id).first()
    
    return templates.TemplateResponse("pig/feeding_settings.html", {
        "request": request,
        "user": user,
        "page_title": "下料设置",
        "pig_pens": pig_pens,
        "feed_settings": feed_settings
    })

@router.get("/daily-summary", response_class=HTMLResponse)
async def daily_summary(
    request: Request, 
    date: Optional[str] = None,
    db: Session = Depends(get_db), 
    user = Depends(get_current_user)
):
    """每日汇总页面"""
    # 设置默认日期为今天
    if not date:
        date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    target_date = datetime.datetime.strptime(date, "%Y-%m-%d")
    next_date = target_date + datetime.timedelta(days=1)
    
    # 获取当天的喂食记录
    feeding_records = db.query(FeedingRecord).filter(
        FeedingRecord.feed_time >= target_date,
        FeedingRecord.feed_time < next_date
    ).all()
    
    # 计算总喂食量
    total_feed_amount = sum(record.feed_amount for record in feeding_records)
    
    # 获取当天的健康记录
    health_records = db.query(HealthRecord).filter(
        HealthRecord.record_date >= target_date,
        HealthRecord.record_date < next_date
    ).all()
    
    # 获取当天的繁育记录（分娩）
    farrowing_records = db.query(BreedingRecord).filter(
        BreedingRecord.actual_farrowing_date >= target_date,
        BreedingRecord.actual_farrowing_date < next_date
    ).all()
    
    # 计算总出生数和存活数
    total_born = sum(record.total_born or 0 for record in farrowing_records)
    born_alive = sum(record.born_alive or 0 for record in farrowing_records)
    
    # 获取当天的环境记录
    environment_records = db.query(EnvironmentRecord).filter(
        EnvironmentRecord.record_time >= target_date,
        EnvironmentRecord.record_time < next_date
    ).order_by(EnvironmentRecord.record_time).all()
    
    # 计算平均温湿度
    avg_temp = sum(record.temperature for record in environment_records) / len(environment_records) if environment_records else 0
    avg_humidity = sum(record.humidity for record in environment_records) / len(environment_records) if environment_records else 0
    
    # 获取当天的异常记录
    abnormal_feeding = [r for r in feeding_records if r.feed_status != "正常"]
    abnormal_health = [r for r in health_records if r.diagnosis != "正常" and r.diagnosis is not None]
    
    # 获取当天的报警
    alerts = db.query(Alert).filter(
        Alert.alert_time >= target_date,
        Alert.alert_time < next_date
    ).order_by(Alert.alert_time.desc()).all()
    
    return templates.TemplateResponse("pig/daily_summary.html", {
        "request": request,
        "user": user,
        "page_title": "每日汇总",
        "date": date,
        "feeding_records": feeding_records,
        "health_records": health_records,
        "farrowing_records": farrowing_records,
        "environment_records": environment_records,
        "alerts": alerts,
        "total_feed_amount": total_feed_amount,
        "total_feeding_count": len(feeding_records),
        "total_born": total_born,
        "born_alive": born_alive,
        "farrowing_count": len(farrowing_records),
        "avg_temp": avg_temp,
        "avg_humidity": avg_humidity,
        "abnormal_feeding": abnormal_feeding,
        "abnormal_health": abnormal_health
    })

@router.get("/alerts", response_class=HTMLResponse)
async def alerts(
    request: Request,
    status: Optional[str] = None,
    level: Optional[str] = None,
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """报警信息页面"""
    # 构建查询
    query = db.query(Alert)
    
    # 根据状态筛选
    if status:
        query = query.filter(Alert.status == status)
    
    # 根据级别筛选
    if level:
        query = query.filter(Alert.alert_level == level)
    
    # 根据类型筛选
    if type:
        query = query.filter(Alert.alert_type == type)
    
    # 获取报警记录
    alerts = query.order_by(Alert.alert_time.desc()).all()
    
    # 统计各种状态的报警数量
    status_counts = {}
    for alert_status in ["未处理", "处理中", "已解决", "已忽略"]:
        status_counts[alert_status] = len([a for a in alerts if a.status == alert_status])
    
    # 统计各级别的报警数量
    level_counts = {}
    for alert_level in ["紧急", "重要", "一般"]:
        level_counts[alert_level] = len([a for a in alerts if a.alert_level == alert_level])
    
    # 获取当前存在的报警类型
    alert_types = set(alert.alert_type for alert in alerts)
    
    return templates.TemplateResponse("pig/alerts.html", {
        "request": request,
        "user": user,
        "page_title": "报警信息",
        "alerts": alerts,
        "status_counts": status_counts,
        "level_counts": level_counts,
        "alert_types": sorted(alert_types),
        "selected_status": status,
        "selected_level": level,
        "selected_type": type,
        "total_count": len(alerts)
    })

@router.get("/control", response_class=HTMLResponse)
async def control_interface(request: Request, user = Depends(get_current_user)):
    """控制界面页面"""
    return templates.TemplateResponse("pig/control.html", {
        "request": request,
        "user": user,
        "page_title": "控制界面"
    }) 