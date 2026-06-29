# V2 全流程生产管理 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将合同确认流程从"客户公开链接确认"改为"销售经理企微群确认 + 管理员手动确认（带意见）"，生产改为双线并行（坯布计划线 + 工艺单线），行项目级别下推工艺单，客户确认移到工艺单层面。

**Architecture:** 基于已存在的 V1 生产管理代码（ProcessStep、ProductionLog、ContractItem 扩展字段），主要修改 contract 状态枚举/确认流程，新增 contract manual-confirm API，修改 process sheet 增加客户确认字段，调整 frontend contract detail 页面。

**Tech Stack:** Python FastAPI/SQLAlchemy + Vue 3/Element Plus + MySQL

---

### Task 1: 数据库迁移 — contract 状态枚举和字段变更

**Files:**
- Modify: `backend/app/models/contract.py:74` — 修改 status 枚举
- Create: `backend/migrate_v2_contract_status.py` — 迁移脚本

- [ ] **Step 1: 修改 Contract 模型 status 枚举**

```python
# backend/app/models/contract.py, line 74
status = Column(SAEnum("草稿", "确认", "已下发"), default="草稿")
```

- [ ] **Step 2: 删除不再需要的字段**

删除 `confirm_token`, `customer_comment`, `latest_confirm_version` 字段。

- [ ] **Step 3: 创建迁移脚本**

```python
# backend/migrate_v2_contract_status.py
"""V2: contract status 草稿/保存/已下发 → 草稿/确认/已下发"""
from app.database import engine, SessionLocal
from sqlalchemy import text

def migrate():
    db = SessionLocal()
    try:
        # 修改 ENUM 定义
        db.execute(text("ALTER TABLE contract MODIFY COLUMN status VARCHAR(20) NOT NULL DEFAULT '草稿'"))
        db.execute(text("UPDATE contract SET status = '确认' WHERE status = '保存'"))
        db.execute(text("ALTER TABLE contract DROP COLUMN confirm_token"))
        db.execute(text("ALTER TABLE contract DROP COLUMN customer_comment"))
        db.execute(text("ALTER TABLE contract DROP COLUMN latest_confirm_version"))
        db.commit()
        print("Migration complete: contract status 草稿/确认/已下发")
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
```

- [ ] **Step 4: 回退时先备份数据**

Run: `python backend/migrate_v2_contract_status.py` (safety: first backup the DB)

---

### Task 2: 后端 — 合同确认 API（手动确认 + 经理确认）

**Files:**
- Modify: `backend/app/services/contract.py` — 新增 manual_confirm 和 confirm 函数
- Modify: `backend/app/api/contracts.py` — 新增手动确认端点，删除旧确认端点
- Modify: `backend/app/schemas/contract.py` — ContractCreate/Update status 更新
- Modify: `backend/app/services/contract.py:compute_contract_status` — 适配新状态

- [ ] **Step 1: Contract schemas 更新 status 枚举**

```python
# backend/app/schemas/contract.py:ContractOut
status: str = "草稿"
# 移除: computed_status 保持不变
```

ContractOut 中移除 `confirm_token`, `customer_comment`, `latest_confirm_version`。

- [ ] **Step 2: Contract service 增加 manual_confirm 函数**

```python
# backend/app/services/contract.py

def manual_confirm_contract(db: Session, contract_id: int, user_id: int, remark: str) -> Contract:
    """管理员手动确认合同，需带确认意见。"""
    from app.models.contract import Contract
    from app.models.production_log import ProductionLog
    from app.models.user import User
    
    contract = db.query(Contract).filter(
        Contract.id == contract_id, Contract.is_deleted == False
    ).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    if contract.status == "已下发":
        raise HTTPException(status_code=400, detail="合同已下发，不可确认")
    if contract.status == "确认":
        raise HTTPException(status_code=400, detail="合同已确认")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.role != "销售经理":
        # Allow admin (username='admin') to bypass role check
        if user.username != "admin":
            raise HTTPException(status_code=403, detail="仅管理员可手动确认")
    
    old_status = contract.status
    contract.status = "确认"
    contract.updated_by = user.display_name or user.username
    
    # Record in production_log
    log = ProductionLog(
        contract_id=contract.id,
        from_status=old_status,
        to_status="确认",
        operation_type="确认",
        operator_id=user.id,
        remark=f"手动确认: {remark}" if remark else "手动确认",
    )
    db.add(log)
    db.commit()
    db.refresh(contract)
    return contract
```

- [ ] **Step 3: 更新 compute_contract_status 适配新状态**

