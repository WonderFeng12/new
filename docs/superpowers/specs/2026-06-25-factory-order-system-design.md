# 花织工厂管理系统 — 第1期设计文档

> 日期：2026-06-25
> 技术栈：Python FastAPI + Vue 3 + Element Plus + MySQL

---

## 1. 系统概述

花织工厂订单管理系统，分三期实施。第1期为 Web 端订单录入系统，实现从订单录入→客户确认→合同生成→工艺单下发的完整闭环。

### 1.1 第1期范围

- 客户主数据维护
- 规格主数据维护
- 合同（订单）录入，含花型图片上传（自动压缩）
- 客户确认图生成（版本控制）
- 销售合同管理
- 工艺单生成与下发
- 工艺单固定格式打印

### 1.2 后续期次（设计时预留扩展点）

- **第2期**：微信小程序 — 客户自主选花型、下单
- **第3期**：工厂内部协同 — 库存管理、信息共享
- **远期**：外协加工通知单（从工艺单下推）

---

## 2. 全局业务规则

### 2.1 状态机

合同与工艺单统一使用三状态：

| 状态 | 含义 | 合同 | 工艺单 |
|------|------|------|--------|
| **草稿** | 可编辑 | 可修改、可生成确认图、可软删除 | 可编辑、可软删除 |
| **保存** | 已定稿 | 客户已确认、版本锁定、可下推 | 不可编辑、可下发 |
| **下发** | 已发布 | 工艺单已下发、不可删除 | 发至车间、不可删除 |

### 2.2 状态流转

```
合同草稿 → (客户确认) → 合同保存 → (下推工艺单) → 合同下发
                                                      ↓
工艺单草稿 → (填写完成) → 工艺单保存 → (校验合同版本) → 工艺单下发
```

### 2.3 关键约束

| 规则 | 说明 |
|------|------|
| 工艺单必须有合同 | 新建工艺单时选择未下推的合同，或从合同下推 |
| 一个合同只能下推一次 | is_pushed_down 标记控制 |
| 工艺单下发需校验合同版本 | 必须基于合同最新确认版本 |
| 工艺单下发 → 合同自动下发 | 联动锁定 |
| 软删除 | 所有表使用 is_deleted 字段 |
| 已下发数据不可删除 | 合同/工艺单下发后禁止删除 |

---

## 3. 客户管理

### 3.1 功能

- 客户主数据维护（支持增删改查）
- 在合同录入时从已有客户中选择

### 3.2 数据结构

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK AUTO_INCREMENT | |
| customer_no | VARCHAR(50) UNIQUE | 客户编号，系统生成 |
| name | VARCHAR(200) NOT NULL | 客户名称 |
| contact | VARCHAR(100) | 联系人 |
| phone | VARCHAR(50) | 联系电话 |
| address | TEXT | 地址 |
| is_deleted | TINYINT(1) DEFAULT 0 | 软删除 |
| created_by | VARCHAR(100) | 创建人 |
| updated_by | VARCHAR(100) | 最后更改人 |
| created_at | DATETIME | |
| updated_at | DATETIME | |

---

## 4. 规格主数据管理

### 4.1 功能

- 规格主数据维护（支持增删改查）
- 创建合同时如果输入的规格不存在，自动创建并给出提示
- 规格描述自动生成：`规格名称(毛毯尺寸) + 毛毯重量 + (单/双层/复合) + 拼接而成`

### 4.2 数据结构

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK AUTO_INCREMENT | |
| spec_name | VARCHAR(100) NOT NULL | 规格名称（毛毯尺寸），如 200×240 |
| weight | VARCHAR(50) NOT NULL | 毛毯重量，如 4KG |
| layer_type | ENUM('单层','双层','复合') NOT NULL | 单双层 |
| splice_method | VARCHAR(100) | 拼接方式 |
| spec_description | TEXT | 规格描述，自动生成 |
| is_deleted | TINYINT(1) DEFAULT 0 | |
| created_by | VARCHAR(100) | 创建人 |
| updated_by | VARCHAR(100) | 最后更改人 |
| created_at | DATETIME | |
| updated_at | DATETIME | |

---

## 5. 合同管理

### 5.1 合同主表字段

