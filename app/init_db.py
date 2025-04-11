from app.db import engine, Base
from app.models.user import User  # Ensure this import triggers model registration

Base.metadata.create_all(bind=engine)

print("✅ Database tables created.")