```python
# backend/app/services/contract.py

def compute_contract_status(db: Session, contract_id: int, items: list = None) -> str:
    if items is None:
        items = db.query(ContractItem).filter(
            ContractItem.contract_id == contract_id
        ).all()
    if not items:
        return "草稿"
    statuses = [i.production_status for i in items]
    has_any = any(s for s in statuses)
    all_cancelled = all(s == "cancelled" for s in statuses if s) and has_any
    all_completed = all(s == "completed" for s in statuses if s) and has_any
    any_production = any(s and s not in ("cancelled", "completed") for s in statuses)
    
    if all_cancelled:
        return "已取消"
    if all_completed:
        return "已完成"
    if any_production:
        return "已下发"
    if has_any:
        return "确认"
    return "草稿"
```

- [ ] **Step 4: 更新 contract API 添加手动确认端点**

```python
# backend/app/api/contracts.py

from pydantic import BaseModel

class ManualConfirmRequest(BaseModel):
    remark: str  # 确认意见，必填

@router.post("/{id}/manual-confirm")
def manual_confirm(
    id: int,
    data: ManualConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not data.remark or not data.remark.strip():
        raise HTTPException(status_code=400, detail="确认意见不能为空")
    result = service.manual_confirm_contract(db, id, current_user.id, data.remark.strip())
    if not result:
        raise HTTPException(status_code=404, detail="合同不存在")
    return result
```

- [ ] **Step 5: 删除旧确认端点并清理 imports**

Remove: `POST /{id}/confirm-image`, `POST /{id}/confirm`, `POST /{id}/generate-confirm-link`, `GET /{id}/versions`

- [ ] **Step 6: 运行测试验证**

Run: `cd backend && python -m pytest tests/test_contract.py -v`
Expected: PASS or adapt tests for new status

---

### Task 3: 前端 — 合同详情页添加手动确认按钮

**Files:**
- Modify: `frontend/src/views/contract/ContractDetail.vue` — 添加手动确认按钮和对话框
- Modify: `frontend/src/api/contract.js` — 添加 manualConfirm API

- [ ] **Step 1: API 封装**

```javascript
// frontend/src/api/contract.js
export function manualConfirm(id, data) { return api.post(`/contracts/${id}/manual-confirm`, data) }
```

- [ ] **Step 2: ContractDetail.vue 添加手动确认按钮（仅 admin 可见）**

```javascript
// 在 script setup 中
const isAdmin = computed(() => {
  try {
    const token = localStorage.getItem('token')
    if (!token) return false
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.sub === 'admin' // or check username
  } catch { return false }
})
```

在 template 合同头部按钮区添加：
```html
<el-button 
  v-if="isAdmin && contract?.status==='草稿'" 
  size="small" type="danger"
  @click="manualConfirmDialogVisible = true">
  手动确认
</el-button>
```

- [ ] **Step 3: 添加手动确认对话框**

```html
<el-dialog v-model="manualConfirmDialogVisible" title="手动确认合同" width="420px">
  <el-form>
    <el-form-item label="合同号">{{ contract?.contract_no }}</el-form-item>
    <el-form-item label="确认意见" required>
      <el-input v-model="manualConfirmRemark" type="textarea" :rows="3" placeholder="请填写确认意见（必填）" />
    </el-form-item>
  </el-form>
  <template #footer>
    <el-button @click="manualConfirmDialogVisible = false">取消</el-button>
    <el-button type="danger" :loading="dialogLoading" @click="handleManualConfirm">确认</el-button>
  </template>
</el-dialog>
```

- [ ] **Step 4: handleManualConfirm 逻辑**

```javascript
async function handleManualConfirm() {
  if (!manualConfirmRemark.value?.trim()) {
    ElMessage.warning('请填写确认意见')
    return
  }
  dialogLoading.value = true
  try {
    await manualConfirm(route.params.id, { remark: manualConfirmRemark.value })
    ElMessage.success('合同已手动确认')
    manualConfirmDialogVisible.value = false
    loadData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '操作失败') }
  finally { dialogLoading.value = false }
}
```

- [ ] **Step 5: 清理旧合同确认按钮（生成确认图、生成确认链接、标记客户确认）**

Remove buttons from ContractDetail.vue header:
- `生成确认图` 
- `生成确认链接`/`复制确认链接`
- `标记客户确认`

These are replaced by the manager confirm flow.

- [ ] **Step 6: 验证前端编译**

Run: `cd frontend && npx vite build`
Expected: Build success

---

### Task 4: 后端 — 行项目级别下推工艺单

**Files:**
- Modify: `backend/app/services/production.py` — 添加 push_down 函数
- Modify: `backend/app/api/production.py` — 添加 push-down 端点

- [ ] **Step 1: Production service 添加 push_down 函数**

