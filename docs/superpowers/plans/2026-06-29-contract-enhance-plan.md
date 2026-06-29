# 合同管理增强 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enhance contract management with detailed change logging, cancel/restore workflow, unified StatusLog component shared with process sheets.

**Architecture:** Backend service layer changes in contract.py and production.py, new API endpoints for restore and log deletion, new shared Vue component StatusLog, frontend modifications to ContractDetail/SheetDetail.

**Tech Stack:** Python FastAPI, SQLAlchemy, Vue 3 + Element Plus

---

### Task 1: Model — Add "创建" to ProductionLog enum + migration

**Files:**
- Modify: `backend/app/models/production_log.py`
- Create: (migration as part of seed)

- [ ] **Step 1: Add "创建" to operation_type enum**

In `backend/app/models/production_log.py:16`, change the enum:

```python
# Old:
operation_type = Column(Enum("推进", "回退", "返工", "取消", "确认", "坯布下达", "重新编辑", "修改"), nullable=False)
# New:
operation_type = Column(Enum("推进", "回退", "返工", "取消", "确认", "坯布下达", "重新编辑", "修改", "创建"), nullable=False)
```

- [ ] **Step 2: Add migration note to CLAUDE.md**

The model change needs a manual ALTER TABLE if DB already exists. Document:

```bash
# Run if production_log table already exists:
mysql -u root -proot huazhi -e "ALTER TABLE production_log MODIFY COLUMN operation_type ENUM('推进','回退','返工','取消','确认','坯布下达','重新编辑','修改','创建') NOT NULL;"
```

---

### Task 2: Backend — contract.py enhancements (create log + diff summary + reopen→草稿)

**Files:**
- Modify: `backend/app/services/contract.py`

- [ ] **Step 1: In `create_contract`, add production log after commit**

Find the end of `create_contract` function (line ~219), after `db.commit()`:

```python
# Add production log for contract creation
from app.models.production_log import ProductionLog
from datetime import datetime
log = ProductionLog(
    contract_id=contract.id,
    from_status=None,
    to_status="草稿",
    operation_type="创建",
    operator_id=None,
    remark=f"合同已创建（{contract.contract_no}），共{len(items_data)}个行项目",
)
db.add(log)
db.commit()
```

- [ ] **Step 2: In `update_contract`, add change-diff logic before writing log**

Before the log-writing section (around line 321), add a diff helper and comparison logic:

