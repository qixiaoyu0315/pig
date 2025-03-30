import sqlite3
import os

def add_feeder_number_column():
    """添加下料器号字段到feeding_records表"""
    # 获取数据库路径
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pig_management.db')
    
    # 连接到数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查字段是否存在
        cursor.execute("PRAGMA table_info(feeding_records)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'feeder_number' not in columns:
            print("添加feeder_number字段到feeding_records表")
            cursor.execute("ALTER TABLE feeding_records ADD COLUMN feeder_number TEXT")
            conn.commit()
            print("字段添加成功")
        else:
            print("feeder_number字段已存在")
            
    except Exception as e:
        print(f"添加字段失败: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_feeder_number_column() 