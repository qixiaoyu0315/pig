import os
import sqlite3
import random

def init_feeder_numbers():
    """为已有的喂食记录初始化下料器号"""
    # 获取数据库路径
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pig_management.db')
    
    # 连接到数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 查询所有没有下料器号的喂食记录
        cursor.execute("SELECT id FROM feeding_records WHERE feeder_number IS NULL")
        records = cursor.fetchall()
        
        print(f"找到 {len(records)} 条需要初始化下料器号的记录")
        
        # 为每条记录生成一个下料器号并更新
        for record_id in records:
            # 生成下料器号 ei-00 开头加三位数字
            feeder_num = f"ei-00{random.randint(100, 999)}"
            cursor.execute("UPDATE feeding_records SET feeder_number = ? WHERE id = ?", 
                          (feeder_num, record_id[0]))
        
        conn.commit()
        print("下料器号初始化完成")
    except Exception as e:
        conn.rollback()
        print(f"初始化下料器号失败: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_feeder_numbers() 