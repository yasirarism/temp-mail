from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Email(Base):
    __tablename__ = "emails"
    id = Column(Integer, primary_key=True, index=True)
    email_to = Column(String, index=True)
    subject = Column(String)
    sender = Column(String)
    body_text = Column(Text)
    body_html = Column(Text)
    date = Column(DateTime, default=datetime.utcnow)

    attachments = relationship("Attachment", back_populates="email", cascade="all, delete-orphan")

class Attachment(Base):
    __tablename__ = "attachments"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    filepath = Column(String)
    email_id = Column(Integer, ForeignKey("emails.id"))
    email = relationship("Email", back_populates="attachments")
