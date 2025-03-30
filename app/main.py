from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

from app.routes import home, auth, pig
from app.db_init import initialize_database, update_pig_backfat

app = FastAPI(
    title="母猪管理系统",
    description="用于管理养猪场母猪繁育、饲养和健康状况的系统",
    version="1.0.0"
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 包含路由
app.include_router(auth.router)
app.include_router(home.router)
app.include_router(pig.router)

# 初始化数据库
@app.on_event("startup")
async def startup_event():
    # 检查数据库文件是否存在
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pig_management.db")
    if not os.path.exists(db_path):
        # 初始化数据库并填充示例数据
        initialize_database()
    else:
        print("数据库已有数据，跳过初始化")
        # 确保所有猪只都有背膘厚度数据
        update_pig_backfat()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
