# 嘉元瑞通工厂管理系统

## 项目概述

嘉元瑞通工厂订单管理系统，分三期实施。第1期为 Web 端订单录入系统，已实现从订单录入→客户确认→合同生成→工艺单下发→生产推进的完整闭环。

- **第1期（已完成）**：Web 页面订单录入系统（含公开确认链接）
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
| 通知 | 企业微信群机器人 Webhook |
| 部署 | Docker + docker-compose |

## 项目结构

```
/
├── CLAUDE.md                  # 本文件
├── Dockerfile                 # 后端 Docker 镜像
├── docker-compose.yml         # 一键部署（MySQL + 后端 + 前端）
├── .dockerignore
├── .claude/
│   ├── settings.local.json      # 本地权限配置
│   └── agents/                  # 测试 Agent 定义
│       ├── spec-tester.md
│       └── contract-tester.md
├── backend/
│   ├── Dockerfile.dev         # 开发用（热重载）
│   ├── requirements.txt
│   ├── main.py                # 启动入口
│   ├── init_db.py             # 建表脚本
│   ├── seed.py                # 测试数据
│   ├── migrate_*.py           # 数据库迁移脚本
│   ├── uploads/               # 上传文件存储（gitignored）
│   └── app/
│       ├── main.py            # FastAPI 入口，注册路由
│       ├── config.py          # 配置（数据库、JWT、图片压缩参数）
│       ├── database.py        # 数据库连接（SQLAlchemy engine/session）
│       ├── dependencies.py    # 依赖注入（get_current_user, require_permission）
│       ├── models/            # SQLAlchemy 模型
│       │   ├── mixins.py      # TimestampMixin, SoftDeleteMixin, AuditMixin
│       │   ├── user.py
│       │   ├── customer.py
│       │   ├── spec.py
│       │   ├── contract.py
│       │   ├── contract_item.py
│       │   ├── confirm_image.py
│       │   ├── process_sheet.py
│       │   ├── process_sheet_item.py
│       │   ├── process_step.py         # 工序主数据
│       │   ├── process_step_assignee.py # 工序负责人配置
│       │   ├── production_log.py       # 生产状态变更日志
│       │   ├── webhook_config.py       # 企微群机器人配置
│       │   ├── system_config.py        # 系统配置
│       │   └── basic_data.py  # 基础数据（颜色映射、包装方式等）
│       ├── schemas/           # Pydantic 校验/序列化
│       │   ├── user.py
│       │   ├── customer.py
│       │   ├── spec.py
│       │   ├── contract.py
│       │   ├── contract_item.py
│       │   ├── confirm_image.py
│       │   ├── process_sheet.py
│       │   ├── process_step.py
│       │   ├── production_log.py
│       │   ├── webhook_config.py
│       │   ├── system_config.py
│       │   └── basic_data.py
│       ├── services/          # 业务逻辑层
│       │   ├── auth.py        # 认证、JWT 生成/验证
│       │   ├── customer.py    # 客户 CRUD + 编号生成
│       │   ├── spec.py        # 规格 CRUD + 描述自动生成
│       │   ├── contract.py    # 合同 CRUD + 金额计算 + 权限过滤
│       │   ├── confirm_image.py # 确认图版本控制
│       │   ├── process_sheet.py # 工艺单 CRUD + 下推 + 版本校验
│       │   ├── process_step.py  # 工序 CRUD + 负责人配置
│       │   ├── production.py    # 生产流程：推进/回退/返工/取消/坯布计划
│       │   ├── notify.py        # 企微通知发送
│       │   ├── reminder.py      # 定时催办
│       │   ├── permission.py    # 权限系统（模块级缓存、check_permission、权限定义）
│       │   └── basic_data.py    # 基础数据 CRUD + 颜色映射查询
│       ├── api/               # 路由层
│       │   ├── auth.py
│       │   ├── customers.py
│       │   ├── specs.py
│       │   ├── contracts.py
│       │   ├── process_sheets.py
│       │   ├── production.py   # 生产流程 + 工序管理 + 设置
│       │   ├── users.py        # 用户管理 CRUD
│       │   ├── webhook_config.py # 企微webhook配置
│       │   ├── upload.py
│       │   ├── basic_data.py
│       │   ├── permissions.py  # 角色权限管理 CRUD
│       │   └── public.py       # 公开端点（无需登录）
│       └── utils/
│           ├── image_compress.py
│           └── pdf_generator.py
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── api/
│       │   ├── index.js
│       │   ├── auth.js
│       │   ├── customer.js
│       │   ├── spec.js
│       │   ├── contract.js
│       │   ├── upload.js
│       │   ├── processSheet.js
│       │   ├── basicData.js
│       │   ├── production.js
│       │   ├── user.js                    # 用户管理 API
│       │   ├── webhookConfig.js           # Webhook 配置 API
│       │   └── permissions.js             # 角色权限 API
│       ├── store/
│       │   ├── user.js
│       │   └── permissions.js             # 权限 Pinia store（hasPermission、fetchMyPermissions）
│       ├── composables/
│       │   └── usePermission.js           # 权限检查组合式函数
│       ├── router/
│       │   └── index.js
│       ├── components/
│       │   ├── ImageUploader.vue
│       │   └── StatusLog.vue
│       └── views/
│           ├── login/Login.vue
│           ├── dashboard/Dashboard.vue
│           ├── customer/CustomerList.vue
│           ├── spec/SpecList.vue
│           ├── contract/ (ContractList, ContractForm, ContractDetail)
│           ├── processSheet/ (SheetList, SheetDetail)
│           ├── basicData/BasicDataList.vue
│           ├── settings/ (WeComSettings.vue, UserList.vue, PermissionMatrix.vue)
│           └── public/ConfirmPage.vue
```

