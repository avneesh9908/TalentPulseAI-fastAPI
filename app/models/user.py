# Add inside your User class in app/models/user.py
from sqlalchemy.orm import relationship

profile     = relationship("Profile",           back_populates="user", uselist=False)
education   = relationship("Education",         back_populates="user")
skills      = relationship("Skill",             back_populates="user")
documents   = relationship("Document",          back_populates="user")
preferences = relationship("CareerPreferences", back_populates="user", uselist=False)