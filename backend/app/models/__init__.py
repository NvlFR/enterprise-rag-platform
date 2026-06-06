from app.db.base_class import Base

from .document import Document
from .user import User

__all__ = ["Base", "User", "Document"]
