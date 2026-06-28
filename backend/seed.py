"""创建测试用户和基础数据"""
from app.database import SessionLocal
from app.models.user import User
from app.models.customer import Customer
from app.models.basic_data import BasicData
from app.services.auth import hash_password

db = SessionLocal()

users = [
    {"username": "admin", "password": "admin123", "display_name": "管理员", "role": "销售经理"},
    {"username": "sales", "password": "sales123", "display_name": "张业务", "role": "业务员"},
    {"username": "producer", "password": "prod123", "display_name": "李生产", "role": "生产专员"},
    {"username": "waixie", "password": "waixie123", "display_name": "外协织造厂", "role": "外协人员"},
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

# 客户种子数据
customers = [
    {"name": "北京家纺有限公司", "contact": "王经理", "phone": "13800138001", "address": "北京市大兴区"},
    {"name": "上海纺织集团", "contact": "李经理", "phone": "13900139002", "address": "上海市浦东新区"},
    {"name": "广州天纺贸易", "contact": "张总", "phone": "13700137003", "address": "广州市番禺区"},
]
for c in customers:
    exists = db.query(Customer).filter(Customer.name == c["name"]).first()
    if not exists:
        last = db.query(Customer).order_by(Customer.id.desc()).first()
        seq = (last.id + 1) if last else 1
        db.add(Customer(
            customer_no=f"C{seq:05d}",
            name=c["name"],
            contact=c["contact"],
            phone=c["phone"],
            address=c["address"],
            created_by="系统",
            updated_by="系统",
        ))
        print(f"Created customer: {c['name']}")
    else:
        print(f"Customer exists: {c['name']}")

# 包装方式种子数据
packaging_types = ["纸箱", "抽真空", "压缩包", "打卷面料"]
for i, pt in enumerate(packaging_types, 1):
    exists = db.query(BasicData).filter(
        BasicData.category == "packaging_type", BasicData.code == pt
    ).first()
    if not exists:
        db.add(BasicData(category="packaging_type", code=pt, value=pt, sort_order=i))
        print(f"Created packaging_type: {pt}")

db.commit()
db.close()
print("Seed complete!")
