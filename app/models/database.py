from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import enum
from datetime import datetime, timedelta
import os
import random
import json

# 创建数据库连接
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'pig_management.db')}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 枚举类型定义
class PigStatus(enum.Enum):
    正常 = "正常"
    妊娠 = "妊娠"
    哺乳 = "哺乳"
    分娩 = "分娩"
    休息 = "休息"
    治疗 = "治疗"
    淘汰 = "淘汰"

class PigHealthStatus(enum.Enum):
    健康 = "健康"
    待观察 = "待观察"
    治疗中 = "治疗中"
    隔离中 = "隔离中"

class AlertLevel(enum.Enum):
    紧急 = "紧急"
    重要 = "重要"
    一般 = "一般"

class AlertStatus(enum.Enum):
    未处理 = "未处理"
    处理中 = "处理中"
    已解决 = "已解决"
    已忽略 = "已忽略"

# 数据表定义
class PigHouse(Base):
    """猪舍表"""
    __tablename__ = "pig_houses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True)
    location = Column(String(100))
    capacity = Column(Integer)  # 最大容量
    current_count = Column(Integer, default=0)  # 当前数量
    manager = Column(String(50))  # 负责人
    temperature = Column(Float)  # 当前温度
    humidity = Column(Float)  # 当前湿度
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    pens = relationship("PigPen", back_populates="pig_house")

class PigPen(Base):
    """猪圈表"""
    __tablename__ = "pig_pens"
    
    id = Column(Integer, primary_key=True, index=True)
    pen_number = Column(String(20), unique=True, index=True)
    pig_house_id = Column(Integer, ForeignKey("pig_houses.id"))
    capacity = Column(Integer)  # 最大容量
    current_count = Column(Integer, default=0)
    type = Column(String(20))  # 圈舍类型：妊娠舍、分娩舍、保育舍等
    area = Column(Float)  # 面积(平方米)
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    pig_house = relationship("PigHouse", back_populates="pens")
    pigs = relationship("Pig", back_populates="pen")

class Pig(Base):
    """猪只表"""
    __tablename__ = "pigs"
    
    id = Column(Integer, primary_key=True, index=True)
    ear_tag = Column(String(50), unique=True, index=True)  # 耳标号
    sow_number = Column(String(50), unique=True, index=True, nullable=True)  # 母猪号
    parity = Column(Integer, default=0)  # 胎次
    birth_date = Column(DateTime)
    breed = Column(String(50))  # 品种
    gender = Column(String(10))  # 性别
    weight = Column(Float)
    backfat_thickness = Column(Float, nullable=True)  # 背膘厚度(mm)
    status = Column(String(20))
    pen_id = Column(Integer, ForeignKey("pig_pens.id"))
    health_status = Column(String(20), default="健康")
    entry_date = Column(DateTime, default=datetime.now)
    last_update = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    last_breeding_date = Column(DateTime, nullable=True)  # 最后配种日期
    pregnancy_days = Column(Integer, nullable=True)  # 妊娠天数
    notes = Column(Text, nullable=True)
    
    # 关系
    pen = relationship("PigPen", back_populates="pigs")
    feeding_records = relationship("FeedingRecord", back_populates="pig")
    health_records = relationship("HealthRecord", back_populates="pig")
    breeding_records = relationship("BreedingRecord", back_populates="pig")
    
    @property
    def current_pregnancy_days(self):
        """计算当前妊娠天数"""
        if self.status != "妊娠" or not self.last_breeding_date:
            return None
        delta = datetime.now() - self.last_breeding_date
        return delta.days
    
    def update_pregnancy_days(self):
        """更新妊娠天数"""
        if self.status == "妊娠" and self.last_breeding_date:
            delta = datetime.now() - self.last_breeding_date
            self.pregnancy_days = delta.days
        else:
            self.pregnancy_days = None
    
    def increment_parity(self):
        """增加胎次"""
        self.parity = (self.parity or 0) + 1
        return self.parity

class FeedingRecord(Base):
    """喂食记录表"""
    __tablename__ = "feeding_records"
    
    id = Column(Integer, primary_key=True, index=True)
    pig_id = Column(Integer, ForeignKey("pigs.id"))
    feed_time = Column(DateTime, default=datetime.now)
    feed_amount = Column(Float)  # 单位：kg
    duration = Column(Integer)   # 单位：分钟
    feed_type = Column(String(50))
    feed_status = Column(String(20), default="正常")
    automatic = Column(Boolean, default=True)
    feeder_number = Column(String(50), nullable=True)  # 下料器号，以ei-00开头
    
    # 关系
    pig = relationship("Pig", back_populates="feeding_records")

