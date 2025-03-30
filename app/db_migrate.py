from sqlalchemy import create_engine, MetaData, Table, Column, Integer, DateTime, String, text
from sqlalchemy.sql import select, update
import os
import sys
from datetime import datetime, timedelta
import sys

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import engine, Base, get_db, init_db, Pig, BreedingRecord

def migrate_database():
    """迁移数据库结构和数据"""
    print("开始数据库迁移...")
    
    # 1. 添加新字段前先备份数据库
    backup_database()
    
    # 2. 添加新字段到数据库表
    add_new_columns()
    
    # 3. 更新母猪妊娠数据
    update_pregnancy_data()
    
    print("数据库迁移完成")

def backup_database():
    """备份数据库"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pig_management.db")
    backup_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                          f"pig_management_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
    
    if os.path.exists(db_path):
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"数据库已备份到 {backup_path}")

def add_new_columns():
    """添加新字段到数据库表"""
    try:
        # 创建元数据对象
        metadata = MetaData()
        
        # 反射现有表
        pigs_table = Table('pigs', metadata, autoload_with=engine)
        breeding_records_table = Table('breeding_records', metadata, autoload_with=engine)
        
        # 获取连接
        with engine.connect() as conn:
            # 检查字段是否已存在，不存在则添加
            # 添加母猪表新字段
            if 'last_breeding_date' not in pigs_table.columns:
                print("添加 last_breeding_date 字段...")
                conn.execute(text('ALTER TABLE pigs ADD COLUMN last_breeding_date DATETIME'))
                conn.commit()
            
            if 'pregnancy_days' not in pigs_table.columns:
                print("添加 pregnancy_days 字段...")
                conn.execute(text('ALTER TABLE pigs ADD COLUMN pregnancy_days INTEGER'))
                conn.commit()
            
            # 添加繁育记录表新字段
            if 'status' not in breeding_records_table.columns:
                print("添加 status 字段...")
                conn.execute(text('ALTER TABLE breeding_records ADD COLUMN status VARCHAR(20) DEFAULT "进行中"'))
                conn.commit()
            
            print("新字段添加完成")
        
    except Exception as e:
        print(f"添加新字段时出错: {e}")
        raise

def update_pregnancy_data():
    """更新母猪妊娠数据"""
    try:
        db = next(get_db())
        
        # 1. 获取所有状态为"妊娠"的母猪
        pregnant_pigs = db.query(Pig).filter(Pig.status == "妊娠").all()
        print(f"找到 {len(pregnant_pigs)} 头妊娠母猪需要更新")
        
        # 2. 查找每头母猪最新的繁育记录，更新last_breeding_date
        for pig in pregnant_pigs:
            latest_breeding = db.query(BreedingRecord).filter(
                BreedingRecord.pig_id == pig.id,
                BreedingRecord.actual_farrowing_date.is_(None)
            ).order_by(BreedingRecord.breeding_date.desc()).first()
            
            if latest_breeding:
                # 设置最后配种日期
                pig.last_breeding_date = latest_breeding.breeding_date
                
                # 更新妊娠天数
                pig.update_pregnancy_days()
                
                # 设置繁育记录状态
                latest_breeding.status = "进行中"
                
                db.add(pig)
                db.add(latest_breeding)
        
        # 3. 获取所有状态为"哺乳"的母猪
        nursing_pigs = db.query(Pig).filter(Pig.status == "哺乳").all()
        print(f"找到 {len(nursing_pigs)} 头哺乳母猪需要更新")
        
        # 4. 更新哺乳母猪相关的繁育记录状态
        for pig in nursing_pigs:
            latest_breeding = db.query(BreedingRecord).filter(
                BreedingRecord.pig_id == pig.id,
                BreedingRecord.actual_farrowing_date.isnot(None)
            ).order_by(BreedingRecord.actual_farrowing_date.desc()).first()
            
            if latest_breeding:
                latest_breeding.status = "已分娩"
                db.add(latest_breeding)
        
        db.commit()
        print("妊娠数据更新完成")
        
    except Exception as e:
        db.rollback()
        print(f"更新妊娠数据时出错: {e}")
        raise

if __name__ == "__main__":
    migrate_database() 