## 数据库模型

### 用户 (user)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | |
| username | VARCHAR(100) UNIQUE | 登录名 |
| password_hash | VARCHAR(200) | bcrypt 哈希 |
| display_name | VARCHAR(100) | 显示名 |
| role | ENUM('业务员','销售经理','生产专员','外协人员') | 角色 |
| is_active | BOOLEAN | 是否启用 |
| is_deleted | BOOLEAN | 软删除 |
| wecom_userid | VARCHAR(100) | 企微用户ID（用于 @提及通知）|

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
| length | VARCHAR(50) | 毛毯尺寸-长（必须是数字）|
| width | VARCHAR(50) | 毛毯尺寸-宽（必须是数字）|
| weight | VARCHAR(50) | 存储如 4KG（输入纯数字，系统自动追加 KG）|
| layer_type | ENUM('单层','双层','复合') | 单双层 |
| spec_name | VARCHAR(200) | 自动生成：`长*宽/重量/层类型` |
| spec_description | TEXT | 自动生成，同 spec_name |

### 基础数据 (basic_data) — 含 TimestampMixin
| 字段 | 类型 | 说明 |
|------|------|------|
| category | VARCHAR(50) | 分类：color_mapping/packaging_type/code_rules |
| code | VARCHAR(100) | 代码/键 |
| value | VARCHAR(200) | 值 |
| sort_order | INT | 排序号 |

### 合同 (contract) — 含 TimestampMixin + SoftDeleteMixin + AuditMixin
包含字段：contract_no, customer_id(FK), contract_date, spec_id(FK 废弃), delivery_date, binding_material/width/color_no, tech_note_1~10(TEXT), accessory_desc/size/qty_1~6, pack_note_1~5, box_note_1~3, emboss_model, total_amount(DECIMAL 12,2)

> 毛毯规格、是否压花、包装方式 已移至行项目级别。

状态字段：
- **status**: ENUM('草稿','确认','已下发')，默认草稿
- **is_pushed_down**: BOOLEAN 是否下推行项目到工艺单
- **push_down_sheet_id**: INT 关联工艺单 ID
- **latest_confirm_version**: INT 版本号：确认后初始 V1，重新确认版本+1
- **confirm_requested_at**: DATETIME 请求确认时间
- **last_reminded_at**: DATETIME 催办提醒时间

### 合同行项目 (contract_item)
| 字段 | 说明 |
|------|------|
| line_no | 行号 |
| spec_id(FK) | 关联规格 |
| is_pressed | 是否压花 |
| packaging_type | 包装方式（纸箱/抽真空/压缩包/打卷面料）|
| delivery_date | 交期 |
| pattern_count | 花型数量 |
| pattern_data(JSON) | 花型详细数据 |
| unit_price / qty / amount | 价格信息 |
| pattern_code | 花型编号 |
| color_a / color_b | A/B 面颜色 |
| image_a_1~3 / image_b_1~3 | A/B 面图片 |
| remark | 备注 |
| **production_status** | VARCHAR(30) 生产状态（工序编码）|
| **yarn_plan_user_id**(FK) | 坯布负责人（外协人员）|
| **yarn_plan_no** | 坯布计划单号 |
| **cancel_reason** | TEXT 取消原因 |
| **cancel_quantities** | JSON 取消数据（含 snapshot: contract_version, production_status, restored 等恢复用字段） |
| has_process_sheet | 是否已下推工艺单（计算属性，非持久化） |
| process_sheet_id / process_sheet_no / process_sheet_status / process_sheet_version | 关联工艺单信息（计算属性，非持久化） |
| yarn_plan_user_name | 坯布负责人姓名（计算属性，非持久化） |

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
| sheet_no | 工艺单号 `月-序号` 或 `YYYYMM-序号` |
| confirm_version_no | DECIMAL：工艺单独立版本号，初始 V0，客户沟通后递增 |
| status | ENUM('草稿','保存','已下发','已确认','修改中') |
| version_marked | BOOLEAN 是否标记客户沟通 |
| version_note | TEXT 版本标记说明 |
| confirm_token | VARCHAR(36) UUID 公开确认链接令牌 |
| customer_comment | TEXT 客户意见 |
| customer_confirmed | BOOLEAN 客户是否已通过公开链接确认 |
| internal_confirm_required | INT 内部确认所需人数，默认1（保留向后兼容，实际以名单人数为准）|
| internal_confirmed_users | JSON 已内部确认的用户ID列表 |
| **confirm_user_ids** | **JSON 工艺单指定的内部确认人用户ID列表，新建时从系统配置继承** |
| detail_data | JSON 生产详情 |
| contract_snapshot | JSON 下推时合同快照（含 contract_no, latest_confirm_version, customer_name 等）|
| contract_snapshot_item | JSON 行项目快照 |

