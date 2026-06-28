"""合同业务测试 — 运行需要 MySQL 数据库"""
from datetime import date
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.contract import Contract
from app.models.contract_item import ContractItem
from app.models.customer import Customer
from app.models.spec import Spec


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_create_contract_with_items(db_session):
    """测试创建合同带行项目"""
    customer = Customer(name="测试客户", customer_no="C00001")
    spec = Spec(length="200", width="240", weight="500g", layer_type="单层",
                spec_name="200*240/500g/单层", spec_description="200*240/500g/单层")
    db_session.add_all([customer, spec])
    db_session.commit()

    contract = Contract(
        contract_no="HT2025060001", customer_id=customer.id,
        contract_date=date(2025, 6, 25), spec_id=spec.id,
        status="草稿", created_by="测试", updated_by="测试",
    )
    db_session.add(contract)
    db_session.flush()

    item = ContractItem(
        contract_id=contract.id, line_no=1,
        spec_id=spec.id, unit_price=100, qty=10, amount=1000,
        pattern_code="P001",
    )
    db_session.add(item)
    contract.total_amount = 1000
    db_session.commit()

    assert contract.id is not None
    assert len(contract.items) == 1
    assert contract.total_amount == 1000


def test_contract_soft_delete(db_session):
    """测试合同软删除"""
    customer = Customer(name="客户B", customer_no="C00002")
    spec = Spec(length="150", width="200", weight="300g", layer_type="双层",
                spec_name="150*200/300g/双层", spec_description="150*200/300g/双层")
    db_session.add_all([customer, spec])
    db_session.commit()

    contract = Contract(
        contract_no="HT2025060002", customer_id=customer.id,
        contract_date=date(2025, 6, 25), spec_id=spec.id,
        status="草稿", created_by="测试", updated_by="测试",
    )
    db_session.add(contract)
    db_session.commit()

    contract.is_deleted = True
    db_session.commit()

    found = db_session.query(Contract).filter(
        Contract.id == contract.id, Contract.is_deleted == False
    ).first()
    assert found is None


def test_contract_status_flow(db_session):
    """测试合同状态流转"""
    customer = Customer(name="客户C", customer_no="C00003")
    spec = Spec(length="100", width="150", weight="200g", layer_type="复合",
                spec_name="100*150/200g/复合", spec_description="100*150/200g/复合")
    db_session.add_all([customer, spec])
    db_session.commit()

    contract = Contract(
        contract_no="HT2025060003", customer_id=customer.id,
        contract_date=date(2025, 6, 25), spec_id=spec.id,
        status="草稿",
    )
    db_session.add(contract)
    db_session.commit()

    assert contract.status == "草稿"

    contract.status = "保存"
    db_session.commit()
    assert contract.status == "保存"

    contract.status = "已下发"
    db_session.commit()
    assert contract.status == "已下发"