| 字段分类 | 字段名 | 类型 | 必填 | 说明 |
|---------|--------|------|------|------|
| 基本信息 | id | INT PK | | |
| | contract_no | VARCHAR(100) | **是** | 合同/订单号，支持手写，后期支持自定义流水号 |
| | customer_id | INT FK | **是** | 关联客户表 |
| | contract_date | DATE | **是** | 日期 |
| | spec_id | INT FK | **是** | 关联规格主数据 |
| | spec_description | TEXT | 否 | 合同中的规格说明，直接使用规格描述 |
| | is_pressed | TINYINT(1) | 否 | 是否压花 |
| | packaging_type | VARCHAR(50) | 否 | 包装方式：纸箱/压缩包/真空包/打卷面料 |
| | delivery_date | DATE | 否 | 出货日期 |
| 合同头部展示 | spec_display | - | - | 规格说明：`规格描述 + 是否压花(是/否) + 包装方式`，使用时动态拼接，不存库 |
| 包边 | binding_material | VARCHAR(200) | **是** | 包边布材料 |
| | binding_width | VARCHAR(50) | 否 | 包边布宽度 |
| | binding_color_no | VARCHAR(50) | 否 | 颜色号(包边布颜色) |
| 技术要求 | tech_note_1~10 | TEXT | **备注1必填** | 10个备注字段 |
| 辅料（6组） | accessory_desc_1~6 | VARCHAR(200) | **说明1必填** | 辅料说明内容 |
| | accessory_size_1~6 | VARCHAR(100) | 否 | 辅料具体尺寸 |
| | accessory_qty_1~6 | DECIMAL(10,2) | 否 | 辅料数量，按行项目计算 |
| 包装要求 | pack_note_1~5 | TEXT | **备注1必填** | 5个备注字段 |
| 装箱要求 | box_note_1~3 | TEXT | **备注1必填** | 3个备注字段 |
| 压花 | emboss_model | VARCHAR(100) | 否 | 压花板型号 |
| 金额 | total_amount | DECIMAL(12,2) | 否 | 总金额，行项目金额合计 |
| 状态 | status | ENUM('草稿','保存','已下发') | | 默认草稿 |
| | is_pushed_down | TINYINT(1) DEFAULT 0 | | 是否已下推工艺单 |
| | push_down_sheet_id | INT | | 关联的工艺单ID |
| 版本 | latest_confirm_version | INT DEFAULT 0 | | 最新确认图版本号 |
| 权限 | created_by | VARCHAR(100) | | 创建人（用于权限控制） |
| | updated_by | VARCHAR(100) | | 最后更改人 |
| 软删除 | is_deleted | TINYINT(1) DEFAULT 0 | | |
| 时间 | created_at | DATETIME | | |
| | updated_at | DATETIME | | |

### 5.2 合同明细行（含价格 + 花型信息）

每条行项目包含金额信息和花型信息：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | INT PK | | |
| contract_id | INT FK | **是** | 关联合同 |
| line_no | INT | **是** | 行号，自动编号 |
| | | | |
| **价格信息** | | | |
| unit_price | DECIMAL(10,2) | 否 | 单价 |
| qty | DECIMAL(10,2) | 否 | 数量 |
| amount | DECIMAL(12,2) | 否 | 金额 = 单价 × 数量 |
| | | | |
| **花型信息** | | | |
| pattern_code | VARCHAR(100) | 否 | 花型编号 |
| **A面** | | | |
| color_a | VARCHAR(100) | 否 | A面颜色 |
| image_a_1~3 | VARCHAR(500) | 否 | A面图片，最多3张 |
| **B面（复合毯）** | | | |
| color_b | VARCHAR(100) | 否 | B面颜色 |
| image_b_1~3 | VARCHAR(500) | 否 | B面图片，最多3张 |
| | | | |
| remark | TEXT | 否 | 备注 |

> 前端显示：单价、数量、金额 → 合同头部总金额
> 合同创建时允许0行；生成工艺单时**必须**包含行项目

---

## 6. 确认图版本控制

### 6.1 流程

```
合同草稿 → 生成确认图V1 → (修改合同) → 生成确认图V2 → ...
    → 客户确认(V2) → 合同保存 → 下推工艺单
```

### 6.2 规则