```python
# backend/app/services/production.py

def push_down_item_to_process_sheet(db: Session, item_id: int, user_id: int):
    """行项目下推为工艺单。"""
    from app.models.contract_item import ContractItem
    from app.models.process_sheet import ProcessSheet
    from app.models.process_sheet_item import ProcessSheetItem
    from app.models.contract import Contract
    from app.models.production_log import ProductionLog
    from app.models.user import User
    
    item = db.query(ContractItem).filter(ContractItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="行项目不存在")
    
    contract = db.query(Contract).filter(Contract.id == item.contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    if contract.status == "草稿":
        raise HTTPException(status_code=400, detail="合同未确认，无法下推")
    
    # Check if already pushed down
    existing = db.query(ProcessSheetItem).filter(
        ProcessSheetItem.contract_item_id == item_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该行项目已下推工艺单")
    
    # Find or create process sheet for this contract
    sheet = db.query(ProcessSheet).filter(
        ProcessSheet.contract_id == contract.id,
        ProcessSheet.is_deleted == False,
    ).first()
    if not sheet:
        from datetime import date
        today = date.today()
        seq = db.query(ProcessSheet).count() + 1
        sheet = ProcessSheet(
            contract_id=contract.id,
            sheet_no=f"GY{today.strftime('%Y%m')}{seq:04d}",
            confirm_version_no=0,
            status="草稿",
            created_by=contract.updated_by or contract.created_by,
            updated_by=contract.updated_by or contract.created_by,
        )
        db.add(sheet)
        db.flush()
    
    # Create process sheet item
    sheet_item = ProcessSheetItem(
        process_sheet_id=sheet.id,
        contract_item_id=item.id,
        line_no=item.line_no,
        spec_id=item.spec_id,
        is_pressed=item.is_pressed,
        packaging_type=item.packaging_type or "",
        delivery_date=item.delivery_date,
        pattern_count=item.pattern_count or 0,
        pattern_data=item.pattern_data,
        pattern_code=item.pattern_code or "",
        color_a=item.color_a or "",
        image_a_1=item.image_a_1 or "",
        image_a_2=item.image_a_2 or "",
        image_a_3=item.image_a_3 or "",
        color_b=item.color_b or "",
        image_b_1=item.image_b_1 or "",
        image_b_2=item.image_b_2 or "",
        image_b_3=item.image_b_3 or "",
        remark=item.remark or "",
    )
    db.add(sheet_item)
    
    # Update contract status to 已下发
    if contract.status != "已下发":
        contract.status = "已下发"
    
    user = db.query(User).filter(User.id == user_id).first()
    log = ProductionLog(
        contract_id=contract.id,
        contract_item_id=item.id,
        from_status=item.production_status,
        to_status="push_down",
        operation_type="推进",
        operator_id=user_id,
        remark=f"下推工艺单: {sheet.sheet_no}",
    )
    db.add(log)
    db.commit()
    return sheet
```

- [ ] **Step 2: 添加 push-down API 端点**

```python
# backend/app/api/production.py

class PushDownRequest(BaseModel):
    pass

@router.post("/contract-items/{id}/push-down")
def push_down_item(
    id: int,
    data: PushDownRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("销售经理", "生产专员"):
        raise HTTPException(status_code=403, detail="权限不足")
    result = prod_service.push_down_item_to_process_sheet(db, id, current_user.id)
    if not result:
        raise HTTPException(status_code=400, detail="下推失败")
    return result
```

---

### Task 5: 前端 — 行项目下推工艺单按钮

**Files:**
- Modify: `frontend/src/views/contract/ContractDetail.vue` — 下推工艺单按钮
- Modify: `frontend/src/api/production.js` — 添加 pushDown API

- [ ] **Step 1: API 封装**

```javascript
// frontend/src/api/production.js
export function pushDownItem(id) { return api.post(`/contract-items/${id}/push-down`, {}) }
```

- [ ] **Step 2: ContractDetail.vue 下推工艺单按钮**

在「操作」列中，已确认状态显示「下推工艺单」按钮，替换旧的「下推工艺单」按钮（原为合同级别）。

```javascript
// 判断逻辑
function canPushDown(row) {
  const role = userRole.value
  if (role !== '销售经理' && role !== '生产专员') return false
  if (contract.value?.status !== '确认' && contract.value?.status !== '已下发') return false
  // Check if already pushed down — need a flag on the row or check via API
  return !row.has_process_sheet
}
```

```html
<el-button size="small" type="primary" @click="handlePushDownItem(row)" 
  :disabled="!canPushDown(row)">
  下推工艺单
</el-button>
```

---

### Task 6: 后端 — compute_contract_status 适配双线并行

**Files:**
- Modify: `backend/app/services/contract.py:compute_contract_status` — 适配新状态映射

- [ ] **Step 1: 更新 compute_contract_status**