class FeedSetting(Base):
    """下料设置表"""
    __tablename__ = "feed_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    pen_id = Column(Integer, ForeignKey("pig_pens.id"))
    feed_type = Column(String(50))
    daily_amount = Column(Float)  # 单位：kg/天
    feeding_times = Column(Integer)  # 每天喂食次数
    time_slots = Column(String(200))  # 存储JSON格式的喂食时间段
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    special_instructions = Column(Text, nullable=True)

class HealthRecord(Base):
    """健康记录表"""
    __tablename__ = "health_records"
    
    id = Column(Integer, primary_key=True, index=True)
    pig_id = Column(Integer, ForeignKey("pigs.id"))
    record_date = Column(DateTime, default=datetime.now)
    temperature = Column(Float, nullable=True)  # 单位：摄氏度
    symptoms = Column(Text, nullable=True)
    diagnosis = Column(String(100), nullable=True)
    treatment = Column(Text, nullable=True)
    vet_name = Column(String(50), nullable=True)
    follow_up_date = Column(DateTime, nullable=True)
    
    # 关系
    pig = relationship("Pig", back_populates="health_records")

class BreedingRecord(Base):
    """繁育记录表"""
    __tablename__ = "breeding_records"
    
    id = Column(Integer, primary_key=True, index=True)
    pig_id = Column(Integer, ForeignKey("pigs.id"))
    breeding_date = Column(DateTime)
    expected_farrowing_date = Column(DateTime, nullable=True)
    actual_farrowing_date = Column(DateTime, nullable=True)
    total_born = Column(Integer, nullable=True)
    born_alive = Column(Integer, nullable=True)
    stillborn = Column(Integer, nullable=True)
    weaned = Column(Integer, nullable=True)
    weaning_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(20), default="进行中")  # 进行中, 已分娩, 已流产, 已取消
    
    # 关系
    pig = relationship("Pig", back_populates="breeding_records")
    
    def update_pig_status(self, db_session):
        """更新母猪状态和妊娠信息"""
        if not self.pig:
            return
            
        # 新增记录时
        if self.status == "进行中":
            self.pig.status = "妊娠"
            self.pig.last_breeding_date = self.breeding_date
            self.pig.update_pregnancy_days()
            
            # 预计分娩日期默认设置为配种日期+114天
            if not self.expected_farrowing_date and self.breeding_date:
                self.expected_farrowing_date = self.breeding_date + timedelta(days=114)
                
        # 已分娩
        elif self.status == "已分娩":
            self.pig.status = "哺乳"
            self.pig.last_breeding_date = None
            self.pig.pregnancy_days = None
            
            # 增加胎次
            self.pig.increment_parity()
            
        # 已流产或已取消
        elif self.status in ["已流产", "已取消"]:
            self.pig.status = "正常"
            self.pig.last_breeding_date = None
            self.pig.pregnancy_days = None
            
        db_session.add(self.pig)
        db_session.commit()

class EnvironmentRecord(Base):
    """猪舍环境记录表"""
    __tablename__ = "environment_records"
    
    id = Column(Integer, primary_key=True, index=True)
    pig_house_id = Column(Integer, ForeignKey("pig_houses.id"))
    record_time = Column(DateTime, default=datetime.now)
    temperature = Column(Float)  # 温度
    humidity = Column(Float)  # 湿度
    co2_level = Column(Float, nullable=True)  # 二氧化碳浓度
    ammonia_level = Column(Float, nullable=True)  # 氨气浓度
    air_quality_index = Column(Float, nullable=True)  # 空气质量指数
    notes = Column(Text, nullable=True)