- 同一合同可多次生成确认图，版本号每次+1
- 每张确认图上标注：版本号 + 生成日期时间 + 修改内容摘要
- 确认图手工发送给客户（微信/邮件等），操作人员在系统中标记"已确认"
- 客户确认基于最新版本
- 工艺单生成时必须指明基于哪个合同版本

### 6.3 数据结构

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | |
| contract_id | INT FK | 关联合同 |
| version_no | INT NOT NULL | 版本号，从1开始 |
| generated_at | DATETIME | 生成时间 |
| generated_by | VARCHAR(100) | 生成人 |
| change_log | TEXT | 本次修改内容 |
| is_confirmed | TINYINT(1) DEFAULT 0 | 客户是否已确认 |
| confirmed_at | DATETIME | 确认时间 |
| confirmed_by | VARCHAR(100) | 确认操作人 |
| image_path | VARCHAR(500) | 确认图文件路径 |
| contract_snapshot | JSON | 生成时的合同数据快照 |

---

## 7. 工艺单管理

### 7.1 工艺单字段

工艺单包含合同所有字段 + 以下工艺单专用字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | INT PK | | |
| contract_id | INT FK | **是** | 关联合同 |
| sheet_no | VARCHAR(100) | **是** | 工艺单号，系统生成 |
| confirm_version_no | INT | **是** | 基于合同的第几版确认图 |
| confirm_image_id | INT FK | **是** | 关联确认图版本记录 |
| status | ENUM('草稿','保存','已下发') | | 默认草稿 |
| is_deleted | TINYINT(1) DEFAULT 0 | | 软删除 |
| created_by | VARCHAR(100) | | 创建人 |
| updated_by | VARCHAR(100) | | 最后更改人 |
| created_at | DATETIME | | |
| updated_at | DATETIME | | |

> 其他字段（客户、规格、包边、技术要求、辅料、包装、装箱、行项目等）从合同带入

### 7.2 创建方式

方式一：从合同详情页点击「下推」，自动创建
方式二：在工艺单新建页面，从「未下推」的合同列表中选择

### 7.3 下发校验规则

```
1. 获取工艺单关联的合同 contract_id
2. 获取合同的最新确认版本号
3. IF 工艺单的 confirm_version_no < 合同最新版本号
   → 禁止下发，提示："合同已有新版本，请重新生成工艺单"
4. IF 工艺单的 confirm_version_no == 合同最新版本号
   → 允许下发
5. 下发后 → 工艺单只读、合同自动变为「已下发」
```

### 7.4 工艺单打印

- 工艺单保存/下发后可按固定格式打印（PDF/Excel）
- 打印内容包含：花型图片、客户确认信息、辅料包装等
- 格式模板**待用户提供**

---

## 8. 图片处理规则

| 项 | 说明 |
|----|------|
| 上传格式 | JPG / PNG / BMP / JPEG |
| 多选上传 | 支持 Ctrl/Shift 多选 |
| 文件名 | 保留原始文件名 |
| 压缩 | **强制压缩**，显示压缩前后大小和压缩率 |
| 数量 | 每行最多3张（A面），复合毯最多3张（B面） |
| 存储 | 压缩后存入服务器，路径记录到数据库 |

---

## 9. 权限与角色设计

### 9.1 角色定义

| 角色 | 权限范围 | 说明 |
|------|---------|------|
| **业务员** | 合同：查看、编辑**自己创建**的合同<br>工艺单：查看关联的工艺单 | 只看到自己的数据 |
| **销售经理** | 合同：查看、编辑**所有**合同<br>工艺单：查看所有工艺单 | 全量合同权限 |
| **生产专员** | 合同：无权限<br>工艺单：查看、编辑、下发 | 聚焦工艺单操作，不接触合同 |

### 9.2 权限控制表

| 功能 | 业务员 | 销售经理 | 生产专员 |
|------|--------|---------|---------|
| 客户管理（增删改查） | 全部 | 全部 | 全部 |
| 规格管理（增删改查） | 全部 | 全部 | 全部 |
| 新建合同 | 可 | 可 | 不可 |
| 查看/编辑自己的合同 | 可 | 可 | 不可 |
| 查看/编辑所有合同 | 不可 | 可 | 不可 |
| 删除合同 | 仅草稿+自己的 | 仅草稿 | 不可 |
| 生成确认图 | 可 | 可 | 不可 |
| 标记客户确认 | 可 | 可 | 不可 |
| 合同查看 | 仅自己的 | 全部 | **不可见** |
| 下推工艺单 | 不可 | 可 | 可 |
| 查看工艺单 | 仅关联 | 全部 | 全部 |
| 编辑/删除工艺单（草稿） | 不可 | 可 | 可 |
| 下发工艺单 | 不可 | 可 | 可 |