### 工艺单行项目 (process_sheet_item)
| 字段 | 说明 |
|------|------|
| process_sheet_id(FK) | 关联工艺单 |
| contract_item_id(FK) | 关联合同行项目 |
| line_no | 行号 |
| spec_id(FK) | 规格 |
| packaging_type | 包装方式 |
| is_pressed | 是否压花 |
| delivery_date | 交期 |
| pattern_count | 花型数量 |
| pattern_data(JSON) | 花型数据 |
| pattern_code | 花型编号 |
| color_a / color_b | 颜色 |
| image_a_1~3 / image_b_1~3 | 图片 |
| qty | 数量 |
| pressed_image(JSON) | 压花图片URL列表（多图）|
| pressed_image_name(JSON) | 压花图片原始文件名列表 |
| process_remark | 工艺备注 |
| remark | 备注 |
| cancel_reason | TEXT 取消原因 |
| cancel_quantities(JSON) | 取消快照（含 restored 标志）|

### 工序 (process_step)
| 字段 | 类型 | 说明 |
|------|------|------|
| step_code | VARCHAR(30) UNIQUE | 工序编码，如 yarn_plan/weaving |
| step_name | VARCHAR(50) | 工序名称 |
| sort_order | INT | 排序 |
| is_active | BOOLEAN | 是否启用 |

### 工序负责人 (process_step_assignee)
| 字段 | 说明 |
|------|------|
| process_step_id(FK) | 关联工序 |
| user_id(FK) | 关联用户 |
| UNIQUE(process_step_id, user_id) | 唯一约束 |

### 生产日志 (production_log)
| 字段 | 说明 |
|------|------|
| contract_id(FK) | 关联合同 |
| contract_item_id(FK) | 关联行项目 |
| process_sheet_id(FK) | 关联工艺单 |
| from_status / to_status | 状态变更 |
| operation_type | ENUM('推进','回退','返工','取消','确认','坯布下达','重新编辑','修改','创建') |
| operator_id(FK) | 操作人 |
| remark | 备注 |
| notify_status | VARCHAR(20) 通知状态 |

> 每次合同保存（`update_contract`）和工艺单保存（`update_sheet_detail`）均会创建 `operation_type='修改'` 的日志，摘要自动对比变更字段生成。工艺单的 mark_version/confirm/dispatch 也会创建对应日志。`operation_type='创建'` 用于合同/工艺单新建时记录。

### Webhook 配置 (webhook_config)
| 字段 | 说明 |
|------|------|
| name | VARCHAR(100) UNIQUE webhook名称 |
| webhook_url | TEXT 企微群机器人URL |
| is_enabled | BOOLEAN 是否启用 |

### 系统配置 (system_config)
| 字段 | 说明 |
|------|------|
| config_key | VARCHAR(100) UNIQUE 配置键 |
| config_value | TEXT 配置值 |

## 状态机

### 合同
```
草稿 → (销售经理确认, V+1) → 确认(V1) → (下推行项目工艺单) → 已下发
  ↑                               │
  └── (重新编辑→草稿, 版本不变) ────┘
```
- **草稿**: 可编辑、可生成确认图、可删除
- **确认**: 已确认、可下推行项目到工艺单；`latest_confirm_version` 每次确认递增（V1→V2→V3...）
- **已下发**: 有行项目已下推工艺单
- **重新打开编辑** → 状态回到草稿，版本保持不变，需再次确认后版本+1

### 合同行项目生产状态（工序驱动）
```
↓ 坯布计划下达
yarn_plan → weaving → weaving_done → setting → setting_done
→ brushing → brushing_done → printing → printing_done
→ sewing → completed
```
- 每步推进需操作人是下一工序负责人
- 回退/返工仅销售经理/生产专员可操作
- 可在任意工序取消（cancelled）