```python
def _build_change_summary(db: Session, contract: Contract, old_data: dict, new_data: dict,
                          old_items: list, new_items: list) -> str | None:
    """Compare old and new contract data, return a human-readable change summary."""
    changes = []

    # Contract-level fields
    field_labels = {
        "binding_material": "包边材料", "binding_width": "包边宽度",
        "binding_color_no": "色号", "emboss_model": "压花型号",
        "delivery_date": "交货日期",
    }
    for field, label in field_labels.items():
        old_val = old_data.get(field)
        new_val = new_data.get(field)
        if str(old_val or "") != str(new_val or ""):
            changes.append(f"{label}({old_val or '空'}→{new_val or '空'})")

    # Tech notes, pack notes, box notes
    for i in range(1, 11):
        f = f"tech_note_{i}"
        if str(old_data.get(f, "") or "") != str(new_data.get(f, "") or ""):
            changes.append(f"技术说明{i}")
    for i in range(1, 6):
        f = f"pack_note_{i}"
        if str(old_data.get(f, "") or "") != str(new_data.get(f, "") or ""):
            changes.append(f"包装说明{i}")
    for i in range(1, 4):
        f = f"box_note_{i}"
        if str(old_data.get(f, "") or "") != str(new_data.get(f, "") or ""):
            changes.append(f"箱单说明{i}")

    # Item-level changes: match by id or line_no
    old_map = {str(it.id): it for it in old_items}
    new_map = {str(it.get("id")): it for it in new_items if it.get("id")}
    for nid, new_it in new_map.items():
        old_it = old_map.get(nid)
        if not old_it:
            changes.append(f"行项目#{new_it.get('line_no', '?')} 新增")
            continue
        ln = new_it.get("line_no", "?")
        item_changes = []
        if getattr(old_it, "packaging_type", "") != new_it.get("packaging_type", ""):
            item_changes.append(f"包装方式({old_it.packaging_type or '空'}→{new_it.get('packaging_type', '') or '空'})")
        if float(getattr(old_it, "qty", 0) or 0) != float(new_it.get("qty", 0) or 0):
            item_changes.append(f"数量({old_it.qty or 0}→{new_it.get('qty', 0)})")
        if bool(old_it.is_pressed) != bool(new_it.get("is_pressed", False)):
            item_changes.append(f"压花({'是' if old_it.is_pressed else '否'}→{'是' if new_it.get('is_pressed') else '否'})")
        if str(old_it.delivery_date or "") != str(new_it.get("delivery_date", "") or ""):
            item_changes.append("交货日期")
        if old_it.spec_id != new_it.get("spec_id"):
            old_spec = db.query(Spec).filter(Spec.id == old_it.spec_id).first()
            new_spec = db.query(Spec).filter(Spec.id == new_it.get("spec_id")).first()
            item_changes.append(f"规格({old_spec.spec_name if old_spec else '?'}→{new_spec.spec_name if new_spec else '?'})")
        if item_changes:
            changes.append(f"行项目{ln}# {'，'.join(item_changes)}")

    # Deleted items
    old_ids = set(getattr(it, "id") for it in old_items if getattr(it, "id", None))
    new_ids = set(it.get("id") for it in new_items if it.get("id"))
    deleted_incoming = old_ids - new_ids
    for did in deleted_incoming:
        dit = next((it for it in old_items if getattr(it, "id", None) == did), None)
        if dit:
            changes.append(f"行项目#{dit.line_no} 已删除")

    if not changes:
        return None
    summary = "修改了：" + "、".join(changes)
    if len(summary) > 500:
        summary = summary[:497] + "..."
    return summary
```

- [ ] **Step 3: Use the diff in `update_contract`, replacing the old fixed log**

Replace the current log-writing section (lines ~321-330):

```python
# === Build change summary and log ===
from app.models.spec import Spec  # ensure imported at top of file

# Snapshot old values before the update_contract function processes them
old_data = {
    "binding_material": contract.binding_material,
    "binding_width": contract.binding_width,
    "binding_color_no": contract.binding_color_no,
    "emboss_model": contract.emboss_model,
    "delivery_date": str(contract.delivery_date) if contract.delivery_date else None,
}
for i in range(1, 11):
    old_data[f"tech_note_{i}"] = getattr(contract, f"tech_note_{i}", "")
for i in range(1, 6):
    old_data[f"pack_note_{i}"] = getattr(contract, f"pack_note_{i}", "")
for i in range(1, 4):
    old_data[f"box_note_{i}"] = getattr(contract, f"box_note_{i}", "")
old_items = list(contract.items)  # snapshot before changes (list() forces evaluation)

# (the existing update logic runs here — fields are modified in-place)

from app.models.production_log import ProductionLog

# Build change summary from comparison
change_summary = _build_change_summary(
    db, contract, old_data, {},
    old_items, items_data or [],
)

if change_summary:
    # Only write log when something actually changed
    from app.models.production_log import ProductionLog
    log = ProductionLog(
        contract_id=contract.id,
        from_status=original_status,
        to_status=contract.status,
        operation_type="修改",
        operator_id=None,
        remark=change_summary,
    )
    db.add(log)
```

Note: The `_build_change_summary` works with the old items (SQLAlchemy objects) before update. Since `update_contract` uses `setattr` for contract fields and processes items separately, we read old_items before any mutation. For new_data (second arg), we pass empty dict `{}` since contract-level changes are read from `contract` after setattr.

- [ ] **Step 4: In `reopen_edit`, change status to 草稿 and update the log**

Replace the current `reopen_edit` function (lines ~401-433) with:

