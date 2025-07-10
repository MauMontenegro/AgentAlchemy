from sqlalchemy import Column,String,Integer,ForeignKey,Table,DateTime,Text,text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer,primary_key=True,index=True)
    username = Column(String,unique=True,nullable=False)
    email = Column(String,unique=True,nullable=False)
    hashed_password = Column(String,nullable=False)
    role = Column(String,nullable=True)
    
    # Define the relationship referenced in UserContext
    contexts = relationship("Context", back_populates="user",cascade="all, delete-orphan")

class Context(Base):
    __tablename__ = "contexts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="contexts")
    documents = relationship("Document", back_populates="context",cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    context_id = Column(Integer, ForeignKey("contexts.id",ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=True)       # optional: 'pdf', 'word', etc.
    category = Column(String, nullable=True)   # optional: 'procedure', 'finance', etc.
    s3_url = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))

    context = relationship("Context", back_populates="documents")
        