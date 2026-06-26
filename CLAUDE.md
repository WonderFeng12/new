# 嘉元瑞通工厂管理系统

## 项目概述

嘉元瑞通工厂订单管理系统，分三期实施。第1期为 Web 端订单录入系统，已实现从订单录入→客户确认→合同生成→工艺单下发的完整闭环。

- **第1期（已完成）**：Web 页面订单录入系统
- **第2期（规划中）**：微信小程序 — 客户自主选花型、下单
- **第3期（规划中）**：工厂内部协同 — 库存管理、信息共享

## 技术栈

| 层 | 技术 |
|---|------|
| 后端框架 | Python FastAPI + SQLAlchemy ORM |
| 数据库 | MySQL 8.0+（开发环境 MySQL 9.6） |
| 前端框架 | Vue 3 (Composition API) + Element Plus |
| 构建工具 | Vite |
| 状态管理 | Pinia |
| 路由 | Vue Router 4 |
| 图片处理 | Pillow（自动压缩） |
| PDF 生成 | WeasyPrint（可选依赖） |
| 认证 | JWT (python-jose) + bcrypt |
| 部署 | Docker + docker-compose |

## 项目结构

```
/
├── CLAUDE.md                  # 本文件
├── Dockerfile                 # 后端 Docker 镜像
├── docker-compose.yml         # 一键部署（MySQL + 后端 + 前端）
├── .dockerignore
├── backend/
│   ├── Dockerfile.dev         # 开发用（热重载）
│   ├── requirements.txt
│   ├── main.py                # 启动入口
│   ├── init_db.py             # 建表脚本
│   ├── seed.py                # 测试数据
│   ├── uploads/               # 上传文件存储（gitignored）
│   └── app/
│       ├── main.py            # FastAPI 入口，注册路由
│       ├── config.py          # 配置（数据库、JWT、图片压缩参数）
│       ├── database.py        # 数据库连接（SQLAlchemy engine/session）
│       ├── dependencies.py    # 依赖注入（get_current_user, require_role）
│       ├── models/            # SQLAlchemy 模型
│       │   ├── mixins.py      # TimestampMixin, SoftDeleteMixin, AuditMixin
│       │   ├── user.py
│       │   ├── customer.py
│       │   ├── spec.py
│       │   ├── contract.py
│       │   ├── contract_item.py
│       │   ├── confirm_image.py
│       │   └── process_sheet.py
│       ├── schemas/           # Pydantic 校验/序列化
│       │   ├── user.py
│       │   ├── customer.py
│       │   ├── spec.py
│       │   ├── contract.py
│       │   ├── contract_item.py
│       │   ├── confirm_image.py
│       │   └── process_sheet.py
│       ├── services/          # 业务逻辑层
│       │   ├── auth.py        # 认证、JWT 生成/验证
│       │   ├── customer.py    # 客户 CRUD + 编号生成
│       │   ├── spec.py        # 规格 CRUD + 描述自动生成
│       │   ├── contract.py    # 合同 CRUD + 金额计算 + 权限过滤
│       │   ├── confirm_image.py # 确认图版本控制
│       │   └── process_sheet.py # 工艺单 CRUD + 下推 + 版本校验
│       ├── api/               # 路由层
│       │   ├── auth.py
│       │   ├── customers.py
│       │   ├── specs.py
│       │   ├── contracts.py
│       │   ├── process_sheets.py
│       │   └── upload.py
│       └── utils/
│           ├── image_compress.py # Pillow 图片压缩
│           └── pdf_generator.py  # WeasyPrint PDF 生成
├── frontend/
│   ├── Dockerfile             # 多阶段构建（node build → nginx serve）
│   ├── nginx.conf             # 反向代理 /api/ → backend
│   └── src/
│       ├── main.js            # Vue 入口，注册 ElementPlus/Pinia/Router
│       ├── App.vue            # 主布局（侧边栏 + 路由视图）
│       ├── api/               # API 调用封装
│       │   ├── index.js       # axios 实例（拦截器、Bearer Token）
│       │   ├── auth.js
│       │   ├── customer.js
│       │   ├── spec.js
│       │   ├── contract.js
│       │   ├── upload.js
│       │   └── processSheet.js
│       ├── store/
│       │   └── user.js        # Pinia store（token、user、role）
│       ├── router/
│       │   └── index.js       # 路由配置 + 守卫
│       ├── components/
│       │   └── ImageUploader.vue # 多文件上传 + 压缩率显示
│       └── views/
│           ├── login/Login.vue
│           ├── dashboard/Dashboard.vue
│           ├── customer/CustomerList.vue
│           ├── spec/SpecList.vue
│           ├── contract/
│           │   ├── ContractList.vue
│           │   ├── ContractForm.vue
│           │   └── ContractDetail.vue
│           └── processSheet/
│               ├── SheetList.vue
│               └── SheetDetail.vue
```

## 数据库模型

### 用户 (user)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | |
| username | VARCHAR(100) UNIQUE | 登录名 |
| password_hash | VARCHAR(200) | bcrypt 哈希 |
| display_name | VARCHAR(100) | 显示名 |
| role | ENUM('业务员','销售经理','生产专员') | 角色 |
| is_active | BOOLEAN | 是否启用 |
| is_deleted | BOOLEAN | 软删除 |

