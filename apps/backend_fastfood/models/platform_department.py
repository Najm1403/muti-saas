from sqlalchemy import Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class PlatformDepartment(Base):
    __tablename__ = "platform_departments"

    name: Mapped[str] = mapped_column(String(80), primary_key=True)
    __table_args__ = (Index("uq_platform_department_name_lower", func.lower(name), unique=True),)