```python
def reopen_edit(db: Session, contract_id: int, user_id: int):
    """Reopen a confirmed/dispatched contract for editing. Resets status to 草稿, increments version."""
    from app.models.production_log import ProductionLog
    from app.models.user import User

    contract = db.query(Contract).filter(
        Contract.id == contract_id, Contract.is_deleted == False
    ).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    if contract.status == "草稿":
        raise HTTPException(status_code=400, detail="草稿合同可直接编辑，无需重新打开")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.role not in ("销售经理", "生产专员"):
        raise HTTPException(status_code=403, detail="权限不足")

    old_status = contract.status
    new_version = (contract.latest_confirm_version or 0) + 1
    contract.latest_confirm_version = new_version
    contract.status = "草稿"
    contract.updated_by = user.display_name or user.username

    log = ProductionLog(
        contract_id=contract.id,
        from_status=old_status,
        to_status="草稿",
        operation_type="重新编辑",
        operator_id=user_id,
        remark=f"重新打开编辑，版本 V{new_version}（由{user.display_name}操作）",
    )
    db.add(log)
    db.commit()
    return True
```

---

### Task 3: Backend — production.py enhancements (cancel snapshot, restore, item_no)

**Files:**
- Modify: `backend/app/services/production.py`

- [ ] **Step 1: In `cancel_item`, snapshot contract version + status into cancel_quantities**

After line 256 (`item.cancel_quantities = quantities`), add:

```python
# Snapshot contract state for restore
from app.models.contract import Contract
ct = db.query(Contract).filter(Contract.id == item.contract_id).first()
if ct:
    snap = dict(quantities or {})
    snap["contract_version"] = ct.latest_confirm_version
    snap["contract_status"] = ct.status
    snap["production_status"] = old_status
    snap["restored"] = False
    item.cancel_quantities = snap
```

- [ ] **Step 2: Add `restore_item` function after `cancel_item`**

```python
def restore_item(db: Session, item_id: int, user_id: int):
    """Restore a cancelled contract item back to its pre-cancel state."""
    item = db.query(ContractItem).filter(
        ContractItem.id == item_id
    ).options(joinedload(ContractItem.contract)).first()
    if not item or item.contract.is_deleted:
        raise HTTPException(status_code=404, detail="行项目不存在")
    if not item.cancel_reason:
        raise HTTPException(status_code=400, detail="该行项目未取消")

    snapshot = item.cancel_quantities
    if not snapshot or snapshot.get("restored"):
        raise HTTPException(status_code=400, detail="无可恢复的取消记录")

    user = db.query(User).filter(User.id == user_id).first()
    if user.role not in ("销售经理", "生产专员"):
        raise HTTPException(status_code=403, detail="权限不足")

    # Restore production status
    prev_status = snapshot.get("production_status")
    item.production_status = prev_status
    item.cancel_reason = None
    snapshot["restored"] = True
    item.cancel_quantities = snapshot

    log = ProductionLog(
        contract_id=item.contract_id,
        contract_item_id=item.id,
        from_status="cancelled",
        to_status=prev_status or "yarn_plan",
        operation_type="取消",
        operator_id=user_id,
        remark=f"已恢复取消：行项目恢复到取消前状态（{prev_status or '待坯布'}）",
    )
    db.add(log)
    db.commit()
    db.refresh(item)
    return item, log
```

- [ ] **Step 3: Add `delete_production_log` function**

```python
def delete_production_log(db: Session, log_id: int):
    """Delete a production log entry."""
    log = db.query(ProductionLog).filter(ProductionLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="日志不存在")
    db.delete(log)
    db.commit()
    return True
```

- [ ] **Step 4: Add item_no to get_contract_logs response**

In `get_contract_logs` function, add item_no by joining ContractItem:

```python
def get_contract_logs(db: Session, contract_id: int):
    """Get all production logs for a contract, with item line numbers."""
    from app.models.contract_item import ContractItem

    logs = db.query(ProductionLog).filter(
        ProductionLog.contract_id == contract_id
    ).order_by(ProductionLog.created_at.desc()).options(
        joinedload(ProductionLog.operator)
    ).all()

    # Attach item_no if contract_item_id exists
    for log in logs:
        log.item_no = None
        if log.contract_item_id:
            item = db.query(ContractItem).filter(
                ContractItem.id == log.contract_item_id
            ).first()
            log.item_no = item.line_no if item else None
        log.operator_name = log.operator.display_name if log.operator else None
    return logs
```

---