### 工艺单（独立于合同的版本体系，两步确认）
```
纯草稿(V0) → (客户沟通) → V0.11 → (修改保存) → V0.12 → ...
→ (客户公开页确认) → V0.5(草稿) → (指定人员内部确认) → V1(保存) → (下发→打印) → 已下发
                                      → (重新编辑) → 重置客户状态，版本不变，可继续编辑
保存(V1+) → (重新编辑) → 回草稿，版本不变 → ...
```
- **纯草稿**（`confirm_version_no` = 0）：显示 V0，无版本，可随意修改
- **客户沟通标记**（首次点击）：从 V0 → V0.11，开启版本追踪
- **后续每次保存**：`confirm_version_no` 自动 +0.01（V0.12 → V0.13...）
- **客户确认（公开页）**：设置 `customer_confirmed=True`，版本设为 V0.5，状态保持"草稿"，等待内部确认
- **内部确认**：由指定的确认人名单人员逐一确认，全部完成后版本进位到整数（V1），状态→"保存"
- **重新编辑**：重置 `customer_confirmed=False`、清空 `internal_confirmed_users`；**版本号保持不变**（与合同逻辑一致）
- **PDF 打印**：V1（保存）后可打印，右上角显示工艺单版本号 + 下发日期时间
- **与合同版本的关系**：
  - 合同 `latest_confirm_version`：销售经理确认后初始 V1，重新确认版本+1
  - 工艺单 `confirm_version_no`：纯草稿 V0，客户沟通触发版本追踪
  - 工艺单详情页显示「下推时合同版本」与「当前合同最新版本」对比

## 业务规则

| ID | 规则 | 实现位置 |
|----|------|---------|
| B001-B003 | 规格/确认图/合同草稿操作 | 各 service |
| B004 | 合同确认：销售经理手动确认（带意见），或管理员确认 | contract service → manual_confirm_contract |
| B005 | 合同确认后可下推行项目到工艺单 | production service |
| B006 | 一个合同行项目只能下推一次工艺单 | production service (ProcessSheetItem 检查) |
| B007 | 工艺单下发前校验合同版本是否为最新 | process_sheet service → dispatch |
| B008 | 工艺单下发 → 合同自动变为「已下发」 | process_sheet service |
| B009 | 所有表软删除，已下发数据不可删除 | 各 service |
| B010 | 上传图片强制压缩（1920px, 85% quality） | image_compress utils |
| B011 | 业务员只能查看/编辑自己创建的合同 | contract service |
| B012 | 金额=单价×数量，合同总金额=∑行项目金额 | contract service |
| B013-B016 | 规格/客户/字段校验 | spec/customer service |
| B017-B020 | 前端自动生成说明 | ContractForm.vue |
| B021-B022 | 公开确认链接 | contract service + public API |
| B023-B024 | 工艺单版本号规则 | process_sheet service |
| B025 | 工艺单 confirm_version_no 初始 V0（独立版本体系），合同版本存于 contract_snapshot 供对比 | production service → create_sheet_from_items |
| B026 | 行项目级别排产：坯布计划下达后 production_status=yarn_plan | production service |
| B027 | 生产推进校验工序负责人权限 | production service |
| B028 | 删除工艺单时硬删除 ProcessSheetItem、重置合同行项目下推状态 | process_sheet service |
| B029 | 坯布计划可指定外协人员 | production service → release_yarn_plan |
| B030 | 工艺单版本历史展示合同版本对比：下推时快照版本 vs 当前合同最新版本 | SheetDetail.vue → contractVersionMatch computed |
| B031 | 每日 8:00 定时检查未确认合同，企微催办销售经理 | reminder.py → APScheduler
| B032 | 工艺单两步确认：客户公开页确认→V0.5，指定确认人逐一内部确认全部完成→V1；客户确认后企微通知指定确认人；重新编辑重置客户确认状态，版本不变 | process_sheet service → customer_confirm_sheet / internal_confirm_sheet / reopen_sheet_edit |
| B033 | 合同重新打开编辑时状态改为草稿，版本号不变；确认时版本+1 | contract service → reopen_edit / manual_confirm_contract |
| B038 | 工艺单可设置具体内部确认人（confirm_user_ids），新建时从系统配置继承默认名单；仅名单中用户可执行内部确认 | process_sheet service → create_sheet_from_items / internal_confirm_sheet |
| B039 | 工艺单保存时自动对比变更字段（detail_data + 行项目字段），生成变更摘要写入操作日志 remark | process_sheet service → update_sheet_detail |
| B040 | 客户公开页确认后自动企微通知工艺单指定的确认人，@提及对应人员 | process_sheet service → customer_confirm_sheet + notify service |
| B041 | 工艺单重新编辑仅改状态回草稿，版本号保持不变（与合同逻辑一致）| process_sheet service → reopen_sheet_edit |
| B042 | 工艺单 V1（保存）后可打印 PDF，右上角显示工艺单版本号+下发日期时间 | pdf_generator + print API |
| B034 | 取消行项目时保存合同版本快照（含 contract_version, production_status），支持恢复 | production service → cancel_item / restore_item |
| B035 | 已取消行项目不可下推工艺单或下达坯布计划（按钮灰化） | ContractDetail.vue → canPushDown / canReleaseYarn |
| B036 | 创建合同时自动记录 operation_type='创建' 的日志 | contract service → create_contract |
| B037 | 编辑合同时自动对比变更字段，生成详细摘要写入日志 remark | contract service → update_contract → _build_change_summary |
| B043 | 工艺单行项目取消/恢复：取消时保存快照写 ProductionLog，恢复时清 cancel_reason 标记 restored | process_sheet service → cancel_sheet_item / restore_sheet_item |
| B044 | 工艺单下发后操作列显示"查看"非编辑只读对话框，所有输入框 disabled，保存/上传/新增按钮隐藏 | SheetDetail.vue → isEditing computed |
| B045 | 工艺单行项目压花图片支持多图上传存储为 JSON 数组，文件名去后缀显示 | SheetDetail.vue + migrate_20260701_pressed_images_json.py |

