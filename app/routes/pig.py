from fastapi import APIRouter, Depends, HTTPException, Request, Form, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
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

# 自定义过滤器：根据状态返回对应的Bootstrap样式类
def status_class(status):
    """根据母猪状态返回对应的Bootstrap样式类"""
    status_map = {
        "正常": "bg-success",
        "妊娠": "bg-info",
        "哺乳": "bg-primary",
        "分娩": "bg-warning",
        "休息": "bg-secondary",
        "治疗": "bg-danger",
        "淘汰": "bg-dark"
    }
    return status_map.get(status, "bg-light text-dark")

# 自定义过滤器：根据健康状态返回对应的Bootstrap样式类
def health_status_class(health_status):
    """根据健康状态返回对应的Bootstrap样式类"""
    health_map = {
        "健康": "bg-success",
        "待观察": "bg-warning",
        "治疗中": "bg-danger",
        "隔离中": "bg-dark"
    }
    return health_map.get(health_status, "bg-light text-dark")

# 自定义过滤器：格式化妊娠天数显示
def format_pregnancy_days(days):
    """格式化妊娠天数显示"""
    if days is None:
        return ""
    return f"{days}天"

# 注册过滤器到Jinja2模板环境
templates.env.filters["status_class"] = status_class
templates.env.filters["health_status_class"] = health_status_class
templates.env.filters["format_pregnancy_days"] = format_pregnancy_days

@router.get("/management", response_class=HTMLResponse)
async def pig_management(
    request: Request, 
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    health_status: Optional[str] = None,
    pen_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db), 
    user = Depends(get_current_user)
):
    """母猪管理页面"""
    # 获取猪舍数据
    pig_houses = db.query(PigHouse).all()
    
    # 获取猪圈数据
    pig_pens = db.query(PigPen).all()
    
    # 构建查询条件
    query = db.query(Pig)
    
    if keyword:
        query = query.filter(Pig.ear_tag.like(f'%{keyword}%'))
    
    if status:
        query = query.filter(Pig.status == status)
    
    if health_status:
        query = query.filter(Pig.health_status == health_status)
    
    if pen_id:
        query = query.filter(Pig.pen_id == pen_id)
    
    # 计算总记录数
    total_count = query.count()
    
    # 计算总页数
    total_pages = (total_count + page_size - 1) // page_size
    
    # 限制页码范围
    page = min(max(1, page), max(1, total_pages))
    
    # 获取分页数据
    pigs = query.order_by(Pig.entry_date.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    # 统计各种状态的猪只数量
    all_pigs = query.all()
    status_counts = {}
    for status in ["正常", "妊娠", "哺乳", "分娩", "休息", "治疗", "淘汰"]:
        status_counts[status] = len([p for p in all_pigs if p.status == status])
    
    # 统计健康状态
    health_counts = {}
    for status in ["健康", "待观察", "治疗中", "隔离中"]:
        health_counts[status] = len([p for p in all_pigs if p.health_status == status])
    
    # 获取最近添加的猪只
    recent_pigs = sorted(all_pigs, key=lambda x: x.entry_date, reverse=True)[:5]
    
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
        "total_count": total_count,
        "keyword": keyword,
        "filter_status": status,
        "filter_health_status": health_status,
        "filter_pen_id": pen_id,
        "current_page": page,
        "total_pages": total_pages,
        "page_size": page_size
    })

