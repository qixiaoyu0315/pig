from app.models.database import init_db, seed_data

def initialize_database():
    """初始化数据库并填充示例数据"""
    # 创建数据库表
    init_db()
    
    # 添加示例数据
    seed_data()
    
if __name__ == "__main__":
    initialize_database() 