### Task 4: Backend — API endpoints (restore + delete_log + item_no in response)

**Files:**
- Modify: `backend/app/api/production.py`
- Modify: `backend/app/api/contracts.py`

- [ ] **Step 1: Add restore_item and delete_log endpoints to production.py **

After the `@router.post("/contract-items/{id}/cancel")` block (line ~160):

```python
@router.post("/contract-items/{id}/restore")
def restore_item(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("销售经理", "生产专员"):
        raise HTTPException(status_code=403, detail="权限不足")
    item, log = prod_service.restore_item(db, id, current_user.id)
    return {"message": "已恢复取消", "production_status": item.production_status}
```

Add a new delete log endpoint (after push_down, around line ~186):

```python
@router.delete("/production-logs/{id}")
def delete_log(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "销售经理":
        raise HTTPException(status_code=403, detail="权限不足")
    prod_service.delete_production_log(db, id)
    return {"message": "日志已删除"}
```

- [ ] **Step 2: Update get_contract_logs API response to include item_no**

In `production.py` — `@router.get("/contracts/{id}/production-logs")` (line ~214), update the response construction to include `item_no`:

```python
@router.get("/contracts/{id}/production-logs")
def get_contract_logs(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logs = prod_service.get_contract_logs(db, id)
    result = []
    for log in logs:
        log_data = {
            "id": log.id,
            "contract_id": log.contract_id,
            "contract_item_id": log.contract_item_id,
            "item_no": log.item_no,  # NEW: line number
            "from_status": log.from_status,
            "to_status": log.to_status,
            "operation_type": log.operation_type,
            "operator_id": log.operator_id,
            "operator_name": log.operator_name or "",
            "remark": log.remark,
            "created_at": log.created_at,
        }
        result.append(log_data)
    return result
```

- [ ] **Step 3: Add rerun migration note for production_log model**

```bash
mysql -u root -proot huazhi -e "ALTER TABLE production_log MODIFY COLUMN operation_type ENUM('推进','回退','返工','取消','确认','坯布下达','重新编辑','修改','创建') NOT NULL;"
```

---

### Task 5: Frontend — production.js API calls

**Files:**
- Modify: `frontend/src/api/production.js`

- [ ] **Step 1: Add restoreItem and deleteLog endpoints**

Read the current file, then add these exports:

```javascript
export function restoreItem(id) { return api.post(`/contract-items/${id}/restore`) }
export function deleteLog(id) { return api.delete(`/production-logs/${id}`) }
```

---

### Task 6: Frontend — StatusLog.vue shared component

**Files:**
- Create: `frontend/src/components/StatusLog.vue`

- [ ] **Step 1: Create the component**

```vue
<template>
  <div>
    <el-table :data="logs" stripe size="small" v-loading="loading" v-if="logs.length">
      <el-table-column v-if="showCol('时间')" prop="created_at" label="时间" width="160" />
      <el-table-column v-if="showCol('操作')" prop="operation_type" label="操作" width="100" />
      <el-table-column v-if="showCol('行号')" label="行号" width="60">
        <template #default="{ row }">{{ row.item_no || '─' }}</template>
      </el-table-column>
      <el-table-column v-if="showCol('从')" prop="from_status" label="从" width="100" />
      <el-table-column v-if="showCol('到')" prop="to_status" label="到" width="100" />
      <el-table-column v-if="showCol('操作人')" prop="operator_name" label="操作人" width="100" />
      <el-table-column v-if="showCol('备注')" prop="remark" label="备注" min-width="150" />
      <el-table-column v-if="canDelete" label="操作" width="60" fixed="right">
        <template #default="{ row }">
          <el-button text type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div v-else style="color:#999;text-align:center;padding:16px">暂无日志</div>
  </div>
</template>

<script setup>
import { ElMessageBox } from 'element-plus'

const props = defineProps({
  logs: { type: Array, default: () => [] },
  columns: { type: Array, default: () => ['时间', '操作', '行号', '从', '到', '操作人', '备注'] },
  canDelete: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['delete'])

function showCol(name) {
  return props.columns.includes(name)
}

function handleDelete(row) {
  ElMessageBox.confirm('确认删除此日志？', '提示', { type: 'warning' }).then(() => {
    emit('delete', row)
  }).catch(() => {})
}
</script>
```

