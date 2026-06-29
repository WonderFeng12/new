# 合同管理增强设计

## 目标

对合同管理的七项需求进行改进，重点是变更记录的详细化、取消恢复、日志统一管理和模块化。

## 1. 后端 Service 变更

### 1.1 创建合同时写日志

`contract.py` — `create_contract`

写一行 `ProductionLog`：

```
operation_type: "创建"
remark: "合同已创建（HT2026060001），共3个行项目"
```

不修改状态。

注意：需要在 `ProductionLog.operation_type` 枚举中添加 `"创建"`（当前是 `Enum('推进','回退','返工','取消','确认','坯布下达','重新编辑','修改')`）

### 1.2 编辑合同时记录详细变更

`contract.py` — `update_contract`

在原有的"修改"日志基础上，增加变更摘要生成逻辑：

**对比的字段：**

合同级：
- `binding_material`, `binding_width`, `binding_color_no`
- `emboss_model`, `delivery_date`
- `tech_note_1` ~ `tech_note_10`（只要值有变化，记录"技术说明N"）
- `pack_note_1` ~ `pack_note_5`（"包装说明N"）
- `box_note_1` ~ `box_note_3`（"箱单说明N"）

行项目级：
- `spec_id` → `"行项目N# 规格(X→Y)"`
- `packaging_type` → `"行项目N# 包装方式(A→B)"`
- `qty` → `"行项目N# 数量(M→N)"`
- `is_pressed` → `"行项目N# 压花(是→否)"`
- `delivery_date` → `"行项目N# 交货日期"`

**日志格式：**

无变化：不写日志
有变化但摘要为空：`"合同已修改（由XX操作）"`
有具体变化：`"修改了：交货日期(2026-07-15→2026-07-20)、行项目3# 包装方式(纸箱→抽真空)"`

摘要长度限制 500 字符，超出截断加 `"..."`。

### 1.3 重新编辑改为草稿

`contract.py` — `reopen_edit`

```python
# 当前状态为"确认"或"已下发"
contract.status = "草稿"
contract.updated_by = username
new_version = (contract.latest_confirm_version or 0) + 1
contract.latest_confirm_version = new_version
```

日志：

```
operation_type: "重新编辑"
remark: "重新打开编辑，版本 V3（由张三操作）"
```

### 1.4 取消时保存快照、恢复功能

`production.py` — `cancel_item`

`cancel_quantities` JSON 增加字段：

```json
{
  "cancel_qty": 50,
  "contract_version": 3,
  "contract_status": "确认",
  "production_status": "yarn_plan",
  "detail": "客户要求减量",
  "restored": false
}
```

`production.py` — 新增 `restore_item(db, item_id, user_id)`

```python
def restore_item(db, item_id, user_id):
    item = get item
    snapshot = item.cancel_quantities
    if not snapshot or snapshot.get("restored"):
        raise 400("无可恢复的取消记录")

    # 恢复生产状态
    item.production_status = snapshot.get("production_status")
    item.cancel_reason = None
    snapshot["restored"] = True
    item.cancel_quantities = snapshot

    log = ProductionLog(
        contract_id=item.contract_id,
        contract_item_id=item.id,
        operation_type="取消",
        from_status="cancelled",
        to_status=snapshot["production_status"],
        remark=f"已恢复取消：行项目恢复到取消前状态"
    )
```

### 1.5 日志删除

新增 `DELETE /api/logs/{id}` 端点（`production.py` 或独立 router）：

```python
@router.delete("/api/logs/{id}")
def delete_log(id, db, current_user):
    if current_user.role != "销售经理":
        raise 403("权限不足")
    log = db.query(ProductionLog).filter(ProductionLog.id == id).first()
    if not log:
        raise 404
    db.delete(log)
    db.commit()
```

## 2. 共享组件 StatusLog

### 2.1 组件接口

```vue
<StatusLog
  :logs="logs"
  :columns="['时间','操作','行号','从','到','操作人','备注']"
  :can-delete="isManager"
  :loading="loading"
  @delete="handleDelete"
/>
```

### 2.2 默认列配置

| 列 | 宽度 | 说明 |
|----|------|------|
| 时间 | 160px | `log.created_at` |
| 操作 | 100px | `operation_type` |
| 行号 | 60px | `contract_item_id` 关联的行号，无则 "─" |
| 从 | 100px | `from_status` |
| 到 | 100px | `to_status` |
| 操作人 | 100px | `operator_name` |
| 备注 | min-width 150px | `remark` 内容 |
| 操作 | 60px | 删除按钮（仅 `canDelete` 时显示） |

删除按钮使用 Element Plus 的 `el-button text type="danger" size="small"`，点击前弹出确认框。

### 2.3 工艺单集成

`SheetDetail.vue` 当前已有 `logs` 表格（改自之前的版本），将其替换为 `<StatusLog>` 组件：

```vue
<StatusLog
  :logs="logs"
  :columns="['时间','操作','备注']"
  :can-delete="isManager"
  :loading="loadingLogs"
  @delete="handleDeleteLog"
/>
```

工艺单日志不需要"行号""从""到""操作人"列，通过 `columns` prop 控制显示哪些列。

## 3. 前端 ContractDetail 修改

### 3.1 移除行项目"日志"按钮

删除：
```vue
<el-button size="small" @click="openLogDialog(row)">日志</el-button>
```

以及对应的 `openLogDialog`、`logDialogVisible`、`dialogLogs` 相关代码。

### 3.2 主状态日志逻辑变更

`loadData` 中 `getContractLogs` 改成获取**该合同所有日志**（当前已经是）。

后端 `get_contract_logs` 需 join `ContractItem` 获取 `line_no`，在 API 响应中增加 `item_no` 字段（行号，无则 `null`）：

```python
# production.py get_contract_logs
item = db.query(ContractItem).filter(
    ContractItem.id == log.contract_item_id
).first() if log.contract_item_id else None
item_no = item.line_no if item else None
```

日志表上方显示 `progressSummary` 不变。

### 3.3 已取消行高亮

行项目表格中，`production_status === 'cancelled'` 的行：

- 整行文字颜色 `#f56c6c`（红色）
- "取消"按钮改为"恢复"按钮（`type="warning"`，粉色）
- `canCancel` 改为 `canRestore`：若行已取消且用户有权限，显示"恢复"按钮

### 3.4 已取消行禁用下推/坯布

`canPushDown` 和 `canReleaseYarn` 增加 `if row.cancel_reason: return false`

### 3.5 可编辑状态条件

`ContractForm.vue` 编辑按钮/页面入口判断：允许 `status === "草稿"` 即可（reopen 后状态已改为草稿）

## 4. 文件清单

| 文件 | 变更类型 |
|------|---------|
| `backend/app/services/contract.py` | 修改 |
| `backend/app/services/production.py` | 修改 |
| `backend/app/api/production.py` | 修改 |
| `backend/app/api/contracts.py` | 修改（reopen_edit 调用改参数）|
| `frontend/src/components/StatusLog.vue` | **新建** |
| `frontend/src/views/contract/ContractDetail.vue` | 修改 |
| `frontend/src/views/contract/ContractForm.vue` | 修改 |
| `frontend/src/views/processSheet/SheetDetail.vue` | 修改 |
| `frontend/src/api/production.js` | 修改（新增 restore、deleteLog）|