# 新增API：获取单个母猪详情
@router.get("/detail/{pig_id}", response_class=JSONResponse)
async def get_pig_detail(pig_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    """获取单个母猪的详细信息"""
    pig = db.query(Pig).filter(Pig.id == pig_id).first()
    
    if not pig:
        raise HTTPException(status_code=404, detail="猪只不存在")
    
    # 获取喂食记录
    feeding_records = db.query(FeedingRecord).filter(
        FeedingRecord.pig_id == pig_id
    ).order_by(FeedingRecord.feed_time.desc()).limit(5).all()
    
    # 获取健康记录
    health_records = db.query(HealthRecord).filter(
        HealthRecord.pig_id == pig_id
    ).order_by(HealthRecord.record_date.desc()).limit(5).all()
    
    # 获取繁育记录
    breeding_records = db.query(BreedingRecord).filter(
        BreedingRecord.pig_id == pig_id
    ).order_by(BreedingRecord.breeding_date.desc()).all()
    
    # 更新妊娠天数
    if pig.status == "妊娠" and pig.last_breeding_date:
        pig.update_pregnancy_days()
        db.add(pig)
        db.commit()
    
    # 格式化日期和数据
    pig_data = {
        "id": pig.id,
        "ear_tag": pig.ear_tag,
        "birth_date": pig.birth_date.strftime("%Y-%m-%d") if pig.birth_date else None,
        "breed": pig.breed,
        "gender": pig.gender,
        "weight": pig.weight,
        "backfat_thickness": pig.backfat_thickness,
        "status": pig.status,
        "health_status": pig.health_status,
        "entry_date": pig.entry_date.strftime("%Y-%m-%d") if pig.entry_date else None,
        "pen": pig.pen.pen_number if pig.pen else None,
        "pen_id": pig.pen_id,
        "notes": pig.notes,
        "last_breeding_date": pig.last_breeding_date.strftime("%Y-%m-%d") if pig.last_breeding_date else None,
        "pregnancy_days": pig.pregnancy_days,
        "feeding_records": [
            {
                "feed_time": record.feed_time.strftime("%Y-%m-%d %H:%M"),
                "feed_amount": record.feed_amount,
                "feed_type": record.feed_type,
                "duration": record.duration,
                "feed_status": record.feed_status
            } for record in feeding_records
        ],
        "health_records": [
            {
                "record_date": record.record_date.strftime("%Y-%m-%d"),
                "temperature": record.temperature,
                "diagnosis": record.diagnosis,
                "treatment": record.treatment
            } for record in health_records
        ],
        "breeding_records": [
            {
                "breeding_date": record.breeding_date.strftime("%Y-%m-%d") if record.breeding_date else None,
                "status": record.status,
                "expected_farrowing_date": record.expected_farrowing_date.strftime("%Y-%m-%d") if record.expected_farrowing_date else None,
                "actual_farrowing_date": record.actual_farrowing_date.strftime("%Y-%m-%d") if record.actual_farrowing_date else None,
                "total_born": record.total_born,
                "born_alive": record.born_alive
            } for record in breeding_records
        ]
    }
    
    return pig_data

# 新增API：添加母猪
@router.post("/add", response_class=JSONResponse)
async def add_pig(
    ear_tag: str = Form(...),
    birth_date: str = Form(...),
    breed: str = Form(...),
    gender: str = Form("母"),
    weight: float = Form(...),
    backfat_thickness: Optional[float] = Form(None),
    status: str = Form(...),
    health_status: str = Form(...),
    pen_id: int = Form(...),
    entry_date: str = Form(...),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """添加新的母猪"""
    # 检查耳标是否已存在
    existing_pig = db.query(Pig).filter(Pig.ear_tag == ear_tag).first()
    if existing_pig:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "耳标号已存在"}
        )
    
    # 检查猪圈是否存在
    pen = db.query(PigPen).filter(PigPen.id == pen_id).first()
    if not pen:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "所选猪圈不存在"}
        )
    
    # 检查猪圈容量
    if pen.current_count >= pen.capacity:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "所选猪圈已满"}
        )
    
    # 格式化日期
    birth_date_obj = datetime.datetime.strptime(birth_date, "%Y-%m-%d")
    entry_date_obj = datetime.datetime.strptime(entry_date, "%Y-%m-%d")
    
    # 创建新母猪
    new_pig = Pig(
        ear_tag=ear_tag,
        birth_date=birth_date_obj,
        breed=breed,
        gender=gender,
        weight=weight,
        backfat_thickness=backfat_thickness,
        status=status,
        health_status=health_status,
        pen_id=pen_id,
        entry_date=entry_date_obj,
        notes=notes
    )
    
    db.add(new_pig)
    
    # 更新猪圈当前数量
    pen.current_count += 1
    
    # 更新猪舍当前数量
    pig_house = db.query(PigHouse).filter(PigHouse.id == pen.pig_house_id).first()
    if pig_house:
        pig_house.current_count += 1
    
    db.commit()
    
    return {"success": True, "message": "添加成功", "pig_id": new_pig.id}