class Alert(Base):
    """报警记录表"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_time = Column(DateTime, default=datetime.now)
    alert_type = Column(String(50))
    alert_level = Column(String(20))
    location = Column(String(50))
    details = Column(Text)
    duration = Column(Integer, nullable=True)  # 持续时间（分钟）
    status = Column(String(20), default="未处理")
    processed_by = Column(String(50), nullable=True)
    processed_time = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)

class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime, nullable=True)

# 初始化数据库
def init_db():
    Base.metadata.create_all(bind=engine)

# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 生成示例数据
def seed_data():
    # 初始化数据库
    init_db()
    
    # 创建会话
    db = SessionLocal()
    
    try:
        # 检查是否已有数据
        if db.query(PigHouse).count() > 0:
            print("数据库已有数据，跳过初始化")
            return
        
        # 添加猪舍
        pig_houses = []
        for i in range(1, 4):
            house = PigHouse(
                name=f"第{i}号猪舍",
                location=f"A区{i}号位置",
                capacity=i * 50,
                current_count=0,
                manager=random.choice(["张三", "李四", "王五", "赵六"]),
                temperature=random.uniform(20.0, 26.0),
                humidity=random.uniform(50.0, 70.0)
            )
            db.add(house)
            pig_houses.append(house)
        
        db.commit()
        
        # 添加猪圈
        pig_pens = []
        pen_types = ["妊娠舍", "分娩舍", "保育舍", "育成舍"]
        for house in pig_houses:
            for i in range(1, 6):  # 每个猪舍5个猪圈
                pen = PigPen(
                    pen_number=f"P{house.id}-{i}",
                    pig_house_id=house.id,
                    capacity=10,
                    current_count=0,
                    type=random.choice(pen_types),
                    area=random.uniform(20.0, 30.0)
                )
                db.add(pen)
                pig_pens.append(pen)
        
        db.commit()
        
        # 添加猪只
        pigs = []
        breeds = ["大白", "长白", "杜洛克", "皮特兰", "巴克夏"]
        statuses = ["正常", "妊娠", "哺乳", "分娩", "休息", "治疗"]
        health_statuses = ["健康", "待观察", "治疗中"]
        
        for i in range(1, 51):  # 创建50头猪
            birth_date = datetime.now() - timedelta(days=random.randint(365, 1095))  # 1-3岁
            pen = random.choice(pig_pens)
            pig = Pig(
                ear_tag=f"ET{10000+i}",
                birth_date=birth_date,
                breed=random.choice(breeds),
                gender="母",  # 母猪
                weight=random.uniform(150.0, 250.0),
                backfat_thickness=random.uniform(10.0, 25.0),  # 随机背膘厚度(mm)
                status=random.choice(statuses),
                pen_id=pen.id,
                health_status=random.choice(health_statuses),
                entry_date=datetime.now() - timedelta(days=random.randint(30, 300)),
                notes=f"测试母猪数据 #{i}"
            )
            db.add(pig)
            pigs.append(pig)
            
            # 更新猪圈当前数量
            pen.current_count += 1
            
            # 更新猪舍当前数量
            house = db.query(PigHouse).filter(PigHouse.id == pen.pig_house_id).first()
            house.current_count += 1
        
        db.commit()
        
        # 添加喂食记录
        feed_types = ["标准饲料", "妊娠饲料", "哺乳饲料", "恢复饲料"]
        feed_statuses = ["正常", "少食", "拒食", "过量"]
        
        for pig in pigs:
            # 为每头猪添加5-15条喂食记录
            for _ in range(random.randint(5, 15)):
                feed_time = datetime.now() - timedelta(days=random.randint(0, 30), 
                                                      hours=random.randint(0, 23),
                                                      minutes=random.randint(0, 59))
                record = FeedingRecord(
                    pig_id=pig.id,
                    feed_time=feed_time,
                    feed_amount=random.uniform(1.5, 4.0),
                    duration=random.randint(10, 45),
                    feed_type=random.choice(feed_types),
                    feed_status=random.choice(feed_statuses),
                    automatic=random.choice([True, True, True, False])  # 75%的几率是自动喂食
                )
                db.add(record)
        
        db.commit()
        
        # 添加下料设置
        for pen in pig_pens:
            # 创建喂食时间段，通常为每天3-4次
            feeding_times = random.randint(3, 4)
            time_slots = []
            for i in range(feeding_times):
                hour = 6 + (i * (12 // feeding_times))  # 从早上6点开始均匀分布
                time_slots.append({
                    "time": f"{hour:02d}:00",
                    "amount": round(random.uniform(1.0, 2.0), 1)
                })
            
            setting = FeedSetting(
                pen_id=pen.id,
                feed_type=random.choice(feed_types),
                daily_amount=sum(slot["amount"] for slot in time_slots),
                feeding_times=feeding_times,
                time_slots=json.dumps(time_slots),
                enabled=True,
                special_instructions=f"圈舍{pen.pen_number}的特殊饲养说明" if random.random() < 0.3 else None
            )
            db.add(setting)
        
        db.commit()
        
        # 添加健康记录
        symptoms_list = ["食欲不振", "发热", "咳嗽", "皮肤异常", "呼吸急促", "无症状"]
        diagnoses = ["正常", "轻微感染", "呼吸道疾病", "消化系统问题", "皮肤病", "产后综合症"]
        treatments = ["观察", "抗生素治疗", "补充营养", "隔离治疗", "无需治疗"]
        vets = ["张医生", "李医生", "王医生", "赵医生"]
        
        for pig in pigs:
            # 30%的猪有健康记录
            if random.random() < 0.3:
                for _ in range(random.randint(1, 3)):
                    record_date = datetime.now() - timedelta(days=random.randint(1, 90))
                    symptom = random.choice(symptoms_list)
                    diagnosis = random.choice(diagnoses)
                    treatment = random.choice(treatments)
                    
                    record = HealthRecord(
                        pig_id=pig.id,
                        record_date=record_date,
                        temperature=random.uniform(37.5, 40.0) if symptom != "无症状" else random.uniform(38.0, 39.0),
                        symptoms=symptom if symptom != "无症状" else None,
                        diagnosis=diagnosis if diagnosis != "正常" else None,
                        treatment=treatment if treatment != "无需治疗" else None,
                        vet_name=random.choice(vets),
                        follow_up_date=record_date + timedelta(days=random.randint(3, 14)) if treatment != "无需治疗" else None
                    )
                    db.add(record)
        
        db.commit()
        
        # 添加繁育记录
        for pig in pigs:
            # 只有状态为妊娠、哺乳或分娩的猪有繁育记录
            if pig.status in ["妊娠", "哺乳", "分娩"]:
                breeding_date = datetime.now() - timedelta(days=random.randint(90, 150))
                expected_farrowing_date = breeding_date + timedelta(days=114)  # 猪的妊娠期约为114天
                
                # 如果预产期已过，则有实际分娩日期和仔猪数据
                has_farrowed = expected_farrowing_date < datetime.now()
                
                record = BreedingRecord(
                    pig_id=pig.id,
                    breeding_date=breeding_date,
                    expected_farrowing_date=expected_farrowing_date,
                    actual_farrowing_date=expected_farrowing_date + timedelta(days=random.randint(-2, 2)) if has_farrowed else None,
                    total_born=random.randint(8, 15) if has_farrowed else None,
                    born_alive=random.randint(7, 14) if has_farrowed else None,
                    stillborn=random.randint(0, 2) if has_farrowed else None,
                    weaned=random.randint(6, 12) if pig.status == "哺乳" and has_farrowed else None,
                    weaning_date=expected_farrowing_date + timedelta(days=21) if pig.status == "哺乳" and has_farrowed else None,
                    notes=f"正常繁育记录 #{pig.id}"
                )
                db.add(record)
        
        db.commit()
        
        # 添加环境记录
        for house in pig_houses:
            # 添加过去14天的环境记录，每天4条
            for day in range(14):
                for hour in [6, 12, 18, 0]:  # 每天6点、12点、18点、0点记录
                    record_time = datetime.now().replace(hour=hour, minute=0, second=0, microsecond=0) - timedelta(days=day)
                    
                    record = EnvironmentRecord(
                        pig_house_id=house.id,
                        record_time=record_time,
                        temperature=random.uniform(18.0, 28.0),
                        humidity=random.uniform(45.0, 75.0),
                        co2_level=random.uniform(400.0, 1200.0),
                        ammonia_level=random.uniform(5.0, 25.0),
                        air_quality_index=random.uniform(50.0, 150.0),
                        notes=None
                    )
                    db.add(record)
        
        db.commit()
        
        # 添加报警记录
        alert_types = ["温度异常", "采食异常", "健康异常", "设备故障", "环境异常"]
        alert_levels = ["紧急", "重要", "一般"]
        locations = [f"猪舍{i}" for i in range(1, 4)] + [f"圈舍{pen.pen_number}" for pen in pig_pens]
        statuses = ["未处理", "处理中", "已解决", "已忽略"]
        
        for _ in range(30):  # 创建30条警报
            alert_time = datetime.now() - timedelta(days=random.randint(0, 10), 
                                                  hours=random.randint(0, 23),
                                                  minutes=random.randint(0, 59))
            alert_type = random.choice(alert_types)
            alert_level = random.choice(alert_levels)
            location = random.choice(locations)
            status = random.choice(statuses)
            
            # 根据警报类型生成详情
            if alert_type == "温度异常":
                details = f"{location}温度异常，当前温度{random.uniform(15.0, 35.0):.1f}°C，正常范围：20-26°C"
            elif alert_type == "采食异常":
                details = f"{location}采食异常，今日采食量减少{random.randint(20, 50)}%"
            elif alert_type == "健康异常":
                details = f"{location}发现母猪健康异常，可能症状：{random.choice(symptoms_list)}"
            elif alert_type == "设备故障":
                details = f"{location}设备故障，需要维修"
            else:
                details = f"{location}环境指标异常，请检查"
            
            processed = status in ["已解决", "已忽略"]
            
            alert = Alert(
                alert_time=alert_time,
                alert_type=alert_type,
                alert_level=alert_level,
                location=location,
                details=details,
                duration=random.randint(10, 120),
                status=status,
                processed_by="管理员" if processed else None,
                processed_time=alert_time + timedelta(hours=random.randint(1, 8)) if processed else None,
                resolution_notes=f"已处理{alert_type}问题" if processed else None
            )
            db.add(alert)
        
        db.commit()
        
        # 创建一个测试用户
        from app.utils.password import get_password_hash
        test_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("password"),
            is_admin=True
        )
        db.add(test_user)
        db.commit()
        
        print("数据库初始化完成！")
        
    except Exception as e:
        print(f"初始化数据库时出错: {e}")
        db.rollback()
    finally:
        db.close() 