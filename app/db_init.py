from app.models.database import init_db, seed_data, get_db
from sqlalchemy.orm import Session
import random
from app.models.database import Pig

def initialize_database():
    """初始化数据库并填充示例数据"""
    # 创建数据库表
    init_db()
    
    # 添加示例数据
    seed_data()
    
    # 更新现有猪只的背膘厚度
    update_pig_backfat()

def update_pig_backfat():
    """为现有猪只添加随机背膘厚度数据"""
    db = next(get_db())
    try:
        # 获取所有背膘厚度为空的猪只
        pigs = db.query(Pig).filter(Pig.backfat_thickness == None).all()
        
        if not pigs:
            print("所有猪只已有背膘厚度数据")
            return
        
        print(f"正在为 {len(pigs)} 头猪只添加背膘厚度数据...")
        
        # 为每头猪添加随机背膘厚度
        for pig in pigs:
            pig.backfat_thickness = random.uniform(10.0, 25.0)  # 随机背膘厚度(mm)
        
        db.commit()
        print("背膘厚度数据更新完成！")
        
    except Exception as e:
        print(f"更新背膘厚度数据时出错: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    initialize_database() 