# 嘉元瑞通工厂管理系统 — 第1期 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成第1期 Web 端订单录入系统，覆盖从合同录入→客户确认→工艺单下发的完整闭环

**Architecture:** 前后端分离。Python FastAPI 提供 RESTful API，SQLAlchemy ORM 操作 MySQL，Vue 3 + Element Plus 做管理界面。图片自动压缩（Pillow），工艺单 PDF 打印（WeasyPrint）。

**Tech Stack:** FastAPI / SQLAlchemy / MySQL 8.0 / Vue 3 + Element Plus / Vite / Pillow / WeasyPrint

---

## 文件结构

```
backend/
  ├── app/
  │   ├── __init__.py
  │   ├── main.py                    # FastAPI 入口
  │   ├── config.py                  # 配置
  │   ├── database.py                # 数据库连接
  │   ├── models/
  │   │   ├── __init__.py
  │   │   ├── user.py                # 用户模型
  │   │   ├── customer.py            # 客户模型
  │   │   ├── spec.py                # 规格模型
  │   │   ├── contract.py            # 合同模型
  │   │   ├── contract_item.py       # 合同行项目模型
  │   │   ├── confirm_image.py       # 确认图版本模型
  │   │   └── process_sheet.py       # 工艺单模型
  │   ├── schemas/
  │   │   ├── __init__.py
  │   │   ├── user.py
  │   │   ├── customer.py
  │   │   ├── spec.py
  │   │   ├── contract.py
  │   │   ├── contract_item.py
  │   │   ├── confirm_image.py
  │   │   └── process_sheet.py
  │   ├── api/
  │   │   ├── __init__.py
  │   │   ├── auth.py                # 登录/注册
  │   │   ├── customers.py
  │   │   ├── specs.py
  │   │   ├── contracts.py
  │   │   ├── process_sheets.py
  │   │   └── upload.py              # 图片上传
  │   ├── services/
  │   │   ├── __init__.py
  │   │   ├── auth.py
  │   │   ├── customer.py
  │   │   ├── spec.py
  │   │   ├── contract.py
  │   │   ├── confirm_image.py
  │   │   └── process_sheet.py
  │   ├── utils/
  │   │   ├── __init__.py
  │   │   ├── image_compress.py      # 图片压缩
  │   │   ├── pdf_generator.py       # PDF 打印
  │   │   └── permissions.py         # 权限装饰器
  │   └── dependencies.py            # 依赖注入（获取当前用户等）
  ├── uploads/                       # 上传文件存储
  ├── requirements.txt
  └── alembic/                       # 数据库迁移

frontend/
  ├── src/
  │   ├── api/
  │   │   ├── index.js               # axios 实例
  │   │   ├── auth.js
  │   │   ├── customer.js
  │   │   ├── spec.js
  │   │   ├── contract.js
  │   │   └── processSheet.js
  │   ├── views/
  │   │   ├── login/
  │   │   │   └── Login.vue
  │   │   ├── dashboard/
  │   │   │   └── Dashboard.vue
  │   │   ├── customer/
  │   │   │   ├── CustomerList.vue
  │   │   │   └── CustomerForm.vue
  │   │   ├── spec/
  │   │   │   ├── SpecList.vue
  │   │   │   └── SpecForm.vue
  │   │   ├── contract/
  │   │   │   ├── ContractList.vue
  │   │   │   ├── ContractForm.vue
  │   │   │   └── ContractDetail.vue
  │   │   └── processSheet/
  │   │       ├── SheetList.vue
  │   │       ├── SheetForm.vue
  │   │       └── SheetDetail.vue
  │   ├── router/
  │   │   └── index.js
  │   ├── store/
  │   │   └── user.js
  │   ├── components/
  │   │   ├── ImageUploader.vue
  │   │   └── VersionHistory.vue
  │   ├── App.vue
  │   └── main.js
  └── package.json
```

---

### Task 1: 项目脚手架搭建

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `backend/app/main.py`

- [ ] **Step 1: 创建 requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.35
pymysql==1.1.1
cryptography==43.0.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.12
pillow==10.4.0
weasyprint==62.0
openpyxl==3.1.5
alembic==1.13.0
pydantic[email]==2.9.0
```

- [ ] **Step 2: 创建 config.py**

```python
import os

class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:root@localhost:3306/huazhi?charset=utf8mb4"
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    MAX_IMAGE_SIZE_MB: int = 10
    COMPRESS_QUALITY: int = 85
    COMPRESS_MAX_WIDTH: int = 1920

settings = Settings()
```

- [ ] **Step 3: 创建 database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import settings

engine = create_engine(settings.DATABASE_URL, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 4: 创建 main.py**

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.config import settings
import os

app = FastAPI(title="嘉元瑞通工厂管理系统", version="1.0.0")

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

@app.get("/api/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 5: 初始化前端项目**

```bash
mkdir -p frontend
cd frontend
npm init vite@latest . -- --template vue
npm install
npm install axios element-plus vue-router@4 pinia @element-plus/icons-vue
```

- [ ] **Step 6: 配置前端 main.js**

```javascript
import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'

