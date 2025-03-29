import uvicorn
import os
from app.db_init import initialize_database

def run_app():
    # 初始化数据库
    initialize_database()
    
    # 启动应用
    uvicorn.run("app.main:app", host="0.0.0.0", port=8002, reload=True)

if __name__ == "__main__":
    run_app() 