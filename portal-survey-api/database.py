import sys
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.exc import OperationalError

from config import settings

# Create engine with connection pool settings
engine = create_engine(
    settings.database_url, 
    echo=settings.DEBUG,
    pool_pre_ping=True,  # Verify connections before using them
    pool_recycle=3600,   # Recycle connections after 1 hour
    connect_args={
        "connect_timeout": 10
    }
)


def create_db_and_tables() -> None:
    """Create database tables if they don't exist."""
    try:
        print("Attempting to connect to database...")
        print(f"  Host: {settings.DB_HOST}:{settings.DB_PORT}")
        print(f"  Database: {settings.DB_NAME}")
        
        # Test connection
        with engine.connect() as conn:
            print("✓ Database connection successful")
        
        # Create tables
        SQLModel.metadata.create_all(engine)
        print("✓ Database tables created/verified")
        
    except OperationalError as e:
        print(f"✗ Database connection failed: {e}", file=sys.stderr)
        print(f"  Connection string: mysql+pymysql://{settings.DB_USER}:****@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}", file=sys.stderr)
        raise
    except Exception as e:
        print(f"✗ Database initialization failed: {e}", file=sys.stderr)
        raise


def get_session():
    with Session(engine) as session:
        yield session