const app = createApp(App)
app.use(ElementPlus)
app.use(router)
app.use(createPinia())
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
}
app.mount('#app')
```

- [ ] **Step 7: 创建 router/index.js 基础骨架**

```javascript
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', component: () => import('../views/login/Login.vue') },
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', component: () => import('../views/dashboard/Dashboard.vue') },
]

const router = createRouter({ history: createWebHistory(), routes })
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) next('/login')
  else next()
})
export default router
```

- [ ] **Step 8: 创建 .gitignore 并提交**

```
__pycache__/
*.pyc
.env
uploads/
node_modules/
dist/
*.db
```

```bash
git init
git add -A
git commit -m "chore: project scaffolding"
```

---

### Task 2: 数据库模型 — 用户 & 基础模型

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/user.py`

- [ ] **Step 1: 创建 models/\_\_init\_\_.py**

```python
from app.database import Base
from app.models.user import User
```

- [ ] **Step 2: 创建 user.py 模型**

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean
from app.database import Base

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    display_name = Column(String(100))
    role = Column(Enum("业务员", "销售经理", "生产专员"), nullable=False, default="业务员")
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
```

- [ ] **Step 3: 创建模型持久化基类 Mixin**

给所有模型添加通用字段。创建 `backend/app/models/mixins.py`：

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean

class TimestampMixin:
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class SoftDeleteMixin:
    is_deleted = Column(Boolean, default=False)

class AuditMixin:
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
```

- [ ] **Step 4: 创建初始迁移（使用 alembic 或直接建表）**

创建 `backend/init_db.py`：

```python
from app.database import engine, Base
from app.models import *

def init():
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

if __name__ == "__main__":
    init()
```

```bash
cd backend
pip install -r requirements.txt
python init_db.py
```

- [ ] **Step 5: 提交**

```bash
git add backend/app/models/ backend/init_db.py
git commit -m "feat: add user model and database init"
```

---

### Task 3: 用户认证 + JWT

**Files:**
- Create: `backend/app/dependencies.py`
- Create: `backend/app/schemas/user.py`
- Create: `backend/app/services/auth.py`
- Create: `backend/app/api/auth.py`

- [ ] **Step 1: 创建 schemas/user.py**

```python
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str
    display_name: str
    role: str = "业务员"

class UserOut(BaseModel):
    id: int
    username: str
    display_name: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class LoginRequest(BaseModel):
    username: str
    password: str
```

- [ ] **Step 2: 创建 services/auth.py**

```python
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(user: User) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user.id), "role": user.role, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def authenticate(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username, User.is_deleted == False).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
```

- [ ] **Step 3: 创建 api/auth.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import LoginRequest, Token, UserOut, UserCreate
from app.services.auth import authenticate, create_token, hash_password, get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login", response_model=Token)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate(db, req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_token(user)
    return Token(access_token=token, user=UserOut.model_validate(user))

@router.post("/register", response_model=Token)
def register(req: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        display_name=req.display_name,
        role=req.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token(user)
    return Token(access_token=token, user=UserOut.model_validate(user))

@router.get("/api/auth/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)
```

- [ ] **Step 4: 创建 dependencies.py**

```python
from fastapi import Depends, HTTPException
from app.services.auth import get_current_user
from app.models.user import User

def require_role(*roles: str):
    def checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="权限不足")
        return current_user
    return checker
```

- [ ] **Step 5: 注册路由到 main.py**

```python
from app.api import auth
app.include_router(auth.router)
```

- [ ] **Step 6: 提交**

```bash
git add backend/app/api/auth.py backend/app/services/auth.py backend/app/schemas/user.py backend/app/dependencies.py
git commit -m "feat: add JWT auth with role-based access"
```

---

### Task 4: 前端登录页面

**Files:**
- Create: `frontend/src/api/index.js`
- Create: `frontend/src/api/auth.js`
- Create: `frontend/src/store/user.js`
- Create: `frontend/src/views/login/Login.vue`

- [ ] **Step 1: 创建 api/index.js**

```javascript
import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 30000 })

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api
```

- [ ] **Step 2: 创建 api/auth.js**

```javascript
import api from './index'

export function login(data) { return api.post('/auth/login', data) }
export function getMe() { return api.get('/auth/me') }
```

- [ ] **Step 3: 创建 store/user.js**

```javascript
import { defineStore } from 'pinia'
import { getMe } from '../api/auth'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: null,
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    role: (state) => state.user?.role || '',
    username: (state) => state.user?.username || '',
  },
  actions: {
    setToken(token) {
      this.token = token
      localStorage.setItem('token', token)
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
    },
    async fetchUser() {
      const res = await getMe()
      this.user = res.data
    },
  },
})
```

- [ ] **Step 4: 创建 Login.vue**

```vue
<template>
  <div style="display:flex;height:100vh;align-items:center;justify-content:center;background:#f0f2f5">
    <el-card style="width:400px">
      <h2 style="text-align:center;margin-bottom:24px;">嘉元瑞通工厂管理系统</h2>
      <el-form ref="formRef" :model="form" :rules="rules" @keyup.enter="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" style="width:100%" :loading="loading" @click="handleLogin">登 录</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../../store/user'