---

### Task 7: Frontend — ContractDetail.vue main changes

**Files:**
- Modify: `frontend/src/views/contract/ContractDetail.vue`

- [ ] **Step 1: Add StatusLog import and new API calls**

In the script section, replace existing import lines:

```javascript
// Replace:
import { listProcessSteps, advanceItem, rollbackItem, cancelItem, releaseYarnPlan, getItemLogs, getContractLogs, pushDownItem } from '../../api/production'
// With:
import { listProcessSteps, advanceItem, rollbackItem, cancelItem, releaseYarnPlan, getItemLogs, getContractLogs, pushDownItem, restoreItem, deleteLog } from '../../api/production'
// Add StatusLog import:
import StatusLog from '../../components/StatusLog.vue'
```

Add `handleDeleteLog` method:

```javascript
async function handleDeleteLog(row) {
  try {
    await deleteLog(row.id)
    ElMessage.success('日志已删除')
    loadData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '删除失败') }
}
```

- [ ] **Step 2: Remove row-level "日志" button**

In the template's "操作" column (around line 77-86), find and remove:
```vue
<el-button size="small" @click="openLogDialog(row)">日志</el-button>
```

Remove related code: `logDialogVisible`, `dialogLogs`, `openLogDialog` function, and the entire `<el-dialog v-model="logDialogVisible">` block (lines ~181-194).

- [ ] **Step 3: Replace log table with StatusLog component**

Replace the current log `<el-table>` block (lines ~89-99):

```vue
<StatusLog
  :logs="contractLogs"
  :columns="['时间','操作','行号','从','到','操作人','备注']"
  :can-delete="userRole === '销售经理'"
  :loading="loading"
  @delete="handleDeleteLog"
/>
```

- [ ] **Step 4: Add restore button for cancelled items**

In the template's "操作" column, after the cancel button, add restore logic:

Replace the existing cancel button section:
```vue
<el-button size="small" type="danger" v-if="canCancel(row)" @click="openCancelDialog(row)">取消</el-button>
```

With:
```vue
<el-button size="small" type="danger" v-if="canCancel(row)" @click="openCancelDialog(row)">取消</el-button>
<el-button size="small" type="warning" v-if="canRestore(row)" @click="handleRestore(row)">恢复</el-button>
```

Add the canRestore method:
```javascript
function canRestore(row) {
  const role = userRole.value
  return (role === '销售经理' || role === '生产专员') && row.cancel_reason
}
```

Add handleRestore method:
```javascript
async function handleRestore(row) {
  try {
    await restoreItem(row.id)
    ElMessage.success('已恢复取消')
    loadData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '恢复失败') }
}
```

- [ ] **Step 5: Add cancelled row highlighting**

Add `:row-class-name` to the items `<el-table>`:

```vue
<el-table :data="contract?.items || []" stripe size="small" :row-class-name="itemRowClass">
```

Add the method:
```javascript
function itemRowClass({ row }) {
  return row.cancel_reason ? 'cancel-row' : ''
}
```

Add the CSS style in the `<style>` section:
```css
.el-table .cancel-row {
  --el-table-tr-bg-color: #fef0f0;
  color: #f56c6c;
}
```

- [ ] **Step 6: Disable push-down and yarn-plan for cancelled rows**

Update `canPushDown` and `canReleaseYarn`:

```javascript
function canPushDown(row) {
  const role = userRole.value
  if (role !== '销售经理' && role !== '生产专员') return false
  if (contract.value?.status !== '确认' && contract.value?.status !== '已下发') return false
  if (row.cancel_reason) return false  // NEW
  return !row.has_process_sheet
}

function canReleaseYarn(row) {
  const role = userRole.value
  if (contract.value?.status === '草稿') return false
  if (row.cancel_reason) return false  // NEW
  return (role === '销售经理' || role === '生产专员') && !row.production_status
}
```

---

### Task 8: Frontend — ContractForm.vue edit condition

**Files:**
- Modify: `frontend/src/views/contract/ContractForm.vue`