## API 端点

### 认证 `/api/auth` — POST /login, POST /register, GET /me

### 客户 `/api/customers` — CRUD + keyword 搜索 + is_in_use 标记

### 规格 `/api/specs` — CRUD + keyword 搜索 + clone

### 合同 `/api/contracts`
- `GET /contracts` — 列表（权限过滤）
- `GET /contracts/available` — 可下推的合同列表
- `GET /contracts/{id}` — 详情
- `POST /contracts` — 新建
- `PUT /contracts/{id}` — 更新（草稿/可编辑）
- `DELETE /contracts/{id}` — 删除（仅草稿）
- `POST /contracts/{id}/confirm-image` — 生成确认图
- `POST /contracts/{id}/manual-confirm` — 销售经理手动确认（版本+1，带意见）
- `POST /contracts/{id}/request-confirm` — 业务员请求确认（企微通知）
- `POST /contracts/{id}/reopen-edit` — 重新打开编辑（状态→草稿，版本号不变）
- `POST /contracts/{id}/generate-confirm-link` — 生成确认链接
- `GET /contracts/{id}/versions` — 确认图版本历史
- `GET /contracts/{id}/production-logs` — 生产日志

### 工艺单 `/api/process-sheets`
- `GET /process-sheets` — 工艺单列表
- `GET /process-sheets/{id}` — 工艺单详情（含快照、合同信息）
- `POST /process-sheets` — 新建（仅通过合同行项目下推触发）
- `PUT /process-sheets/{id}/detail` — 保存工艺详情（含行项目明细、detail_data；自动对比变更写入操作日志）
- `POST /process-sheets/{id}/mark-version` — 标记客户沟通（版本 +0.01，首次 V0→V0.11）
- `POST /process-sheets/{id}/internal-confirm` — 内部确认一次（仅确认人名单中用户可操作）
- `POST /process-sheets/{id}/reopen-edit` — 重新打开编辑（状态→草稿，版本不变，重置客户确认状态）
- `PUT /process-sheets/{id}/confirm-users` — 设置工艺单内部确认人（仅销售经理）
- `PUT /process-sheets/{id}/confirm-requirements` — 设置需确认人数（仅销售经理，保留兼容）
- `POST /process-sheets/{id}/dispatch` — 下发工艺单
- `GET /process-sheets/{id}/print` — 打印工艺单 PDF（右上角版本号+下发日期）
- `DELETE /process-sheets/{id}` — 删除（恢复行项目下推状态）
- `POST /process-sheets/{id}/generate-confirm-link` — 生成客户确认链接
- `GET /process-sheets/{id}/logs` — 工艺单操作日志列表（按时间降序）
- `POST /process-sheets/{sheet_id}/items/{item_id}/cancel` — 取消工艺单行项目（快照数量+原因）
- `POST /process-sheets/{sheet_id}/items/{item_id}/restore` — 恢复已取消的工艺单行项目

### 生产流程 `/api` (production router)
- `GET /process-steps` — 工序列表
- `POST /process-steps` — 创建工序
- `PUT /process-steps/{id}` — 更新工序
- `DELETE /process-steps/{id}` — 删除工序
- `PUT /process-steps/{id}/assignees` — 设置工序负责人
- `POST /contract-items/{id}/advance` — 推进到下一工序
- `POST /contract-items/{id}/rollback` — 回退一工序
- `POST /contract-items/{id}/rework` — 返工到指定工序
- `POST /contract-items/{id}/cancel` — 取消行项目（快照合同版本+生产状态）
- `POST /contract-items/{id}/restore` — 恢复已取消的行项目（还原到取消前状态）
- `POST /contract-items/{id}/yarn-plan` — 下达坯布计划
- `POST /contract-items/{id}/push-down` — 下推工艺单
- `GET /contract-items/{id}/logs` — 行项目生产日志
- `GET /my-tasks` — 我的任务（外协人员）
- `GET /settings/wecom` — 企微设置
- `PUT /settings/wecom` — 更新企微设置
- `PUT /users/me/wecom` — 更新本人企微ID

### 基础数据 `/api/basic-data` — CRUD

### 图片上传 `/api/upload` — POST /images

### 公开接口 `/api/public` — GET /contract/{token}, POST /confirm/{token}

### 用户管理 `/api/users` — CRUD（仅销售经理）
- `GET /users` — 用户列表
- `POST /users` — 新建用户
- `PUT /users/{id}` — 编辑用户信息
- `PUT /users/{id}/reset-password` — 重置密码
- `DELETE /users/{id}` — 删除用户

