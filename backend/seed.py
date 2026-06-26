"""创建测试用户"""
from app.database import SessionLocal
from app.models.user import User
from app.services.auth import hash_password

db = SessionLocal()

users = [
    {"username": "admin", "password": "admin123", "display_name": "管理员", "role": "销售经理"},
    {"username": "sales", "password": "sales123", "display_name": "张业务", "role": "业务员"},
    {"username": "producer", "password": "prod123", "display_name": "李生产", "role": "生产专员"},
]

for u in users:
    exists = db.query(User).filter(User.username == u["username"]).first()
    if not exists:
        db.add(User(
            username=u["username"],
            password_hash=hash_password(u["password"]),
            display_name=u["display_name"],
            role=u["role"],
        ))
        print(f"Created user: {u['username']}")
    else:
        print(f"User exists: {u['username']}")

db.commit()
db.close()
print("Seed complete!")