```python
def compute_contract_status(db: Session, contract_id: int, items: list = None) -> str:
    """Derive display status from items' production_status."""
    if items is None:
        items = db.query(ContractItem).filter(
            ContractItem.contract_id == contract_id
        ).all()
    if not items:
        return "草稿"
    statuses = [i.production_status for i in items]
    has_any = any(s for s in statuses)
    all_cancelled = all(s == "cancelled" for s in statuses if s) and has_any
    all_completed = all(s == "completed" for s in statuses if s) and has_any
    any_production = any(s and s not in ("cancelled", "completed") for s in statuses)
    
    if all_cancelled:
        return "已取消"
    if all_completed:
        return "已完成"
    if any_production:
        return "已下发"
    if has_any:
        return "确认"
    return "草稿"
```

---

### Task 7: 前端 — 合同详情页状态列适配

**Files:**
- Modify: `frontend/src/views/contract/ContractDetail.vue` — 进度列显示优化
- Modify: `frontend/src/views/contract/ContractList.vue` — 状态列更新

- [ ] **Step 1: 更新状态类型函数**

```javascript
function statusType(s) {
  if (s === '草稿') return 'warning'
  if (s === '确认') return 'success'
  if (s === '已下发') return 'primary'
  return 'info'
}
```

- [ ] **Step 2: 更新按钮规则**

Update `canReleaseYarn` to check contract status:
```javascript
function canReleaseYarn(row) {
  const role = userRole.value
  if (contract.value?.status !== '确认' && contract.value?.status !== '已下发') return false
  return (role === '销售经理' || role === '生产专员') && !row.production_status
}
```

---

### Task 8: 工艺单客户确认（从合同迁移）

**Files:**
- Modify: `backend/app/models/process_sheet.py` — 加 confirm_token, customer_comment
- Modify: `backend/app/services/process_sheet.py` — 加 generate_confirm_link, mark_confirmed
- Modify: `backend/app/api/process_sheets.py` — 加确认端点
- Modify: `backend/app/api/public.py` — 工艺单公开确认端点

- [ ] **Step 1: ProcessSheet 模型添加字段**

```python
# backend/app/models/process_sheet.py
confirm_token = Column(String(36), unique=True, nullable=True)
customer_comment = Column(Text)
```

- [ ] **Step 2: 创建迁移脚本**

```sql
ALTER TABLE process_sheet ADD COLUMN confirm_token VARCHAR(36) UNIQUE;
ALTER TABLE process_sheet ADD COLUMN customer_comment TEXT;
```

- [ ] **Step 3: Process sheet service 添加确认链接和确认逻辑**

(迁移自 contract service 和 confirm_image service, 移除版本号逻辑, 改用 production_log)

- [ ] **Step 4: 公开 API 从 /api/public/contract/{token} 改为 /api/public/process-sheet/{token}**

---

### Task 9: 种子数据更新

**Files:**
- Modify: `backend/seed.py` — 更新 process_step 种子数据支持双线

- [ ] **Step 1: 更新 process_step 种子数据**

```python
# backend/seed.py — process_step 种子
process_steps = [
    {"step_code": "yarn_plan_released", "step_name": "坯布计划已下达", "sort_order": 0},
    {"step_code": "weaving", "step_name": "织造中", "sort_order": 1},
    {"step_code": "weaving_done", "step_name": "织造完成", "sort_order": 2},
    {"step_code": "setting", "step_name": "定型中", "sort_order": 3},
    {"step_code": "setting_done", "step_name": "定型完成", "sort_order": 4},
    {"step_code": "brushing", "step_name": "刷毛烫光中", "sort_order": 5},
    {"step_code": "brushing_done", "step_name": "刷毛烫光完成", "sort_order": 6},
    {"step_code": "printing", "step_name": "印花中", "sort_order": 7},
    {"step_code": "printing_done", "step_name": "印花完成", "sort_order": 8},
    {"step_code": "sewing", "step_name": "成品缝制", "sort_order": 9},
    {"step_code": "completed", "step_name": "成品完成", "sort_order": 10},
]
```

---

### Task 10: 企业微信通知集成

**Files:**
- Create: `backend/app/services/notify.py` — 通知服务
- Modify: `backend/app/services/production.py` — 在关键操作点调用 notify

- [ ] **Step 1: 创建 NotifyService**

- [ ] **Step 2: 在 advance/rollback/cancel/yarn-plan 操作中集成通知**

---

### Task 11: 外协人员专属任务页面

**Files:**
- Create: `frontend/src/views/production/MyTasks.vue` — 外协任务页面
- Modify: `frontend/src/router/index.js` — 添加路由

---

### Task 12: 全流程回归测试

- [ ] 合同草稿 → 手动确认 → 确认状态
- [ ] 确认后行项目可下达坯布计划
- [ ] 确认后行项目可下推工艺单
- [ ] 坯布计划线：下达→织造中→织造完成
- [ ] 工艺单线：下推→定型→刷毛→印花→成品
- [ ] 行项目取消
- [ ] 状态日志记录正确
- [ ] 外协人员仅看到自己的任务