# 新增API：更新母猪
@router.put("/update/{pig_id}", response_class=JSONResponse)
async def update_pig(
    pig_id: int,
    ear_tag: str = Form(...),
    birth_date: str = Form(...),
    breed: str = Form(...),
    weight: float = Form(...),
    backfat_thickness: Optional[float] = Form(None),
    status: str = Form(...),
    health_status: str = Form(...),
    pen_id: int = Form(...),
    entry_date: str = Form(...),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """更新母猪信息"""
    # 查找母猪
    pig = db.query(Pig).filter(Pig.id == pig_id).first()
    if not pig:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "猪只不存在"}
        )
    
    # 检查耳标是否已存在（排除当前猪只）
    existing_pig = db.query(Pig).filter(Pig.ear_tag == ear_tag, Pig.id != pig_id).first()
    if existing_pig:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "耳标号已存在"}
        )
    
    # 处理猪圈变更
    old_pen_id = pig.pen_id
    if pen_id != old_pen_id:
        # 检查新猪圈是否存在
        new_pen = db.query(PigPen).filter(PigPen.id == pen_id).first()
        if not new_pen:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "所选猪圈不存在"}
            )
        
        # 检查新猪圈容量
        if new_pen.current_count >= new_pen.capacity:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "所选猪圈已满"}
            )
        
        # 更新旧猪圈数量
        old_pen = db.query(PigPen).filter(PigPen.id == old_pen_id).first()
        if old_pen:
            old_pen.current_count -= 1
            
            # 更新旧猪舍数量
            old_house = db.query(PigHouse).filter(PigHouse.id == old_pen.pig_house_id).first()
            if old_house:
                old_house.current_count -= 1
        
        # 更新新猪圈数量
        new_pen.current_count += 1
        
        # 更新新猪舍数量
        new_house = db.query(PigHouse).filter(PigHouse.id == new_pen.pig_house_id).first()
        if new_house:
            new_house.current_count += 1
    
    # 格式化日期
    birth_date_obj = datetime.datetime.strptime(birth_date, "%Y-%m-%d")
    entry_date_obj = datetime.datetime.strptime(entry_date, "%Y-%m-%d")
    
    # 更新猪只信息
    pig.ear_tag = ear_tag
    pig.birth_date = birth_date_obj
    pig.breed = breed
    pig.weight = weight
    pig.backfat_thickness = backfat_thickness
    pig.status = status
    pig.health_status = health_status
    pig.pen_id = pen_id
    pig.entry_date = entry_date_obj
    pig.notes = notes
    pig.last_update = datetime.datetime.now()
    
    db.commit()
    
    return {"success": True, "message": "更新成功"}

# 新增API：删除母猪
@router.delete("/delete/{pig_id}", response_class=JSONResponse)
async def delete_pig(
    pig_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """删除母猪"""
    # 查找母猪
    pig = db.query(Pig).filter(Pig.id == pig_id).first()
    if not pig:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "猪只不存在"}
        )
    
    # 获取猪圈信息以便更新计数
    pen_id = pig.pen_id
    pen = db.query(PigPen).filter(PigPen.id == pen_id).first()
    
    # 删除相关记录
    db.query(FeedingRecord).filter(FeedingRecord.pig_id == pig_id).delete()
    db.query(HealthRecord).filter(HealthRecord.pig_id == pig_id).delete()
    db.query(BreedingRecord).filter(BreedingRecord.pig_id == pig_id).delete()
    
    # 删除猪只
    db.delete(pig)
    
    # 更新猪圈数量
    if pen:
        pen.current_count = max(0, pen.current_count - 1)
        
        # 更新猪舍数量
        house = db.query(PigHouse).filter(PigHouse.id == pen.pig_house_id).first()
        if house:
            house.current_count = max(0, house.current_count - 1)
    
    db.commit()
    
    return {"success": True, "message": "删除成功"}

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
    
    # 获取报警并排序
    alerts = query.order_by(Alert.alert_time.desc()).all()
    
    # 获取报警统计信息
    total_alerts = len(alerts)
    
    # 按级别统计
    level_counts = {}
    for l in ["紧急", "重要", "一般"]:
        level_counts[l] = len([a for a in alerts if a.alert_level == l])
    
    # 按状态统计
    status_counts = {}
    for s in ["未处理", "处理中", "已解决", "已忽略"]:
        status_counts[s] = len([a for a in alerts if a.status == s])
    
    # 按类型统计
    type_counts = {}
    alert_types = set(alert.alert_type for alert in alerts)
    for t in alert_types:
        type_counts[t] = len([a for a in alerts if a.alert_type == t])
    
    return templates.TemplateResponse("pig/alerts.html", {
        "request": request,
        "user": user,
        "page_title": "报警信息",
        "alerts": alerts,
        "total_alerts": total_alerts,
        "level_counts": level_counts,
        "status_counts": status_counts,
        "type_counts": type_counts,
        "filter_status": status,
        "filter_level": level,
        "filter_type": type
    })

