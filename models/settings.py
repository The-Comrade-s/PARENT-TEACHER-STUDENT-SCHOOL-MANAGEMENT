"""System settings, saved reports, and export history."""

from sqlalchemy import Column, String, ForeignKey, Text

from models.base import BaseModel


class SystemSetting(BaseModel):
    __tablename__ = "system_settings"

    key = Column(String(150), nullable=False, unique=True)
    value = Column(Text, nullable=True)
    description = Column(String(300), nullable=True)


class SavedReport(BaseModel):
    __tablename__ = "saved_reports"

    name = Column(String(255), nullable=False)
    report_type = Column(String(100), nullable=False)   # e.g. attendance, results, behaviour
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    parameters = Column(Text, nullable=True)   # JSON-encoded filter parameters


class ExportHistory(BaseModel):
    __tablename__ = "export_history"

    exported_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    export_type = Column(String(50), nullable=False)   # csv, excel, pdf
    module = Column(String(100), nullable=False)
    file_name = Column(String(255), nullable=True)