### 客户 (customer) — 含 TimestampMixin + SoftDeleteMixin + AuditMixin
| 字段 | 类型 | 说明 |
|------|------|------|
| customer_no | VARCHAR(50) UNIQUE | "C00001" 格式自动生成 |
| name | VARCHAR(200) | 客户名称 |
| contact | VARCHAR(100) | 联系人 |
| phone | VARCHAR(50) | 电话 |
| address | TEXT | 地址 |

### 规格 (spec) — 含 AuditMixin
| 字段 | 类型 | 说明 |
|------|------|------|
| length | VARCHAR(50) | 毛毯尺寸-长，如 200 |
| width | VARCHAR(50) | 毛毯尺寸-宽，如 240 |
| weight | VARCHAR(50) | 毛毯重量，如 4KG |
| layer_type | ENUM('单层','双层','复合') | 单双层 |
| splice_method | VARCHAR(100) | 拼接方式如 对拼接 |
| spec_name | VARCHAR(200) | 自动生成：`长*宽/重量/层类型` 如 `200*240/4KG/单层` |
| spec_description | TEXT | 自动生成，同 spec_name |

### 合同 (contract) — 含 TimestampMixin + SoftDeleteMixin + AuditMixin
包含字段：contract_no, customer_id(FK), contract_date, spec_id(FK), spec_description, is_pressed, packaging_type, delivery_date, binding_material/width/color_no, tech_note_1~10(TEXT), accessory_desc/size/qty_1~6, pack_note_1~5, box_note_1~3, emboss_model, total_amount(DECIMAL 12,2)

状态字段：
- **status**: ENUM('草稿','保存','已下发')，默认草稿
- **is_pushed_down**: BOOLEAN 是否已下推工艺单
- **push_down_sheet_id**: INT 关联工艺单 ID
- **latest_confirm_version**: INT 最新确认图版本号

### 合同行项目 (contract_item)
| 字段 | 说明 |
|------|------|
| line_no | 行号 |
| unit_price / qty / amount | 价格信息（amount = unit_price × qty）|
| pattern_code | 花型编号 |
| color_a / color_b | A/B 面颜色 |
| image_a_1~3 / image_b_1~3 | A/B 面图片路径（最多各3张）|
| remark | 备注 |

### 确认图版本 (confirm_image)
| 字段 | 说明 |
|------|------|
| contract_id(FK) | 关联合同 |
| version_no | 版本号，从1递增 |
| generated_at / generated_by | 生成时间/人 |
| change_log | 修改内容摘要 |
| is_confirmed / confirmed_at / confirmed_by | 客户确认信息 |
| image_path | 确认图路径 |
| contract_snapshot(JSON) | 生成时的合同快照 |

### 工艺单 (process_sheet) — 含 TimestampMixin + SoftDeleteMixin + AuditMixin
| 字段 | 说明 |
|------|------|
| contract_id(FK) | 关联合同 |
| sheet_no | 工艺单号，系统生成 "GY2026060001" |
| confirm_version_no | 基于合同的确认图版本号 |
| confirm_image_id(FK) | 关联确认图版本记录 |
| status | ENUM('草稿','保存','已下发') |

> 工艺单的详细内容（客户、规格、包边、行项目等）从关联合同读取。

## 状态机

### 合同
```
草稿 → (客户确认) → 保存 → (下推工艺单) → 已下发
```
- **草稿**: 可编辑、可生成确认图、可软删除
- **保存**: 客户已确认、不可编辑、可下推工艺单
- **已下发**: 工艺单已下发、不可删除

### 工艺单
```
草稿 → (确认) → 保存 → (下发) → 已下发
```
- **草稿**: 可编辑、可删除
- **保存**: 不可编辑、可下发
- **已下发**: 发至车间、不可删除

## 业务规则

| ID | 规则 | 实现位置 |
|----|------|---------|
| B001 | 合同录入时，规格不存在则自动创建并提示 | contract service |
| B002 | 合同草稿可修改、可反复生成确认图 | contract service |
| B003 | 确认图版本号每次+1，含时间戳和修改日志 | confirm_image service |
| B004 | 客户确认后合同变为「保存」 | confirm_image service → mark_confirmed |
| B005 | 合同保存后才可下推工艺单 | process_sheet service |
| B006 | 一个合同只能下推一次 | process_sheet service (is_pushed_down 检查) |
| B007 | 工艺单下发前校验合同版本是否为最新 | process_sheet service → dispatch |
| B008 | 工艺单下发 → 合同自动变为「已下发」 | process_sheet service |
| B009 | 所有表软删除，已下发数据不可删除 | 各 service |
| B010 | 上传图片强制压缩（1920px, 85% quality） | image_compress utils |
| B011 | 业务员只能查看/编辑自己创建的合同 | contract service |
| B012 | 金额=单价×数量，合同总金额=∑行项目金额 | contract service |

## API 端点

### 认证 `/api/auth`
- `POST /login` — 登录获取 JWT
- `POST /register` — 注册新用户
- `GET /me` — 获取当前用户信息

