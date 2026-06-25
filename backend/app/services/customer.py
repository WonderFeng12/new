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
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(customer, field, value)
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
