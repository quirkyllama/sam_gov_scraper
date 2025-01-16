import os
from sqlalchemy import JSON, Boolean, Column, Index, Integer, String, DateTime, Float, ForeignKey, Table
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

# class DepartmentAgency(Base):
#     __tablename__ = 'department_agencies'
    
#     id = Column(String, primary_key=True)
#     name = Column(String)

class SamContractor(Base):
    __tablename__ = 'sam_contractors'
    
    id = Column(Integer, primary_key=True)
    unique_entity_id = Column(String)
    name = Column(String)
    address = Column(String)

    # Relationships
    contracts = relationship("SamContract", back_populates="contractor")

class SamLink(Base):
    __tablename__ = 'sam_links'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    attachment_id = Column(String)
    resource_id = Column(String)
    extension = Column(String)

    # Foreign key to parent contract
    contract_id = Column(Integer, ForeignKey('sam_contracts.id'))
    
    # Relationship back to parent contract
    contract = relationship("SamContract", back_populates="links")

    def get_url(self):
       return f"https://sam.gov/api/prod/opps/v3/opportunities/resources/files/{self.resource_id}/download?&token="

class SamContract(Base):
    __tablename__ = 'sam_contracts'

    id = Column(Integer, primary_key=True)
    solicitation_number = Column(String)
    opportunity_id = Column(String)
    title = Column(String)  
    description = Column(String)
    notice_id = Column(String)
    contract_award_date = Column(DateTime)
    contract_award_number = Column(String)
    contract_amount = Column(Float)
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
    archived = Column(Boolean, default=False)
    cancelled = Column(Boolean, default=False) 
    deleted = Column(Boolean, default=False)
    modified_date = Column(DateTime)

    # There are multiple point of contacts
    # Only recording the primary right now
    point_of_contact_email = Column(String)
    point_of_contact_name = Column(String)
    point_of_contact_phone = Column(String)

    department_agency_id =Column(String)

    # Foreign Keys
    contractor_id = Column(Integer, ForeignKey('sam_contractors.id'))

    # Relationships
    contractor = relationship("SamContractor", back_populates="contracts")

    __table_args__ = (
        Index('idx_sam_contracts_solicitation_number', 'solicitation_number'),
        Index('idx_sam_contracts_opportunity_id', 'opportunity_id'),
        Index('idx_sam_contracts_contract_award_date', 'contract_award_date'),
    )

# Add relationship to SamContract class
SamContract.links = relationship("SamLink", back_populates="contract")

def reset_db():
    """Drops all tables and recreates the schema"""
    engine = _create_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
