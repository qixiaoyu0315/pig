import sqlite3
import os
import random

# 获取数据库文件路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'pig_management.db')
parent_db_path = os.path.join(os.path.dirname(BASE_DIR), 'pig_management.db')

def migrate_database():
    """手动迁移数据库，添加背膘厚度列"""
    # 检查两个可能的数据库位置
    real_db_path = db_path if os.path.exists(db_path) else parent_db_path
    
    print(f"准备迁移数据库: {real_db_path}")
    
    # 检查数据库是否存在
    if not os.path.exists(real_db_path):
        print("数据库文件不存在，无需迁移")
        return
    
    conn = None
    try:
        # 连接数据库
        conn = sqlite3.connect(real_db_path)
        cursor = conn.cursor()
        
        # 检查列是否存在
        cursor.execute("PRAGMA table_info(pigs)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'backfat_thickness' in columns:
            print("背膘厚度列已存在，无需添加")
        else:
            print("添加背膘厚度列到pigs表")
            # 添加新列
            cursor.execute("ALTER TABLE pigs ADD COLUMN backfat_thickness FLOAT")
            
            # 为现有数据添加随机背膘厚度
            cursor.execute("SELECT id FROM pigs")
            pig_ids = [row[0] for row in cursor.fetchall()]
            
            for pig_id in pig_ids:
                backfat_thickness = random.uniform(10.0, 25.0)
                cursor.execute(
                    "UPDATE pigs SET backfat_thickness = ? WHERE id = ?", 
                    (backfat_thickness, pig_id)
                )
            
            print(f"成功为 {len(pig_ids)} 头猪更新了背膘厚度数据")
            
            # 提交更改
            conn.commit()
            print("数据库迁移完成")
    except sqlite3.Error as e:
        print(f"数据库操作错误: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_database() 