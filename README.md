# 母猪管理系统

一个用于养猪场管理的综合系统，使用FastAPI和Bootstrap开发，为养猪场管理人员提供母猪繁育、饲养和健康状况的高效管理工具。

## 核心功能

- **母猪管理**：记录和管理所有母猪的基本信息，包括耳标号、品种、体重、背膘厚度等
- **饲喂管理**：跟踪每日饲料消耗，设置自动饲喂计划
- **健康监控**：记录健康检查结果，跟踪治疗过程
- **繁育记录**：管理配种、分娩和断奶等繁育信息
- **环境监测**：记录和展示猪舍温度、湿度等环境参数
- **报警系统**：当环境参数或健康状况异常时发出报警
- **数据可视化**：使用ECharts提供多种图表，直观展示各类数据

## 数据可视化功能

首页集成多种数据图表展示：
- 近7天饲料消耗趋势折线图
- 猪只状态分布饼图
- 背膘厚度分布柱状图
- 近24小时环境数据折线图（温度和湿度）

## 数据模型

系统包含以下主要数据模型：
- **猪舍(PigHouse)**：管理多个猪圈的基本单位
- **猪圈(PigPen)**：母猪所在的具体位置
- **母猪(Pig)**：记录母猪的全部信息，包括基本信息、状态、健康状况、背膘厚度等
- **饲喂记录(FeedingRecord)**：记录每次饲喂的详细信息
- **健康记录(HealthRecord)**：记录健康检查和治疗情况
- **繁育记录(BreedingRecord)**：记录配种、分娩和断奶等繁育相关信息
- **环境记录(EnvironmentRecord)**：记录猪舍环境参数变化
- **报警(Alert)**：记录系统产生的各类报警信息
- **用户(User)**：管理系统用户的权限和信息

## 技术栈

- **后端**：
  - FastAPI - 高性能Web框架
  - SQLAlchemy - ORM工具
  - SQLite - 轻量级数据库
  - Pydantic - 数据验证

- **前端**：
  - Bootstrap 5 - 响应式UI框架
  - ECharts - 数据可视化图表库
  - JavaScript - 客户端交互
  - Jinja2 - 模板引擎

## 功能页面

- **首页**：提供系统概览和数据可视化
- **母猪管理**：提供完整的CRUD功能，支持分页和筛选
- **采食信息**：跟踪和管理饲料消耗数据
- **下料设置**：管理自动饲喂系统的配置
- **每日汇总**：提供每日数据的汇总展示
- **报警信息**：展示和处理系统报警
- **控制界面**：提供对设备的直接控制功能

## 安装与使用

1. 克隆仓库
```
git clone https://github.com/qixiaoyu0315/pig.git
cd pig-management
```

2. 创建并激活虚拟环境
```
python -m venv venv
source venv/bin/activate  # 在Windows上使用 venv\Scripts\activate
```

3. 安装依赖
```
pip install -r requirements.txt
```

4. 运行应用
```
python run.py
```

5. 打开浏览器访问 `http://localhost:8002/login`

## 登录信息

- **用户名**: admin
- **密码**: password

## 项目结构
- FastAPI - 后端框架
- SQLAlchemy - ORM
- SQLite - 数据库
- Bootstrap 5 - 前端框架
- Jinja2 - 模板引擎
```
app/
├── __init__.py
├── db_init.py            # 数据库初始化
├── db_migrate.py         # 数据库迁移
├── main.py               # 应用入口点
├── models/               # 数据模型
│   └── database.py       # 所有数据表定义
├── routes/               # 路由处理
│   ├── __init__.py
│   ├── auth.py           # 认证相关路由
│   ├── home.py           # 首页路由
│   └── pig.py            # 猪只管理相关路由
├── static/               # 静态文件
│   ├── css/
│   ├── js/
│   └── img/
└── templates/            # HTML模板
    ├── admin_layout.html # 管理界面布局
    ├── base.html         # 基础布局
    ├── home.html         # 首页
    ├── login.html        # 登录页
    ├── register.html     # 注册页
    └── pig/              # 猪只管理相关页面
        ├── management.html
        ├── feeding.html
        ├── daily_summary.html
        ├── feeding_settings.html
        ├── alerts.html
        └── control.html
```

## 未来计划

- 增加更多统计分析功能
- 添加用户权限管理
- 开发移动端应用
- 集成物联网设备实时监控
- 添加批量导入导出功能

## 贡献

欢迎提交问题报告和功能请求。如果您想贡献代码，请先打开一个issue讨论您想要更改的内容。

## 许可证

[MIT](LICENSE) 