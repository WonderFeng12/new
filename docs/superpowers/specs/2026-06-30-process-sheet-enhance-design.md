# 工艺单管理增强 Implementation Design

**Goal:** 完善工艺单管理的完整流程，涵盖创建方式简化、版本时间线修复、辅助功能改进、操作日志增强、内部确认人员配置、PDF 打印、重新编辑逻辑修正等。

**Architecture:** 后端 modifications 集中在 process_sheet service、production service、process_sheet model、notify service、pdf_generator；前端集中在 SheetDetail.vue、SheetList.vue、系统设置页。

**Tech Stack:** Python FastAPI + SQLAlchemy, Vue 3 + Element Plus, WeasyPrint (PDF), 企微 Webhook (通知)

---

## 模块1：工艺单创建方式变更

### 变更内容
- 删除 SheetList.vue 中的「新建工艺单」按钮及选合同弹窗
- 保留合同详情页行项目「下推工艺单」作为唯一创建方式
- 后端 API `POST /api/process-sheets` 保留（兼容性）
- `get_available_contracts` 保留

### 影响文件
- Modify: `frontend/src/views/processSheet/SheetList.vue` — 移除新建按钮及弹窗逻辑

## 模块2：版本时间线展示修复

### 变更内容
- 客户公开链接确认后版本变为 V0.5，但前端时间线组件未展示此事件
- 在 SheetDetail.vue 的时间线中加入客户确认事件节点
- 从操作日志中筛选客户确认事件（`remark` 含"客户确认"）来展示

### 影响文件
- Modify: `frontend/src/views/processSheet/SheetDetail.vue` — 时间线组件增加客户确认节点

## 模块3：辅助功能改进

### 3a 压花图片显示文件名
- 上传压花图片时，显示原始文件名在图片缩略图旁边
- 后端上传返回 `original_name` 字段（已有）

### 3b 辅料上传自动填充数量
- 辅料页签上传图片后，自动将对应辅料的数量更新为合同数量（从快照中取）
- 只在第一次上传时填充，已有数量时不覆盖

### 影响文件
- Modify: `frontend/src/views/processSheet/SheetDetail.vue` — emboss 上传区域显示文件名，辅料上传自动填充 qty

## 模块4：操作日志增强（行项目变更追踪）

### 变更内容
- 工艺单保存时（`update_sheet_detail`），像合同一样对比变更字段
- 生成变更摘要写入操作日志 remark
- 对比范围：`detail_data` 字段 + 行项目字段（pattern_data、packaging_type、is_pressed 等）

### 影响文件
- Modify: `backend/app/services/process_sheet.py` — `update_sheet_detail` 增加变更对比逻辑

## 模块5：内部确认人员配置

### 5a 系统级配置
- 在系统设置中新增「工艺单内部确认人」配置项
- 以 `system_config` 表存储，`config_key = 'process_sheet_confirm_users'`
- `config_value = JSON 数组 [user_id1, user_id2, ...]`
- 在设置页面可勾选用户（销售经理/生产专员）

### 5b 工艺单级确认人配置
- ProcessSheet 模型新增字段 `confirm_user_ids` (JSON, 默认[])
- 新建工艺单时从系统配置继承默认确认人
- 工艺单详情页新增「设置确认人」按钮（仅销售经理可操作）
- 弹窗显示用户列表供勾选

### 5c 客户确认后通知
- `customer_confirm_sheet` 中增加企微通知
- 通知内容："工艺单 XXX 客户已确认，请登录系统进行内部确认"
- @提及工艺单确认人名单中的用户（通过 wecom_userid）

### 5d 内部确认逻辑调整
- 只有 `confirm_user_ids` 名单中的用户可以点「内部确认」
- 确认完成后版本进位到 V1
- 不再使用 `internal_confirm_required` 数字（保留字段向后兼容）

### 影响文件
- Modify: `backend/app/models/process_sheet.py` — 新增 `confirm_user_ids` 字段
- Modify: `backend/app/schemas/process_sheet.py` — 新增确认人相关 schema
- Modify: `backend/app/services/process_sheet.py` — `create_sheet_from_items` 继承默认确认人、customer_confirm_sheet 增加通知、internal_confirm_sheet 校验名单
- Modify: `backend/app/services/notify.py` — 新增工艺单确认通知函数
- Modify: `backend/app/api/process_sheets.py` — 新增配置确认人端点
- Modify: `frontend/src/views/processSheet/SheetDetail.vue` — 新增设置确认人按钮/弹窗
- Modify: `frontend/src/views/settings/WeComSettings.vue` — 新增工艺单确认人配置（或新增独立设置页签）

## 模块6：重新编辑逻辑修正

### 变更内容
- 当前 `reopen_sheet_edit` 从"保存"状态重开时版本+1（V1→V2）
- 改为：只改状态回"草稿"，版本号保持不变（与合同逻辑一致）

### 影响文件
- Modify: `backend/app/services/process_sheet.py` — `reopen_sheet_edit` 移除版本递增逻辑

## 模块7：PDF 打印

### 变更内容
- 工艺单状态为"保存"（V1+）时，详情页显示「打印」按钮
- 点击后调用打印接口，下载 PDF
- PDF 右上角显示工艺单版本号 + 当前日期时间
- PDF 内容包含工艺单所有信息（花型行项目、技术说明、辅料明细、包装要求、箱单要求等）
- 使用工艺单数据（`detail_data` + 行项目数据）而非合同数据

### 影响文件
- Modify: `backend/app/utils/pdf_generator.py` — 完整重写，按新模板布局
- Modify: `backend/app/api/process_sheets.py` — 打印接口已存在，调整数据传递

## 模块8（记录待办）：权限控制梳理

### 待办内容
- 系统设置中工艺单确认人配置的权限
- 工艺单详情页设置确认人的权限
- 与现有角色权限体系合并梳理
- 暂不实施，仅记录

---

## CLAUDE.md 差异对比

### 需要更新的内容

1. **工艺单状态机**（CLAUDE.md L338-L354）
   - 重新编辑逻辑：版本不变（当前写的是 V1→V2 递增，需修正）

2. **业务规则**（CLAUDE.md L358-L386）
   - 新增 B038: 工艺单可设置具体内部确认人
   - 新增 B039: 工艺单保存时自动对比变更字段写入日志
   - 新增 B040: 客户确认后自动企微通知指定确认人
   - B032 内部确认规则需更新

3. **工艺单 API**（CLAUDE.md L411-L425）
   - 新增 `PUT /process-sheets/{id}/confirm-users` — 设置确认人
   - `POST /process-sheets/{id}/mark-version` 描述更新
   - 打印接口说明更新（PDF 含版本号+日期）

4. **工艺单两步确认流程**（CLAUDE.md L519-L536）
   - 更新内部确认流程：从名单制度替代人数制度

5. **权限表**（CLAUDE.md L467-L486）
   - 新增：设置工艺单确认人（仅销售经理）

6. **工艺单模型**（CLAUDE.md L235-L251）
   - 新增 `confirm_user_ids` 字段

7. **核心工作流**（CLAUDE.md L488-L506）
   - 步骤 6-8 更新为新的内部确认流程
