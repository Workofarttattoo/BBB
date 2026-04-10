from sqlalchemy import create_engine, Column
from sqlalchemy.orm import declarative_base
from src.blank_business_builder.database import UUIDType

Base = declarative_base()

class TestModel(Base):
    __tablename__ = 'test_table_pg'
    id = Column(UUIDType(), primary_key=True)

def test_postgres_uuid():
    # Use postgresql dialect to trigger the non-sqlite code path
    engine = create_engine('postgresql://user:pass@localhost/db')
    try:
        Base.metadata.create_all(engine)
    except Exception as e:
        print(f"Exception: {e}")
        # The exception shouldn't be NameError for UUID
    # We can directly instantiate it and process dialect
    impl = UUIDType().load_dialect_impl(engine.dialect)
    print("Dialect impl:", impl)

if __name__ == '__main__':
    test_postgres_uuid()