import { login } from '../../api/auth'

const router = useRouter()
const store = useUserStore()
const formRef = ref(null)
const loading = ref(false)
const form = reactive({ username: '', password: '' })
const rules = { username: [{ required: true, message: '请输入用户名' }], password: [{ required: true, message: '请输入密码' }] }

const handleLogin = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    const res = await login(form)
    store.setToken(res.data.access_token)
    store.user = res.data.user
    router.push('/')
  } catch {
    ElMessage.error('用户名或密码错误')
  } finally {
    loading.value = false
  }
}
</script>
```

- [ ] **Step 5: 提交**

```bash
git add frontend/src/api/ frontend/src/store/ frontend/src/views/login/
git commit -m "feat: add login page with JWT auth"
```

---

### Task 5: 客户管理（后端）

**Files:**
- Create: `backend/app/models/customer.py`
- Create: `backend/app/schemas/customer.py`
- Create: `backend/app/services/customer.py`
- Create: `backend/app/api/customers.py`

- [ ] **Step 1: 创建 customer 模型**

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from app.database import Base
from app.models.mixins import TimestampMixin, SoftDeleteMixin, AuditMixin

class Customer(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "customer"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_no = Column(String(50), unique=True, index=True)
    name = Column(String(200), nullable=False)
    contact = Column(String(100))
    phone = Column(String(50))
    address = Column(Text)
```

- [ ] **Step 2: 创建 schemas/customer.py**

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CustomerCreate(BaseModel):
    name: str
    contact: Optional[str] = ""
    phone: Optional[str] = ""
    address: Optional[str] = ""

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    contact: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class CustomerOut(BaseModel):
    id: int
    customer_no: str
    name: str
    contact: Optional[str] = ""
    phone: Optional[str] = ""
    address: Optional[str] = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True
```

- [ ] **Step 3: 创建 services/customer.py**

```python
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate

def generate_customer_no(db: Session) -> str:
    last = db.query(Customer).order_by(Customer.id.desc()).first()
    seq = (last.id + 1) if last else 1
    return f"C{seq:05d}"

def list_customers(db: Session, keyword: str = ""):
    q = db.query(Customer).filter(Customer.is_deleted == False)
    if keyword:
        q = q.filter(Customer.name.like(f"%{keyword}%"))
    return q.order_by(Customer.id.desc()).all()

def get_customer(db: Session, id: int):
    return db.query(Customer).filter(Customer.id == id, Customer.is_deleted == False).first()