@router.get("/control", response_class=HTMLResponse)
async def control_interface(request: Request, user = Depends(get_current_user)):
    """控制界面"""
    return templates.TemplateResponse("pig/control.html", {
        "request": request,
        "user": user,
        "page_title": "控制界面"
    })

# 新增API：添加繁育记录
@router.post("/breeding/add", response_class=JSONResponse)
async def add_breeding_record(
    pig_id: int = Form(...),
    breeding_date: str = Form(...),
    expected_farrowing_date: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """添加新的繁育记录"""
    # 查找母猪
    pig = db.query(Pig).filter(Pig.id == pig_id).first()
    if not pig:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "猪只不存在"}
        )
    
    # 检查性别必须是母
    if pig.gender != "母":
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "只有母猪才能添加繁育记录"}
        )
    
    # 检查是否有未完成的繁育记录
    existing_record = db.query(BreedingRecord).filter(
        BreedingRecord.pig_id == pig_id,
        BreedingRecord.status == "进行中"
    ).first()
    
    if existing_record:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "该母猪有未完成的繁育记录"}
        )
    
    # 格式化日期
    breeding_date_obj = datetime.datetime.strptime(breeding_date, "%Y-%m-%d")
    expected_farrowing_date_obj = None
    
    if expected_farrowing_date:
        expected_farrowing_date_obj = datetime.datetime.strptime(expected_farrowing_date, "%Y-%m-%d")
    else:
        # 默认114天
        expected_farrowing_date_obj = breeding_date_obj + datetime.timedelta(days=114)
    
    # 创建新繁育记录
    new_breeding = BreedingRecord(
        pig_id=pig_id,
        breeding_date=breeding_date_obj,
        expected_farrowing_date=expected_farrowing_date_obj,
        status="进行中",
        notes=notes
    )
    
    db.add(new_breeding)
    db.flush()  # 获取新记录ID
    
    # 更新母猪状态
    new_breeding.update_pig_status(db)
    
    return {"success": True, "message": "添加成功", "record_id": new_breeding.id}

# 新增API：更新繁育记录
@router.put("/breeding/{record_id}", response_class=JSONResponse)
async def update_breeding_record(
    record_id: int,
    status: str = Form(...),  # 进行中, 已分娩, 已流产, 已取消
    actual_farrowing_date: Optional[str] = Form(None),
    total_born: Optional[int] = Form(None),
    born_alive: Optional[int] = Form(None),
    stillborn: Optional[int] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """更新繁育记录"""
    # 查找繁育记录
    breeding_record = db.query(BreedingRecord).filter(BreedingRecord.id == record_id).first()
    if not breeding_record:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "繁育记录不存在"}
        )
    
    # 更新状态
    old_status = breeding_record.status
    breeding_record.status = status
    
    # 已分娩状态需要额外信息
    if status == "已分娩":
        if not actual_farrowing_date:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "已分娩状态需要提供实际分娩日期"}
            )
        
        if not total_born or not born_alive:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "已分娩状态需要提供产仔数量"}
            )
        
        breeding_record.actual_farrowing_date = datetime.datetime.strptime(actual_farrowing_date, "%Y-%m-%d")
        breeding_record.total_born = total_born
        breeding_record.born_alive = born_alive
        breeding_record.stillborn = stillborn if stillborn is not None else (total_born - born_alive)
    
    # 更新备注
    if notes:
        breeding_record.notes = notes
    
    db.add(breeding_record)
    
    # 只有当状态变更时才更新母猪状态
    if old_status != status:
        breeding_record.update_pig_status(db)
    else:
        db.commit()
    
    return {"success": True, "message": "更新成功"} 