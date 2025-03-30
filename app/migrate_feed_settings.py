import os
import sys
import sqlite3
import random
from datetime import datetime, timedelta
import shutil
import json

# 添加项目根路径到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import engine, Base, SessionLocal, Pig, FeedSetting, FeedCalculation

def create_backup():
    """创建数据库备份"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pig_management.db')
    backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
        f'pig_management_backup_feed_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
    
    if os.path.exists(db_path):
        shutil.copy2(db_path, backup_path)
        print(f"数据库已备份到: {backup_path}")
    else:
        print("未找到数据库文件，跳过备份")

def add_column_if_not_exists(conn, table, column, column_type):
    """检查列是否存在，如果不存在则添加"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in cursor.fetchall()]
    
    if column not in columns:
        print(f"添加 {column} 列到 {table} 表")
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
        conn.commit()
        return True
    else:
        print(f"{column} 列已存在于 {table} 表中")
        return False

def create_feed_calculations_table():
    """创建feed_calculations表（如果不存在）"""
    # 使用SQLAlchemy的元数据创建表
    Base.metadata.create_all(engine)
    print("确保feed_calculations表存在")

def init_feed_settings_data():
    """初始化feed_settings表的新字段数据"""
    db = SessionLocal()
    try:
        # 查询所有设置记录
        settings = db.query(FeedSetting).all()
        print(f"找到 {len(settings)} 条feed_settings记录需要初始化")
        
        # 查询所有猪只
        pigs = db.query(Pig).all()
        
        # 为每条记录初始化数据
        for i, setting in enumerate(settings):
            # 生成下料器号，格式为ei-00加三位数字
            if not setting.feeder_number:
                setting.feeder_number = f"ei-00{random.randint(100, 999)}"
            
            # 随机关联一头猪（如果不是所有圈舍的设置）
            if not setting.pig_id and pigs and i < len(pigs):
                setting.pig_id = pigs[i].id
                
            # 设置采食量相关数据
            if not setting.predicted_amount:
                setting.predicted_amount = round(random.uniform(10.0, 18.0), 1)
                
            if not setting.actual_amount:
                # 实际采食量在预测的80%-120%范围内
                if setting.predicted_amount:
                    base = setting.predicted_amount
                else:
                    base = 15.0
                setting.actual_amount = round(base * random.uniform(0.8, 1.2), 1)
                
            if not setting.set_amount:
                setting.set_amount = round(setting.daily_amount, 1)
                
            if not setting.last_setting_time:
                # 最近3-14天内随机一个时间
                days_ago = random.randint(3, 14)
                setting.last_setting_time = datetime.now() - timedelta(days=days_ago)
            
            db.add(setting)
            
        db.commit()
        print("feed_settings数据初始化完成")
        
        # 为每个设置添加计算记录
        init_feed_calculations(db)
        
    except Exception as e:
        db.rollback()
        print(f"初始化feed_settings数据失败: {e}")
    finally:
        db.close()

def init_feed_calculations(db):
    """初始化feed_calculations表数据"""
    try:
        # 查询所有设置记录
        settings = db.query(FeedSetting).all()
        
        # 为每个设置添加1-3条计算记录
        for setting in settings:
            for _ in range(random.randint(1, 3)):
                # 随机生成各种因子
                weight_factor = round(random.uniform(0.8, 1.2), 2)
                health_factor = round(random.uniform(0.9, 1.1), 2)
                temperature_factor = round(random.uniform(0.9, 1.1), 2)
                stage_factor = round(random.uniform(0.8, 1.2), 2)
                
                # 计算公式示例
                formula = f"base_amount * {weight_factor} * {health_factor} * {temperature_factor} * {stage_factor}"
                
                # 基础用量和调整后用量
                base_amount = setting.daily_amount or 15.0
                adjusted_amount = round(base_amount * weight_factor * health_factor * temperature_factor * stage_factor, 1)
                
                # 计算日期（过去30天内随机）
                days_ago = random.randint(1, 30)
                calc_date = datetime.now() - timedelta(days=days_ago)
                
                # 创建计算记录
                calculation = FeedCalculation(
                    feed_setting_id=setting.id,
                    calculation_date=calc_date,
                    weight_factor=weight_factor,
                    health_factor=health_factor,
                    temperature_factor=temperature_factor,
                    stage_factor=stage_factor,
                    calculation_formula=formula,
                    base_amount=base_amount,
                    adjusted_amount=adjusted_amount,
                    notes=f"基于母猪状态的自动计算"
                )
                
                db.add(calculation)
        
        db.commit()
        print("feed_calculations数据初始化完成")
        
    except Exception as e:
        db.rollback()
        print(f"初始化feed_calculations数据失败: {e}")

def migrate_feed_settings():
    """迁移feed_settings表结构和数据"""
    print("开始feed_settings表迁移...")
    
    # 创建数据库备份
    create_backup()
    
    # 连接数据库
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pig_management.db')
    conn = sqlite3.connect(db_path)
    
    # 添加新字段到feed_settings表
    add_column_if_not_exists(conn, "feed_settings", "feeder_number", "TEXT")
    add_column_if_not_exists(conn, "feed_settings", "pig_id", "INTEGER")
    add_column_if_not_exists(conn, "feed_settings", "predicted_amount", "REAL")
    add_column_if_not_exists(conn, "feed_settings", "actual_amount", "REAL")
    add_column_if_not_exists(conn, "feed_settings", "set_amount", "REAL")
    add_column_if_not_exists(conn, "feed_settings", "last_setting_time", "TIMESTAMP")
    
    # 关闭连接
    conn.close()
    
    # 创建feed_calculations表
    create_feed_calculations_table()
    
    # 初始化feed_settings表数据
    init_feed_settings_data()
    
    print("feed_settings表迁移完成")

if __name__ == "__main__":
    migrate_feed_settings() 