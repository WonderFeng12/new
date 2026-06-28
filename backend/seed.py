"""创建测试用户和基础数据"""
import json
from app.database import SessionLocal
from app.models.user import User
from app.models.customer import Customer
from app.models.basic_data import BasicData
from app.models.process_step import ProcessStep
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
        BasicData.category == "packing", BasicData.code == pt
    ).first()
    if not exists:
        db.add(BasicData(category="packing", code=pt, value=pt, sort_order=i))
        print(f"Created packaging_type: {pt}")

# 层类型种子数据
layer_types = ["单层", "双层", "复合直角", "复合圆角", "枕头", "床单"]
for i, lt in enumerate(layer_types, 1):
    exists = db.query(BasicData).filter(
        BasicData.category == "layer_type", BasicData.code == lt
    ).first()
    if not exists:
        db.add(BasicData(category="layer_type", code=lt, value=lt, sort_order=i))
        print(f"Created layer_type: {lt}")

# 合同编码规则种子数据（与客户关联）
code_rules = [
    {"code": "R26", "suffix": "", "customer_name": "北京家纺有限公司"},
    {"code": "R", "suffix": "", "customer_name": "上海纺织集团"},
]
for i, cr in enumerate(code_rules, 1):
    exists = db.query(BasicData).filter(
        BasicData.category == "code_rules", BasicData.code == cr["code"]
    ).first()
    if not exists:
        customer = db.query(Customer).filter(Customer.name == cr["customer_name"]).first()
        val = json.dumps({"suffix": cr["suffix"], "customer_id": customer.id}) if customer else json.dumps({"suffix": cr["suffix"]})
        db.add(BasicData(category="code_rules", code=cr["code"], value=val, sort_order=i))
        print(f"Created code_rule: {cr['code']} -> {cr['customer_name']}")

# 流程步骤种子数据
process_steps = [
    {"step_code": "yarn_plan_released", "step_name": "坯布计划已下达", "sort_order": 1},
    {"step_code": "weaving", "step_name": "织造中", "sort_order": 2},
    {"step_code": "weaving_done", "step_name": "织造完成", "sort_order": 3},
    {"step_code": "setting", "step_name": "定型中", "sort_order": 4},
    {"step_code": "setting_done", "step_name": "定型完成", "sort_order": 5},
    {"step_code": "brushing", "step_name": "刷毛烫光中", "sort_order": 6},
    {"step_code": "brushing_done", "step_name": "刷毛烫光完成", "sort_order": 7},
    {"step_code": "printing", "step_name": "印花中", "sort_order": 8},
    {"step_code": "printing_done", "step_name": "印花完成", "sort_order": 9},
    {"step_code": "sewing", "step_name": "成品缝制", "sort_order": 10},
    {"step_code": "completed", "step_name": "成品完成", "sort_order": 11},
]

for step in process_steps:
    exists = db.query(ProcessStep).filter(ProcessStep.step_code == step["step_code"]).first()
    if not exists:
        db.add(ProcessStep(**step))
        print(f"Created process step: {step['step_name']}")
    else:
        print(f"Process step exists: {step['step_name']}")

db.commit()
db.close()
print("Seed complete!")
