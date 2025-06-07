from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Numeric
from app import db

class User(db.Model):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(128), nullable=False)
    used_storage = Column(Numeric(10, 2), default=0)
    storage_limit = Column(Numeric(10, 2), default=1024.00)
    is_locked = Column(Boolean, default=False)
    def __repr__(self):
        return f"<User {self.username}>"


class File(db.Model):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    username = Column(String(50), nullable=False)
    size_mb = Column(Float, nullable=False)
    upload_date = Column(DateTime, nullable=False)
    is_deleted = Column(Boolean, default=False)

    def __repr__(self):
        return f"<File {self.filename} - User: {self.username}>"

class SharedFile(db.Model):
    __tablename__ = 'shared_files'

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, db.ForeignKey('files.id'), nullable=False)
    owner_id = Column(Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = Column(Integer, db.ForeignKey('users.id'), nullable=False)

    file = db.relationship('File', backref='shared_entries')
    owner = db.relationship('User', foreign_keys=[owner_id])
    recipient = db.relationship('User', foreign_keys=[recipient_id])

    def __repr__(self):
        return f"<SharedFile file_id={self.file_id} from user_id={self.owner_id} to user_id={self.recipient_id}>"