### 客户 `/api/customers`
- `GET /api/customers?keyword=` — 客户列表（支持关键词搜索）
- `GET /api/customers/{id}` — 客户详情
- `POST /api/customers` — 新建客户
- `PUT /api/customers/{id}` — 更新客户
- `DELETE /api/customers/{id}` — 删除客户

### 规格 `/api/specs`
- `GET /api/specs?keyword=` — 规格列表
- `GET /api/specs/{id}` — 规格详情
- `POST /api/specs` — 新建规格
- `PUT /api/specs/{id}` — 更新规格
- `DELETE /api/specs/{id}` — 删除规格

### 合同 `/api/contracts`
- `GET /api/contracts?keyword=&status=` — 合同列表（权限过滤）
- `GET /api/contracts/available` — 可下推的合同列表
- `GET /api/contracts/{id}` — 合同详情
- `POST /api/contracts` — 新建合同
- `PUT /api/contracts/{id}` — 更新合同（仅草稿）
- `DELETE /api/contracts/{id}` — 删除合同（仅草稿）
- `POST /api/contracts/{id}/confirm-image` — 生成确认图
- `POST /api/contracts/{id}/confirm` — 标记客户确认
- `GET /api/contracts/{id}/versions` — 确认图版本历史

### 图片上传 `/api/upload`
- `POST /api/upload/images` — 上传图片（多文件、自动压缩）

### 工艺单 `/api/process-sheets`
- `GET /api/process-sheets?keyword=` — 工艺单列表
- `GET /api/process-sheets/{id}` — 工艺单详情
- `POST /api/process-sheets` — 新建工艺单（选择未下推合同）
- `POST /api/process-sheets/push-down/{contract_id}` — 从合同下推
- `PUT /api/process-sheets/{id}/confirm` — 工艺单确认（草稿→保存）
- `POST /api/process-sheets/{id}/dispatch` — 工艺单下发
- `GET /api/process-sheets/{id}/print` — 打印 PDF
- `DELETE /api/process-sheets/{id}` — 删除工艺单

## 角色权限

| 功能 | 业务员 | 销售经理 | 生产专员 |
|------|--------|---------|---------|
| 客户/规格增删改查 | 全部 | 全部 | 全部 |
| 新建/查看合同 | 仅自己 | 全部 | **不可见**（403） |
| 编辑合同 | 仅自己的草稿 | 全部草稿 | 不可 |
| 生成确认图 | 可 | 可 | 不可 |
| 标记确认 | 可 | 可 | 不可 |
| 删除合同 | 仅草稿+自己的 | 仅草稿 | 不可 |
| 下推工艺单 | 不可 | 可 | 可 |
| 查看工艺单 | 仅关联 | 全部 | 全部 |
| 编辑/删除工艺单（草稿） | 不可 | 可 | 可 |
| 下发工艺单 | 不可 | 可 | 可 |

## 核心工作流

### 完整流程
```
1. 创建客户 → 创建规格
2. 新建合同（填写基本信息、工艺备注、辅料、包装箱单、行项目）
3. 上传花型图片（自动压缩）
4. 生成确认图V1（系统自动分配版本号）
5. 发送确认图给客户确认（线下：微信/邮件）
6. 标记客户已确认（合同→保存，版本锁定）
7. 下推工艺单（合同→已下发，创建工艺单→草稿）
8. 确认工艺单（工艺单→保存）
9. 下发工艺单（工艺单→已下发，校验合同版本）
10. 打印工艺单 PDF
```

### 确认图版本控制
```
草稿 → 生成确认图V1 → (修改合同) → 生成V2 → ... → 客户确认(Vn) → 保存
```
- 每次生成版本号+1
- 每张确认图记录生成时间、操作人、修改日志
- 标记确认基于最新版本
- 工艺单生成时记录基于哪个版本

## 本地开发

### 后端
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# WeasyPrint 可选：pip install weasyprint

# 确保 MySQL 运行，创建数据库
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS huazhi CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 初始化数据库并插入测试数据
python init_db.py
python seed.py

# 启动（热重载）
uvicorn app.main:app --reload --port 8000
```

### 前端
```bash
cd frontend
npm install
npm run dev
```

### 测试账号
| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 销售经理 |
| sales | sales123 | 业务员 |
| producer | prod123 | 生产专员 |

### 数据库配置（backend/app/config.py）
```
DATABASE_URL=mysql+pymysql://root:root@localhost:3306/huazhi?charset=utf8mb4
COMPRESS_QUALITY=85
COMPRESS_MAX_WIDTH=1920
```

## Docker 部署

```bash
docker-compose up -d
```

部署架构：
- **MySQL 8.0**: 端口 3306，持久化卷 mysql_data
- **Backend**: Python FastAPI 运行在 uvicorn，端口 8000
- **Frontend**: Nginx 托管 Vue 构建产物，端口 80，反向代理 /api/ 和 /uploads/ 到后端

前端 Nginx 配置代理：
- `/api/` → `http://backend:8000/api/`
- `/uploads/` → `http://backend:8000/uploads/`