### Webhook配置 `/api/webhook-configs` — CRUD（仅销售经理）
- `GET /webhook-configs` — 配置列表
- `POST /webhook-configs` — 新增配置
- `PUT /webhook-configs/{id}` — 编辑配置
- `DELETE /webhook-configs/{id}` — 删除配置

### 角色权限 `/api/permissions`
- `GET /permissions/definitions` — 返回 35 项权限定义（按模块分组，无需登录）
- `GET /permissions` — 当前角色→权限映射（需 `settings:permissions:manage`）
- `PUT /permissions` — 更新映射（需 `settings:permissions:manage`，写入 system_config）
- `GET /permissions/my` — 当前用户角色的权限列表

## 角色权限

### 灵活权限系统

权限存储在 `system_config` 表的 `role_permissions` 键中（JSON 格式），管理员可在 **系统设置 → 角色权限** 中自由勾选。

| 权限项 | key | 初始默认角色 |
|--------|-----|------------|
| **合同管理** | | |
| 查看合同 | contract:view | 业务员、销售经理、生产专员 |
| 新建合同 | contract:create | 业务员、销售经理 |
| 编辑合同 | contract:edit | 业务员、销售经理、生产专员 |
| 删除合同 | contract:delete | 业务员、销售经理 |
| 请求确认 | contract:request_confirm | 业务员、销售经理 |
| 手动确认 | contract:manual_confirm | 销售经理 |
| 重新打开编辑 | contract:reopen_edit | 销售经理、生产专员 |
| 生成确认图 | contract:generate_confirm_image | 业务员、销售经理 |
| 查看版本历史 | contract:view_versions | 业务员、销售经理 |
| 下推行项目到工艺单 | contract:push_down | 销售经理、生产专员 |
| **工艺单管理** | | |
| 查看工艺单 | sheet:view | 业务员、销售经理、生产专员 |
| 新建/下推工艺单 | sheet:create | 销售经理、生产专员 |
| 编辑工艺单 | sheet:edit | 销售经理、生产专员 |
| 删除工艺单 | sheet:delete | 销售经理、生产专员 |
| 客户沟通标记 | sheet:mark_version | 销售经理、生产专员 |
| 内部确认 | sheet:internal_confirm | 销售经理、生产专员（仅名单中） |
| 强制通过 | sheet:force_confirm | 销售经理 |
| 设置内部确认人 | sheet:set_confirm_users | 销售经理 |
| 下发工艺单 | sheet:dispatch | 销售经理、生产专员 |
| 打印 PDF | sheet:print | 销售经理、生产专员 |
| 重新打开编辑 | sheet:reopen_edit | 销售经理、生产专员 |
| 生成确认链接 | sheet:generate_confirm_link | 销售经理、生产专员 |
| **生产管理** | | |
| 管理工序(CRUD) | production:manage_steps | 销售经理、生产专员 |
| 生产推进 | production:advance | 销售经理、生产专员 |
| 回退 | production:rollback | 销售经理、生产专员 |
| 返工 | production:rework | 销售经理、生产专员 |
| 取消行项目 | production:cancel | 业务员、销售经理、生产专员 |
| 恢复已取消行项目 | production:restore | 销售经理、生产专员 |
| 下达坯布计划 | production:yarn_plan | 销售经理、生产专员 |
| **基础数据** | | |
| 查看基础数据 | basic_data:view | 全部角色 |
| 管理基础数据 | basic_data:manage | 销售经理、生产专员 |
| 管理客户 | customer:manage | 销售经理、生产专员 |
| 管理规格 | spec:manage | 销售经理、生产专员 |
| **系统设置** | | |
| 查看用户列表 | settings:user:view | 销售经理 |
| 管理用户 | settings:user:manage | 销售经理 |
| 查看 Webhook | settings:webhook:view | 销售经理 |
| 管理 Webhook | settings:webhook:manage | 销售经理 |
| 管理角色权限 | settings:permissions:manage | 销售经理 |

### 后端权限检查机制
- **API 层**：路由参数 `Depends(require_permission("perm_key"))` 自动拦截无权限请求，返回 403
- **Service 层**：`check_permission(db, role, permission)` 读取模块级缓存
- **缓存机制**：首次查询后缓存角色→权限映射，`PUT /api/permissions` 时自动失效
- **迁移脚本** `migrate_20260630_role_permissions.py` 初始化默认权限

### 前端权限检查机制
- **Pinia store**：`usePermissionStore.hasPermission('perm_key')` 在登录后自动加载
- **组件级**：`v-if="permStore.hasPermission('contract:edit')"` 控制按钮/功能显示
- **路由级**：`meta.roles` 从 JWT 解码检查基础访问，`meta.permissions` 做额外校验（store 加载后生效）
- **设置页**：`/settings/permissions` 矩阵页面，管理员自由勾选

### 新增角色

