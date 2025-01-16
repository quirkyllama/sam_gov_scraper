import os
from sqlalchemy import JSON, Column, String, DateTime, Float, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
Session = None

def _create_engine():
    # Initializes the database 
    return create_engine(os.environ.get("DATABASE_URL"))

def get_session():
    global Session
    if Session is None:
        Session = sessionmaker(bind=_create_engine())
    return Session()

class DepartmentAgency(Base):
    __tablename__ = 'department_agencies'
    
    id = Column(String, primary_key=True)
    name = Column(String)

class Contractor(Base):
    __tablename__ = 'contractors'
    
    id = Column(String, primary_key=True)
    unique_entity_id = Column(String)
    name = Column(String)
    address = Column(String)

class SamContract(Base):
    __tablename__ = 'sam_contracts'

    _id = Column(String, primary_key=True)
    notice_id = Column(String)
    contract_award_date = Column(DateTime)
    contract_award_number = Column(String)
    task_delivery_order_number = Column(String)
    base_and_all_options_value = Column(Float)
    contract_opportunity_type = Column(String)
    original_published_date = Column(DateTime)
    inactive_policy = Column(String)
    original_inactive_date = Column(DateTime)
    initiative = Column(ARRAY(String))
    original_set_aside = Column(String)
    product_service_code = Column(String)
    naics_code = Column(String)
    place_of_performance = Column(String)
    raw_xhr_data = Column(JSON)
    links = Column(ARRAY(String))

    # Foreign Keys
    department_agency_id = Column(String, ForeignKey('department_agencies.id'))
    contractor_id = Column(String, ForeignKey('contractors.id'))

    # Relationships
    department_agency = relationship("DepartmentAgency")
    contractor = relationship("Contractor")

def reset_db():
    """Drops all tables and recreates the schema"""
    engine = _create_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
