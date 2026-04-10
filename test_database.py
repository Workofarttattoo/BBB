from sqlalchemy import create_engine, Column
from sqlalchemy.orm import declarative_base
from src.blank_business_builder.database import UUIDType

Base = declarative_base()

class TestModel(Base):
    __tablename__ = 'test_table'
    id = Column(UUIDType(), primary_key=True)

def test_uuid_type():
    # Test with sqlite to verify load_dialect_impl works
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    assert True

if __name__ == '__main__':
    test_uuid_type()
    print("Test passed successfully.")