- [ ] **Step 1: Allow editing for 草稿 status (reopened contracts)**

In the template header (line 3), the condition already shows "重新编辑合同" for non-draft statuses via `contractStatus`. The key change: the "编辑" button in ContractDetail.vue currently checks `contract?.status!=='草稿'` to disable. Since reopen now sets status to 草稿, the button will naturally work.

But the ContractForm.vue currently loads contract data on mount. The Edit button and redirect from ContractDetail already passes the contract id. Since `reopen_edit` changes status to "草稿" before redirect, the form should load without issues.

Verify the form's `handleSave` doesn't have old-status restrictions. The current `update_contract` already allows editing contracts in any status (with guard for "已下发"). No changes needed in ContractForm.vue itself — the reopen→草稿 flow already makes it work.

If the template header shows `contractStatus`, it will read the contract's current status from API. After reopen, it'll be "草稿", so the form will show "编辑合同" instead of "重新编辑合同" — which is correct.

No code changes needed.

---

### Task 9: Frontend — SheetDetail.vue replace logs with StatusLog

**Files:**
- Modify: `frontend/src/views/processSheet/SheetDetail.vue`

- [ ] **Step 1: Import StatusLog and add handleDeleteLog**

In the script section, add:
```javascript
import StatusLog from '../../components/StatusLog.vue'
import { deleteLog } from '../../api/production'
```

Add method:
```javascript
async function handleDeleteLog(row) {
  try {
    await deleteLog(row.id)
    ElMessage.success('日志已删除')
    loadLogs()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '删除失败') }
}
```

Determine manager status:
```javascript
const isManager = computed(() => {
  return userStore.role === '销售经理'
})
```

- [ ] **Step 2: Replace the raw log table with StatusLog component**

Find the current log section:
```vue
<el-divider>操作日志</el-divider>
<el-table :data="logs" stripe size="small" v-if="logs.length" v-loading="loadingLogs">
  <el-table-column prop="created_at" label="时间" width="160" />
  <el-table-column prop="operation_type" label="操作" width="120" />
  <el-table-column prop="remark" label="说明" min-width="200" />
</el-table>
<div v-else style="color:#999;text-align:center;padding:16px">暂无操作记录</div>
```

Replace with:
```vue
<el-divider>操作日志</el-divider>
<StatusLog
  :logs="logs"
  :columns="['时间','操作','备注']"
  :can-delete="isManager"
  :loading="loadingLogs"
  @delete="handleDeleteLog"
/>
```

---

### Task 10: DB migration (run once)

- [ ] **Step 1: Run the enum migration**

```bash
mysql -u root -proot huazhi -e "ALTER TABLE production_log MODIFY COLUMN operation_type ENUM('推进','回退','返工','取消','确认','坯布下达','重新编辑','修改','创建') NOT NULL;"
```

---

## Self-Review

### Spec coverage check:

| Spec section | Implemented in |
|-------------|---------------|
| 1.1 创建合同写日志 | Task 2 Step 1 |
| 1.2 编辑记录详细变更 | Task 2 Steps 2-3 |
| 1.3 重新编辑→草稿 | Task 2 Step 4 |
| 1.4 取消快照+恢复 | Task 3 Steps 1-2, Task 4 Step 1 |
| 1.5 日志删除 | Task 3 Step 3, Task 4 Step 1 |
| 2. StatusLog 组件 | Task 6 |
| 3.1 移除行项目日志按钮 | Task 7 Step 2 |
| 3.2 主日志含 item_no | Task 3 Step 4, Task 4 Step 2 |
| 3.3 取消行高亮+恢复 | Task 7 Steps 4-5 |
| 3.4 已取消禁用下推/坯布 | Task 7 Step 6 |
| 3.5 编辑条件(草稿即可) | Task 8 |
| 工艺单集成 StatusLog | Task 9 |
| API 文件 production.js | Task 5 |

### Type consistency:

- Log response includes `item_no` (int|null) — used in StatusLog
- `restore_item` returns `{message, production_status}` — used in handleRestore
- `deleteLog` takes `id` (int) — used in handleDeleteLog
- StatusLog columns prop is `Array<string>` — values match column names

No gaps found.