当前角色定义有 4 处硬编码，新增角色时需要同步修改：

| 位置 | 文件 | 改动内容 |
|------|------|----------|
| 数据库模型 | `backend/app/models/user.py` | `role` 字段的 `ENUM` 追加新角色值 |
| 迁移脚本 | `backend/migrate_20260630_role_permissions.py` | `DEFAULT_ROLES` 字典加新角色名和默认权限列表 |
| 权限设置页 | `frontend/src/views/settings/PermissionMatrix.vue` | `const roles = [...]` 数组加新角色 |
| 路由守卫 | `frontend/src/router/index.js` | 各路由 `meta.roles` 按需添加新角色 |

### 新增功能权限

新增功能（如库存管理、报表等）需要添加对应的权限项：

| 步骤 | 文件 | 改动内容 |
|------|------|----------|
| 1 | `backend/app/services/permission.py` | `get_all_permission_definitions()` 中加一条 `{"key": "模块:操作", "label": "说明"}` |
| 2 | `backend/migrate_20260630_role_permissions.py` | `DEFAULT_ROLES` 中决定哪些角色默认拥有新权限 |
| 3 | `backend/app/api/xxx.py` | 对应端点加 `Depends(require_permission("模块:操作"))` |
| 4 | `frontend/src/views/xxx.vue` | 对应按钮/入口加 `v-if="permStore.hasPermission('模块:操作')"` |

### 后续完善方向

如果角色或权限变动频繁，可考虑以下改进：

| 方向 | 说明 | 改动量 |
|------|------|--------|
| **角色动态化** | `User.role` 从 ENUM 改为 VARCHAR，角色列表存 `system_config` | 较大（涉及 JWT payload、路由守卫） |
| **权限定义动态化** | `get_all_permission_definitions()` 移到 `system_config`，设置页支持增删权限 | 中 |
| **数据权限** | 当前"业务员只能看自己合同"是硬编码的 Service 层逻辑，可拆为 `xxx:view:own` / `xxx:view:all` 两级 | 中 |
| **迁移脚本改为 seeds** | 用 `get_or_create` 方式追加，避免新增权限时反复改迁移脚本 | 小 |

## 核心工作流（V2）

### 完整流程
```
1. 创建客户 → 创建规格 → 新建合同（含行项目、花型图片）
2. 业务员填写完成 → 点击「请求确认」→ 企微通知销售经理
3. 销售经理打开合同详情 → 点击「手动确认」→ 填写确认意见 → 合同→确认(V1)
4. 在合同详情中，选择行项目 → 点击「下推工艺单」→ 弹出工艺备注弹窗
5. 系统创建工艺单(草稿,V0) → 跳转到工艺单详情页
6. 编辑工艺单详情 → 点击「客户沟通」→ 版本标记 V0.11，生成确认链接发给客户
7. 客户打开链接确认 → 版本 V0.5(草稿)，customer_confirmed=True → 企微自动通知指定确认人
8. 指定确认人逐一点击「内部确认」→ 企微通知进度 → 全部确认完成 → 版本 V1(保存)
9. （可选）打印工艺单 PDF → 右上角版本号+日期
10. 下发工艺单 → 工艺单→已下发
10. 在合同详情中，为行项目下达坯布计划 → 指定外协人员
11. 生产推进：每工序完成由负责人点击推进 → 企微通知下一工序负责人
12. 遇到问题时：回退/返工（仅销售经理/生产专员）
13. 需要取消时：填写原因取消行项目（企微通知，自动快照当前合同版本）
14. 取消后可点击「恢复」取消的行项目，还原到取消前状态（合同版本变更时提示）
```

### 合同确认流程
```
业务员完成合同 → 点击[请求确认] → 企微群通知销售经理
                                      ↓
                          销售经理打开合同详情
                                      ↓
                          点击[手动确认]，填写确认意见
                                      ↓
                          合同→确认(latest_confirm_version +1)
```

### 工艺单两步确认流程
```
客户打开公开链接 → 确认 → V0.5(草稿, customer_confirmed=True)
                               ↓
                    企微自动通知指定确认人：@{确认人1} {确认人2} ...
                               ↓
                    指定确认人逐一点击[内部确认]
                               ↓
                    企微通知："{用户名} 已确认（1/{总人数}）"
                               ↓
                    ... 所有确认人点击后 ...
                               ↓
                    企微通知："工艺单 {sheet_no} 已完成内部确认"
                    版本 → V1，状态 → 保存（可打印PDF）
```
- 客户确认后状态保持"草稿"，版本为 V0.5，显示"客户已确认"标签
- 内部确认人来源：工艺单级 `confirm_user_ids`（新建时从系统配置继承）
- 仅确认人名单中用户可以执行内部确认
- 客户确认后自动企微通知指定确认人（@提及）
- 每次内部确认发送企微通知进度
- 「重新编辑」按钮重置 `customer_confirmed=False`，清空内部确认列表，**版本号保持不变**
- 从"保存"/"已确认"重新编辑时版本不变（V1→回草稿V1）
- V1（保存）后详情页显示「打印」按钮，PDF 右上角显示版本号+当前日期时间

