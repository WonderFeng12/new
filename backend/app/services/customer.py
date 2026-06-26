from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.models.contract import Contract
from app.schemas.customer import CustomerCreate, CustomerUpdate
from fastapi import HTTPException


def generate_customer_no(db: Session) -> str:
    last = db.query(Customer).order_by(Customer.id.desc()).first()
    seq = (last.id + 1) if last else 1
    return f"C{seq:05d}"


def list_customers(db: Session, keyword: str = ""):
    q = db.query(Customer).filter(Customer.is_deleted == False)
    if keyword:
        q = q.filter(Customer.name.like(f"%{keyword}%"))
    customers = q.order_by(Customer.id.desc()).all()

    customer_ids = [c.id for c in customers]
    if customer_ids:
        used_ids = {
            row[0] for row in db.query(Contract.customer_id).filter(
                Contract.customer_id.in_(customer_ids),
                Contract.is_deleted == False,
            ).distinct().all()
        }
    else:
        used_ids = set()

    for c in customers:
        c.is_in_use = c.id in used_ids
    return customers


def get_customer(db: Session, id: int):
    customer = db.query(Customer).filter(Customer.id == id, Customer.is_deleted == False).first()
    if customer:
        customer.is_in_use = db.query(Contract).filter(
            Contract.customer_id == id,
            Contract.is_deleted == False,
        ).first() is not None
    return customer


def create_customer(db: Session, data: CustomerCreate, username: str):
    customer = Customer(
        customer_no=generate_customer_no(db),
        name=data.name,
        contact=data.contact or "",
        phone=data.phone or "",
        address=data.address or "",
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
    if getattr(customer, 'is_in_use', False) or db.query(Contract).filter(
        Contract.customer_id == id, Contract.is_deleted == False,
    ).first():
        raise HTTPException(status_code=400, detail="该客户已被合同引用，不可修改")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(customer, field, value)
    customer.updated_by = username
    db.commit()
    db.refresh(customer)
    return customer


def delete_customer(db: Session, id: int):
    customer = db.query(Customer).filter(Customer.id == id, Customer.is_deleted == False).first()
    if not customer:
        return False
    in_use = db.query(Contract).filter(
        Contract.customer_id == id, Contract.is_deleted == False,
    ).first() is not None
    if in_use:
        raise HTTPException(status_code=400, detail="该客户已被合同引用，不可删除")
    customer.is_deleted = True
    db.commit()
    return True
