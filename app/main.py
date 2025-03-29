from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routes import auth, home, pig
from app.database import engine
from app.models import user

# 创建数据库表
user.Base.metadata.create_all(bind=engine)

app = FastAPI(title="母猪管理系统")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 包含路由
app.include_router(auth.router, tags=["auth"])
app.include_router(home.router, tags=["home"])
app.include_router(pig.router, tags=["pig"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