### 9.3 实现方式

采用简单 RBAC（Role-Based Access Control）：

```
用户表扩展：
user {
  id, username, password_hash,
  role: ENUM('业务员','销售经理','生产专员'),
  is_active, is_deleted
}

合同数据权限：
- 业务员: WHERE created_by = current_user
- 销售经理: 无条件（全量）
- 生产专员: 只能访问工艺单相关接口，合同接口无权限

后端通过依赖注入获取当前用户角色，
在 Service 层做权限判断。
```

### 9.4 预留扩展

- 角色表设计为可扩展（后续可改为动态角色+权限点模式）
- API 层预留装饰器/中间件做权限校验，后续角色增多不改结构

### 9.2 项目结构（初步）

```
backend/
  ├── app/
  │   ├── api/          # 路由
  │   ├── models/       # SQLAlchemy 模型
  │   ├── schemas/      # Pydantic 校验
  │   ├── services/     # 业务逻辑
  │   ├── utils/        # 图片压缩、PDF生成
  │   └── config.py
  └── main.py

frontend/
  ├── src/
  │   ├── views/        # 页面
  │   ├── components/   # 组件
  │   ├── api/          # 接口调用
  │   └── router/       # 路由
  └── package.json
```

### 9.3 API 设计（初步）

```
# 客户
GET/POST    /api/customers
GET/PUT/DELETE /api/customers/{id}

# 规格
GET/POST    /api/specs
GET/PUT/DELETE /api/specs/{id}

# 合同
GET/POST    /api/contracts
GET/PUT/DELETE /api/contracts/{id}
POST        /api/contracts/{id}/confirm-image   # 生成确认图
POST        /api/contracts/{id}/confirm         # 标记客户确认
GET         /api/contracts/{id}/versions        # 确认图版本历史

# 工艺单
GET/POST    /api/process-sheets
GET/PUT/DELETE /api/process-sheets/{id}
POST        /api/process-sheets/{id}/confirm    # 工艺单确认
POST        /api/process-sheets/{id}/dispatch   # 工艺单下发
GET         /api/process-sheets/{id}/print      # 打印
GET         /api/contracts/available            # 可供下推的合同列表
```

---

## 11. 关键业务逻辑清单

| ID | 逻辑 | 位置 |
|----|------|------|
| B001 | 合同录入时，规格不存在则自动创建并提示 | 合同Service |
| B002 | 合同草稿可修改、可反复生成确认图 | 合同Service |
| B003 | 确认图版本号递增，含时间戳和修改日志 | 确认图Service |
| B004 | 客户确认后合同变为「保存」，版本锁定 | 合同Service |
| B005 | 合同保存后才可下推工艺单 | 工艺单Service |
| B006 | 一个合同只能下推一次 | 数据库UNIQUE约束+代码 |
| B007 | 工艺单下发前校验合同版本是否为最新 | 工艺单Service |
| B008 | 工艺单下发 → 合同自动变为「已下发」 | 工艺单Service |
| B009 | 所有表软删除，已下发数据不可删除 | 各Service |
| B010 | 上传图片强制压缩，保留原始文件名 | 图片Utils |
| B011 | 业务员只能查看/编辑自己创建的合同 | 合同Service |
| B012 | 金额=单价×数量，合同总金额=∑行项目金额 | 合同Service |

---

## 12. 数据库ER关系

```
user (角色: 业务员/销售经理/生产专员)
  │
  ├── created_by ──< contract ──< contract_item (单价/数量/金额+花型)
  │                    │
  │               confirm_image (多版本, 关联确认版本)
  │                    │
  │               process_sheet (基于合同X版本生成)
  │
  ├── created_by ──< customer (主数据)
  ├── created_by ──< spec (主数据)
```

---

## 13. 待确认/补充

- [ ] 工艺单打印格式模板（用户晚点提供）
- [ ] 确认图的具体排版样式
- [ ] 流水号规则的具体配置方式
