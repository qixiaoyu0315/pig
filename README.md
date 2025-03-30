# 母猪管理系统

一个使用FastAPI和Bootstrap开发的母猪管理系统，包含用户登录、注册和基本的管理界面。

## 功能特点

- 用户注册和登录
- 安全的密码存储
- 响应式界面设计
- 使用SQLite数据库存储数据

## 安装

1. 克隆仓库
```
git clone https://github.com/qixiaoyu0315/pig.git
cd pig-management
```

2. 安装依赖
```
pip install -r requirements.txt
```

3. 运行应用
```
python run.py
```

4. 打开浏览器访问 `http://localhost:8000`

## 技术栈

- FastAPI - 后端框架
- SQLAlchemy - ORM
- SQLite - 数据库
- Bootstrap 5 - 前端框架
- Jinja2 - 模板引擎

## 项目结构

```
app/
├── __init__.py
├── main.py               # 应用入口点
├── database.py           # 数据库配置
├── utils.py              # 工具函数
├── models/               # 数据模型
│   └── user.py
├── schemas/              # Pydantic模型
│   └── user.py
├── routes/               # 路由处理
│   ├── __init__.py
│   ├── auth.py           # 认证相关路由
│   └── home.py           # 首页路由
├── static/               # 静态文件
│   ├── css/
│   ├── js/
│   └── img/
└── templates/            # HTML模板
    ├── base.html
    ├── login.html
    ├── register.html
    └── home.html
``` 