### 行项目下推 vs 旧合同下推
- **行项目下推（V2新模式）**：在合同详情中，每个行项目有独立「下推工艺单」按钮，一个行项目只能下推一次
- **旧合同下推（保留兼容）**：`POST /api/process-sheets/push-down/{contract_id}` 整单下推（is_pushed_down 标记）
- 删除工艺单 → 硬删除 ProcessSheetItem + 重置合同行项目下推状态

### 工序推进流程
```
坯布计划下达(yarn_plan) → 织造中 → 织造完成 → 定型中 → 定型完成
→ 刷毛烫光中 → 刷毛烫光完成 → 印花中 → 印花完成
→ 成品缝制 → 成品完成(completed)
```
- 行项目生产状态由 `production_status` 追踪
- 步进式推进，每步校验操作人权限
- 全部工序完成 → 自动发企微通知

## 图片存储策略

### 当前方案（第1期）
- **存储位置**：本地 `backend/uploads/` 目录
- **处理流程**：上传 → Pillow 强制压缩（最长边 1920px, 85% quality）
- **前端访问**：Nginx 反向代理 `/uploads/` → `http://backend:8000/uploads/`

### 未来方案（第2期规划）
上传 → 计算 SHA256 文件指纹 → 以 hash 为文件名存 OSS → 数据库只存 hash 和 URL → 天然去重

## 本地开发

### 后端
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS huazhi CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
python init_db.py && python seed.py
uvicorn app.main:app --reload --port 8000
```

### 前端
```bash
cd frontend && npm install && npm run dev
```

### 测试账号
| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 销售经理 |
| sales | sales123 | 销售经理 |
| producer | prod123 | 生产专员 |

### 登录流程说明

前端登录页 (`frontend/src/views/login/Login.vue`) 采用表单提交方式：

1. `<el-form>` 绑定 `@submit.prevent="handleLogin"`，登录按钮设置 `native-type="submit"`
2. 登录前先重置权限 store（`permStore.reset()`），确保切换账号时旧权限数据被清除
3. 登录成功后直接导航到 `/dashboard`（而非经过 `/` 的 redirect 链）
4. 防重复提交：`submitting` 标志在第一次 `await` 前设置

### axios 401 拦截器

`frontend/src/api/index.js` 中的 401 拦截器行为：
- 收到 401 响应 → 清除 localStorage 中的 token → 跳转 `/login`
- 如果已处于 `/login` 页面则跳过跳转（防止重定向循环）
- 403（权限不足）不会触发该拦截器，由各组件 catch 自行处理

### 数据库配置
```
DATABASE_URL=mysql+pymysql://root:root@localhost:3306/huazhi?charset=utf8mb4
COMPRESS_QUALITY=85
COMPRESS_MAX_WIDTH=1920
```

## Docker 部署

### 环境变量

复制 `.env.example` 为 `.env`，修改其中的密码和密钥：

```bash
cp .env.example .env
```

| 变量 | 说明 |
|------|------|
| `MYSQL_ROOT_PASSWORD` | MySQL root 密码（首次部署前修改）|
| `SECRET_KEY` | JWT 签名密钥（首次部署前修改为随机字符串）|

### 部署架构

```
外网 → 服务器:80 → Nginx容器 → 后端容器:8000 → MySQL容器:3306
                     └── /uploads/ → 后端:8000/uploads
```

- **MySQL 8.0**: 仅内部网络，不暴露端口
- **Backend**: Python FastAPI uvicorn，仅内部网络
- **Frontend**: Nginx 托管 Vue 产物，对外暴露 80 端口，反向代理 /api/ 和 /uploads/

### 一键部署（CentOS）

```bash
# 首次部署
cd /root/new/repo && bash scripts/deploy.sh init

# 日常更新（git pull + 重建 + 迁移）
cd /root/new/repo && bash scripts/deploy.sh update
```

首次部署后需在后台 **系统设置 → Webhook** 中配置 `system_base_url`（服务器公网地址），
公开确认链接功能才能正常工作。

### 手动部署

```bash
docker compose up -d --build
docker compose exec backend python init_db.py
# 按时间顺序执行所有迁移脚本
docker compose exec backend python migrate_20260629_internal_confirm.py
docker compose exec backend python migrate_20260629_production_log_process_sheet.py
docker compose exec backend python migrate_20260630_process_sheet_fields.py
docker compose exec backend python migrate_20260630_role_permissions.py
docker compose exec backend python migrate_20260630_process_sheet_item_cancel.py
docker compose exec backend python migrate_20260701_pressed_images_json.py
```

### 日常运维

```bash
# 构建并重启
docker compose up -d --build

# 查看日志
docker compose logs -f backend

# 备份数据库
docker compose exec db mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" huazhi > backup_$(date +%Y%m%d).sql

# 健康检查
curl http://localhost/api/health
```