def create_customer(db: Session, data: CustomerCreate, username: str):
    customer = Customer(
        customer_no=generate_customer_no(db),
        name=data.name,
        contact=data.contact,
        phone=data.phone,
        address=data.address,
        created_by=username,
        updated_by=username,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer

def update_customer(db: Session, id: int, data: CustomerUpdate, username: str):
    customer = get_customer(db, id)
    if not customer:
        return None
    for field in ["name", "contact", "phone", "address"]:
        val = getattr(data, field)
        if val is not None:
            setattr(customer, field, val)
    customer.updated_by = username
    db.commit()
    db.refresh(customer)
    return customer

def delete_customer(db: Session, id: int):
    customer = get_customer(db, id)
    if not customer:
        return False
    customer.is_deleted = True
    db.commit()
    return True
```

- [ ] **Step 4: 创建 api/customers.py**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerOut
from app.services import customer as service
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/customers", tags=["customers"])

@router.get("", response_model=list[CustomerOut])
def list_all(keyword: str = "", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return service.list_customers(db, keyword)

@router.get("/{id}", response_model=CustomerOut)
def get_one(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return service.get_customer(db, id)

@router.post("", response_model=CustomerOut)
def create(data: CustomerCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return service.create_customer(db, data, current_user.display_name or current_user.username)

@router.put("/{id}", response_model=CustomerOut)
def update(id: int, data: CustomerUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = service.update_customer(db, id, data, current_user.display_name or current_user.username)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="客户不存在")
    return result

@router.delete("/{id}")
def delete(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not service.delete_customer(db, id):
        raise HTTPException(status_code=404, detail="客户不存在")
    return {"message": "已删除"}
```

- [ ] **Step 5: 注册路由到 main.py**

```python
from app.api import customers
app.include_router(customers.router)
```

- [ ] **Step 6: 提交**

```bash
git add backend/app/models/customer.py backend/app/schemas/customer.py backend/app/services/customer.py backend/app/api/customers.py
git commit -m "feat: add customer CRUD API"
```

---

### Task 6: 规格管理（后端）

**Files:**
- Create: `backend/app/models/spec.py`
- Create: `backend/app/schemas/spec.py`
- Create: `backend/app/services/spec.py`
- Create: `backend/app/api/specs.py`

- [ ] **Step 1: 创建 spec 模型**

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum as SAEnum
from app.database import Base
from app.models.mixins import TimestampMixin, SoftDeleteMixin, AuditMixin

class Spec(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "spec"

    id = Column(Integer, primary_key=True, autoincrement=True)
    spec_name = Column(String(100), nullable=False)
    weight = Column(String(50), nullable=False)
    layer_type = Column(SAEnum("单层", "双层", "复合"), nullable=False)
    splice_method = Column(String(100))
    spec_description = Column(Text)
```

- [ ] **Step 2: 创建 schemas/spec.py**

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SpecCreate(BaseModel):
    spec_name: str
    weight: str
    layer_type: str
    splice_method: Optional[str] = ""

class SpecUpdate(BaseModel):
    spec_name: Optional[str] = None
    weight: Optional[str] = None
    layer_type: Optional[str] = None
    splice_method: Optional[str] = None

class SpecOut(BaseModel):
    id: int
    spec_name: str
    weight: str
    layer_type: str
    splice_method: Optional[str] = ""
    spec_description: Optional[str] = ""
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True
```

- [ ] **Step 3: 创建 services/spec.py**

```python
from sqlalchemy.orm import Session
from app.models.spec import Spec
from app.schemas.spec import SpecCreate, SpecUpdate

def build_description(spec: Spec) -> str:
    return f"{spec.spec_name}({spec.weight})+({spec.layer_type})+{spec.splice_method or ''}"

def list_specs(db: Session, keyword: str = ""):
    q = db.query(Spec).filter(Spec.is_deleted == False)
    if keyword:
        q = q.filter(Spec.spec_name.like(f"%{keyword}%"))
    return q.order_by(Spec.id.desc()).all()

def get_spec(db: Session, id: int):
    return db.query(Spec).filter(Spec.id == id, Spec.is_deleted == False).first()

def find_spec_by_name(db: Session, name: str):
    return db.query(Spec).filter(Spec.spec_name == name, Spec.is_deleted == False).first()

def create_spec(db: Session, data: SpecCreate, username: str):
    spec = Spec(
        spec_name=data.spec_name, weight=data.weight,
        layer_type=data.layer_type, splice_method=data.splice_method or "",
        created_by=username, updated_by=username,
    )
    spec.spec_description = build_description(spec)
    db.add(spec); db.commit(); db.refresh(spec)
    return spec

def update_spec(db: Session, id: int, data: SpecUpdate, username: str):
    spec = get_spec(db, id)
    if not spec:
        return None
    for field in ["spec_name", "weight", "layer_type", "splice_method"]:
        val = getattr(data, field)
        if val is not None:
            setattr(spec, field, val)
    spec.spec_description = build_description(spec)
    spec.updated_by = username
    db.commit(); db.refresh(spec)
    return spec

def delete_spec(db: Session, id: int):
    spec = get_spec(db, id)
    if not spec:
        return False
    spec.is_deleted = True
    db.commit()
    return True
```

- [ ] **Step 4: 创建 api/specs.py**（参考 customer 结构，CRUD + 搜索）

- [ ] **Step 5: 注册路由并提交**

---

### Task 7: 合同管理（后端）

**Files:**
- Create: `backend/app/models/contract.py`
- Create: `backend/app/models/contract_item.py`
- Create: `backend/app/schemas/contract.py`
- Create: `backend/app/services/contract.py`
- Create: `backend/app/api/contracts.py`

- [ ] **Step 1: 创建 contract 模型**

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Boolean, Enum as SAEnum, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.mixins import TimestampMixin, SoftDeleteMixin, AuditMixin

class Contract(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "contract"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_no = Column(String(100), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customer.id"), nullable=False)
    contract_date = Column(Date, nullable=False)
    spec_id = Column(Integer, ForeignKey("spec.id"), nullable=False)
    spec_description = Column(Text)
    is_pressed = Column(Boolean, default=False)
    packaging_type = Column(String(50))
    delivery_date = Column(Date)

    binding_material = Column(String(200))
    binding_width = Column(String(50))
    binding_color_no = Column(String(50))

    for i in range(1, 11):
        locals()[f"tech_note_{i}"] = Column(Text)

    for i in range(1, 7):
        locals()[f"accessory_desc_{i}"] = Column(String(200))
        locals()[f"accessory_size_{i}"] = Column(String(100))
        locals()[f"accessory_qty_{i}"] = Column(DECIMAL(10, 2))

    for i in range(1, 6):
        locals()[f"pack_note_{i}"] = Column(Text)

    for i in range(1, 4):
        locals()[f"box_note_{i}"] = Column(Text)

    emboss_model = Column(String(100))
    total_amount = Column(DECIMAL(12, 2))

    status = Column(SAEnum("草稿", "保存", "已下发"), default="草稿")
    is_pushed_down = Column(Boolean, default=False)
    push_down_sheet_id = Column(Integer, nullable=True)
    latest_confirm_version = Column(Integer, default=0)

    customer = relationship("Customer")
    spec = relationship("Spec")
    items = relationship("ContractItem", back_populates="contract", cascade="all, delete-orphan")
```

> 注：`tech_note_1~10` 等重复字段在 SQLAlchemy 中可以用循环生成。生产代码可用 `declared_attr` 或直接手动列出。这里为简化使用 `locals()` 方式。

- [ ] **Step 2: 创建 contract_item 模型**

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DECIMAL, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class ContractItem(Base):
    __tablename__ = "contract_item"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contract.id"), nullable=False)
    line_no = Column(Integer, nullable=False)
    unit_price = Column(DECIMAL(10, 2))
    qty = Column(DECIMAL(10, 2))
    amount = Column(DECIMAL(12, 2))
    pattern_code = Column(String(100))
    color_a = Column(String(100))
    image_a_1 = Column(String(500))
    image_a_2 = Column(String(500))
    image_a_3 = Column(String(500))
    color_b = Column(String(100))
    image_b_1 = Column(String(500))
    image_b_2 = Column(String(500))
    image_b_3 = Column(String(500))
    remark = Column(Text)

    contract = relationship("Contract", back_populates="items")
```

- [ ] **Step 3: 创建 schemas/contract.py 和 schemas/contract_item.py**

```python
# schemas/contract_item.py
from pydantic import BaseModel
from typing import Optional

class ContractItemCreate(BaseModel):
    line_no: int
    unit_price: Optional[float] = None
    qty: Optional[float] = None
    pattern_code: Optional[str] = ""
    color_a: Optional[str] = ""
    image_a_1: Optional[str] = ""
    image_a_2: Optional[str] = ""
    image_a_3: Optional[str] = ""
    color_b: Optional[str] = ""
    image_b_1: Optional[str] = ""
    image_b_2: Optional[str] = ""
    image_b_3: Optional[str] = ""
    remark: Optional[str] = ""

class ContractItemOut(BaseModel):
    id: int
    contract_id: int
    line_no: int
    unit_price: Optional[float] = None
    qty: Optional[float] = None
    amount: Optional[float] = None
    pattern_code: Optional[str] = ""
    color_a: Optional[str] = ""
    image_a_1: Optional[str] = ""
    image_a_2: Optional[str] = ""
    image_a_3: Optional[str] = ""
    color_b: Optional[str] = ""
    image_b_1: Optional[str] = ""
    image_b_2: Optional[str] = ""
    image_b_3: Optional[str] = ""
    remark: Optional[str] = ""

    class Config:
        from_attributes = True

# schemas/contract.py
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class ContractCreate(BaseModel):
    contract_no: str
    customer_id: int
    contract_date: date
    spec_id: int
    spec_description: Optional[str] = ""
    is_pressed: Optional[bool] = False
    packaging_type: Optional[str] = ""
    delivery_date: Optional[date] = None
    binding_material: str = ""
    binding_width: Optional[str] = ""
    binding_color_no: Optional[str] = ""
    emboss_model: Optional[str] = ""
    items: list[ContractItemCreate] = []

    tech_note_1: Optional[str] = ""
    # ... up to 10
    # 简化：使用 dict 或 kwargs 接收
```

> 实际代码中，10个tech_note、6组辅料等字段需要逐一列出，此处省略重复代码。

- [ ] **Step 4: 创建 services/contract.py**（核心业务逻辑）

包括：

```
- create_contract: 创建合同 + 行项目，自动计算 total_amount
- update_contract: 更新合同，草稿状态才允许修改
- delete_contract: 软删除，已下发不可删
- get_contract / list_contracts: 带权限过滤（业务员只看自己的）
- push_down: 下推工艺单（调用 process_sheet service）
- generate_confirm_image: 生成确认图版本
- mark_confirmed: 客户确认，合同状态→保存
```

- [ ] **Step 5: 创建 api/contracts.py**（CRUD 路由）

- [ ] **Step 6: 注册路由并提交**

---

### Task 8: 图片上传 + 自动压缩

**Files:**
- Create: `backend/app/utils/image_compress.py`
- Create: `backend/app/api/upload.py`

- [ ] **Step 1: 创建图片压缩工具**

```python
import os
from PIL import Image
from app.config import settings

def compress_image(file_path: str) -> dict:
    """压缩图片，返回 {original_size, compressed_size, original_name, path}"""
    original_size = os.path.getsize(file_path)
    img = Image.open(file_path)

    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    # 等比例缩放
    if max(img.width, img.height) > settings.COMPRESS_MAX_WIDTH:
        ratio = settings.COMPRESS_MAX_WIDTH / max(img.width, img.height)
        img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)

    # 覆盖保存
    img.save(file_path, 'JPEG', quality=settings.COMPRESS_QUALITY, optimize=True)
    compressed_size = os.path.getsize(file_path)

    return {
        "original_size": original_size,
        "compressed_size": compressed_size,
        "saved_percent": round((1 - compressed_size / original_size) * 100, 1),
    }
```

- [ ] **Step 2: 创建 api/upload.py**

```python
import os
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.config import settings
from app.utils.image_compress import compress_image
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/upload", tags=["upload"])

ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}

@router.post("/images")
async def upload_images(
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
):
    results = []
    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTS:
            raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}")

        # 保留原始文件名，加 UUID 防止冲突
        save_name = f"{uuid.uuid4().hex}{ext}"
        save_path = os.path.join(settings.UPLOAD_DIR, save_name)

        content = await file.read()
        with open(save_path, "wb") as f:
            f.write(content)

        # 强制压缩
        compress_info = compress_image(save_path)

        results.append({
            "original_name": file.filename,
            "url": f"/uploads/{save_name}",
            "path": save_name,
            **compress_info,
        })

    return results
```

- [ ] **Step 3: 注册路由并提交**

```bash
git add backend/app/utils/ backend/app/api/upload.py
git commit -m "feat: add image upload with auto-compression"
```

---

### Task 9: 确认图版本控制（后端）

**Files:**
- Create: `backend/app/models/confirm_image.py`
- Create: `backend/app/schemas/confirm_image.py`
- Create: `backend/app/services/confirm_image.py`

- [ ] **Step 1: 创建 confirm_image 模型**

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from app.database import Base

class ConfirmImage(Base):
    __tablename__ = "confirm_image"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contract.id"), nullable=False)
    version_no = Column(Integer, nullable=False)
    generated_at = Column(DateTime, default=datetime.now)
    generated_by = Column(String(100))
    change_log = Column(Text)
    is_confirmed = Column(Boolean, default=False)
    confirmed_at = Column(DateTime)
    confirmed_by = Column(String(100))
    image_path = Column(String(500))
    contract_snapshot = Column(JSON)
```

- [ ] **Step 2: 实现 services/confirm_image.py**

核心逻辑：
```python
def generate_confirm_image(db, contract_id, username):
    contract = get_contract(db, contract_id)
    # 计算新版本号
    last = db.query(ConfirmImage).filter(
        ConfirmImage.contract_id == contract_id
    ).order_by(ConfirmImage.version_no.desc()).first()
    version_no = (last.version_no + 1) if last else 1

    # 记录修改日志（与上次版本对比）
    change_log = build_change_log(contract, last)

    # 生成确认图（将合同信息+花型渲染为图片）
    image_path = render_confirmation_image(contract, version_no)

    # 保存合同快照
    snapshot = jsonable_encoder(contract_to_dict(contract))

    record = ConfirmImage(
        contract_id=contract_id, version_no=version_no,
        generated_by=username, change_log=change_log,
        image_path=image_path, contract_snapshot=snapshot,
    )
    db.add(record)
    contract.latest_confirm_version = version_no
    db.commit()
    return record

def mark_confirmed(db, contract_id, username):
    """标记客户确认"""
    contract = get_contract(db, contract_id)
    if contract.status != "草稿":
        raise HTTPException(status_code=400, detail="合同已确认，无需重复操作")

    # 将最新版本标记为已确认
    latest = db.query(ConfirmImage).filter(
        ConfirmImage.contract_id == contract_id
    ).order_by(ConfirmImage.version_no.desc()).first()
    if not latest:
        raise HTTPException(status_code=400, detail="请先生成确认图")

    latest.is_confirmed = True
    latest.confirmed_at = datetime.now()
    latest.confirmed_by = username
    contract.status = "保存"
    db.commit()
    return latest
```

- [ ] **Step 3: 将确认路由挂载到 contracts.py**

```python
@router.post("/{id}/confirm-image")
def generate_confirm(id: int, db=Depends(get_db), current_user=Depends(get_current_user)):
    return confirm_service.generate_confirm_image(db, id, current_user.username)

@router.post("/{id}/confirm")
def mark_confirm(id: int, db=Depends(get_db), current_user=Depends(get_current_user)):
    return confirm_service.mark_confirmed(db, id, current_user.username)

@router.get("/{id}/versions")
def version_history(id: int, db=Depends(get_db), current_user=Depends(get_current_user)):
    return confirm_service.get_versions(db, id)
```

- [ ] **Step 4: 提交**

---

### Task 10: 工艺单管理（后端）

**Files:**
- Create: `backend/app/models/process_sheet.py`
- Create: `backend/app/schemas/process_sheet.py`
- Create: `backend/app/services/process_sheet.py`
- Create: `backend/app/api/process_sheets.py`

- [ ] **Step 1: 工艺单模型**

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.mixins import TimestampMixin, SoftDeleteMixin, AuditMixin

class ProcessSheet(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "process_sheet"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contract.id"), nullable=False)
    sheet_no = Column(String(100), nullable=False, index=True)
    confirm_version_no = Column(Integer, nullable=False)
    confirm_image_id = Column(Integer, ForeignKey("confirm_image.id"))
    status = Column(SAEnum("草稿", "保存", "已下发"), default="草稿")

    contract = relationship("Contract")
```

- [ ] **Step 2: 核心业务逻辑 services/process_sheet.py**

```python
def push_down_from_contract(db: Session, contract_id: int, username: str):
    """从合同下推创建工艺单"""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract or contract.is_deleted:
        raise HTTPException(404, "合同不存在")
    if contract.status != "保存":
        raise HTTPException(400, "合同尚未确认，无法下推")
    if contract.is_pushed_down:
        raise HTTPException(400, "合同已下推，不可重复操作")

    sheet_no = generate_sheet_no(db)
    sheet = ProcessSheet(
        contract_id=contract_id,
        sheet_no=sheet_no,
        confirm_version_no=contract.latest_confirm_version,
        status="草稿",
        created_by=username, updated_by=username,
    )
    db.add(sheet)
    contract.is_pushed_down = True
    contract.push_down_sheet_id = sheet.id
    contract.status = "已下发"
    contract.updated_by = username
    db.commit()
    db.refresh(sheet)
    return sheet

def dispatch_sheet(db: Session, sheet_id: int, username: str):
    """下发工艺单 — 校验合同版本是否为最新"""
    sheet = db.query(ProcessSheet).filter(ProcessSheet.id == sheet_id).first()
    if not sheet or sheet.is_deleted:
        raise HTTPException(404, "工艺单不存在")
    if sheet.status != "保存":
        raise HTTPException(400, "工艺单未确认，无法下发")

    contract = sheet.contract
    if sheet.confirm_version_no < contract.latest_confirm_version:
        raise HTTPException(400, "合同已有新版本，请重新生成工艺单")

    sheet.status = "已下发"
    sheet.updated_by = username
    contract.status = "已下发"
    db.commit()
    return sheet
```

- [ ] **Step 3: 创建 API 路由**

```python
router = APIRouter(prefix="/api/process-sheets", tags=["process-sheets"])

@router.get("")              # 列表（生产专员看全部，业务员看关联）
@router.get("/{id}")         # 详情（含合同带入的所有字段）
@router.post("")             # 新建（选择未下推合同）
@router.post("/push-down/{contract_id}")  # 下推
@router.put("/{id}/confirm") # 工艺单确认（草稿→保存）
@router.post("/{id}/dispatch") # 下发
@router.get("/{id}/print")   # 打印
@router.delete("/{id}")      # 软删除
```

- [ ] **Step 4: 提交**

---

### Task 11: 前端 — 合同列表 & 表单页面

**Files:**
- Create: `frontend/src/api/contract.js`
- Create: `frontend/src/api/upload.js`
- Create: `frontend/src/views/contract/ContractList.vue`
- Create: `frontend/src/views/contract/ContractForm.vue`
- Create: `frontend/src/views/contract/ContractDetail.vue`
- Create: `frontend/src/components/ImageUploader.vue`

- [ ] **Step 1: 创建 contract.js API**

```javascript
import api from '../api'

export function listContracts(params) { return api.get('/contracts', { params }) }
export function getContract(id) { return api.get(`/contracts/${id}`) }
export function createContract(data) { return api.post('/contracts', data) }
export function updateContract(id, data) { return api.put(`/contracts/${id}`, data) }
export function deleteContract(id) { return api.delete(`/contracts/${id}`) }
export function generateConfirmImage(id) { return api.post(`/contracts/${id}/confirm-image`) }
export function markConfirmed(id) { return api.post(`/contracts/${id}/confirm`) }
export function getVersions(id) { return api.get(`/contracts/${id}/versions`) }
```

- [ ] **Step 2: 创建 ImageUploader.vue**（上传+预览+压缩率展示）

- [ ] **Step 3: 创建 ContractList.vue**（表格+搜索+权限控制）

- [ ] **Step 4: 创建 ContractForm.vue**（含行项目编辑、规格自动创建提示）

- [ ] **Step 5: 创建 ContractDetail.vue**（展示+操作按钮：生成确认图、标记确认、下推）

- [ ] **Step 6: 添加路由并提交**

---

### Task 12: 前端 — 工艺单页面

**Files:**
- Create: `frontend/src/api/processSheet.js`
- Create: `frontend/src/views/processSheet/SheetList.vue`
- Create: `frontend/src/views/processSheet/SheetForm.vue`
- Create: `frontend/src/views/processSheet/SheetDetail.vue`

- [ ] **Step 1: 创建 processSheet.js API**

```javascript
import api from '../api'

export function listSheets(params) { return api.get('/process-sheets', { params }) }
export function getSheet(id) { return api.get(`/process-sheets/${id}`) }
export function createSheet(data) { return api.post('/process-sheets', data) }
export function pushDownFromContract(contractId) { return api.post(`/process-sheets/push-down/${contractId}`) }
export function confirmSheet(id) { return api.put(`/process-sheets/${id}/confirm`) }
export function dispatchSheet(id) { return api.post(`/process-sheets/${id}/dispatch`) }
export function printSheet(id) { return api.get(`/process-sheets/${id}/print`, { responseType: 'blob' }) }
export function deleteSheet(id) { return api.delete(`/process-sheets/${id}`) }
export function getAvailableContracts() { return api.get('/contracts/available') }
```

- [ ] **Step 2~5: 创建视图组件**（列表、新建/编辑、详情）

- [ ] **Step 6: 提交**

---

### Task 13: 工艺单打印 + 仪表盘

**Files:**
- Create: `backend/app/utils/pdf_generator.py`
- Create: `frontend/src/views/dashboard/Dashboard.vue`

- [ ] **Step 1: 创建 PDF 生成器（占位，等待用户提供格式）**

```python
from weasyprint import HTML

def render_process_sheet(sheet, contract, items) -> bytes:
    """将工艺单渲染为 PDF，格式待用户定稿后完善"""
    html = f"""
    <html>
    <head><meta charset="utf-8">
      <style>
        body {{ font-family: 'SimSun', serif; font-size: 12pt; padding: 20mm; }}
        h1 {{ text-align: center; font-size: 16pt; }}
        table {{ width: 100%; border-collapse: collapse; }}
        td, th {{ border: 1px solid #333; padding: 4px 8px; }}
        .version-note {{ margin-top: 10px; color: #666; font-size: 10pt; }}
      </style>
    </head>
    <body>
      <h1>嘉元瑞通 · 生产工艺单</h1>
      <p>工艺单号：{sheet.sheet_no} | 合同号：{contract.contract_no}</p>
      <p>客户：{contract.customer.name}</p>
      <p>规格：{contract.spec.spec_description}</p>
      <hr/>
      <table>
        <tr><th>行号</th><th>花型</th><th>颜色</th><th>数量</th><th>单价</th><th>金额</th></tr>
        {''.join(f'<tr><td>{i.line_no}</td><td>{i.pattern_code}</td><td>{i.color_a}</td><td>{i.qty}</td><td>{i.unit_price}</td><td>{i.amount}</td></tr>' for i in items)}
      </table>
      <div class="version-note">
        ⓘ 本工艺单基于 {contract.contract_no} 合同的 V{sheet.confirm_version_no} 版本生成
      </div>
    </body>
    </html>
    """
    return HTML(string=html).write_pdf()
```

- [ ] **Step 2: 创建仪表盘页面**

```vue
<template>
  <div>
    <h2>欢迎回来，{{ store.user?.display_name }}</h2>
    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="6">
        <el-card><div class="stat"><div>我的合同</div><div class="num">{{ stats.myContracts }}</div></div></el-card>
      </el-col>
      <el-col :span="6">
        <el-card><div class="stat"><div>待确认合同</div><div class="num">{{ stats.pendingConfirm }}</div></div></el-card>
      </el-col>
      <el-col :span="6">
        <el-card><div class="stat"><div>工艺单</div><div class="num">{{ stats.sheets }}</div></div></el-card>
      </el-col>
      <el-col :span="6">
        <el-card><div class="stat"><div>本月合同数</div><div class="num">{{ stats.monthContracts }}</div></div></el-card>
      </el-col>
    </el-row>
  </div>
</template>
```

- [ ] **Step 3: 提交**

---

### Task 14: 权限集成 — 前端路由守卫 & 菜单

**Files:**
- Modify: `frontend/src/router/index.js`
- Create: `frontend/src/components/SideMenu.vue`

- [ ] **Step 1: 路由守卫增强**

```javascript
// 添加 meta.roles 控制
const routes = [
  {
    path: '/contracts',
    meta: { roles: ['业务员', '销售经理'] },  // 生产专员不可见
    component: () => import('../views/contract/ContractList.vue'),
  },
  {
    path: '/process-sheets',
    meta: { roles: ['业务员', '销售经理', '生产专员'] },
    component: () => import('../views/processSheet/SheetList.vue'),
  },
]
```

- [ ] **Step 2: 菜单组件 — 根据角色动态显示**

- [ ] **Step 3: 提交**

---

### Task 15: 集成测试 & 验收

- [ ] **Step 1: 创建后端测试（pytest）**

```python
# tests/test_contract.py
def test_create_contract_as_salesperson(client, db_session):
    """业务员可以创建合同"""
    ...

def test_salesperson_cannot_see_others_contracts(client, db_session):
    """业务员只能看自己的合同"""
    ...

def test_dispatch_with_stale_version_blocked(client, db_session):
    """工艺单版本落后时禁止下发"""
    ...
```

- [ ] **Step 2: 端到端流程验证**

```
登录业务员 → 新建合同 → 添加行项目 → 上传图片(确认压缩生效)
→ 生成确认图V1 → 修改合同 → 生成确认图V2
→ 标记客户确认 → 合同状态变为保存
→ 下推工艺单 → 填写工艺单 → 确认工艺单 → 下发工艺单
→ 验证合同状态变为已下发
→ 尝试删除已下发合同 → 失败
→ 打印工艺单 PDF
```

- [ ] **Step 3: 最终提交**

```bash
git add -A
git commit -m "feat: complete phase 1 - order management system"
```
