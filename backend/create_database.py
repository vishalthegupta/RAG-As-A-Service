"""Create the PostgreSQL database if it doesn't exist"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Database connection parameters
DB_HOST = "localhost"
DB_PORT = "5432"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_NAME = "ragdb"

def create_database():
    """Create the database if it doesn't exist"""
    try:
        # Connect to PostgreSQL server (default postgres database)
        print(f"Connecting to PostgreSQL server at {DB_HOST}:{DB_PORT}...")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database="postgres"  # Connect to default database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (DB_NAME,)
        )
        exists = cursor.fetchone()
        
        if exists:
            print(f"✓ Database '{DB_NAME}' already exists")
        else:
            # Create database
            print(f"Creating database '{DB_NAME}'...")
            cursor.execute(f'CREATE DATABASE {DB_NAME}')
            print(f"✓ Database '{DB_NAME}' created successfully")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        print(f"✗ Could not connect to PostgreSQL server:")
        print(f"  Error: {e}")
        print(f"\nPlease make sure:")
        print(f"  1. PostgreSQL is running")
        print(f"  2. Host: {DB_HOST}, Port: {DB_PORT}")
        print(f"  3. User: {DB_USER}, Password: {DB_PASSWORD}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("PostgreSQL Database Setup")
    print("=" * 60)
    print()
    
    if create_database():
        print()
        print("=" * 60)
        print("✓ Database setup complete!")
        print("=" * 60)
        print()
        print("You can now start the server with:")
        print("  uvicorn app.main:app --reload")
    else:
        print()
        print("=" * 60)
        print("✗ Database setup failed")
        print("=" * 60)
        exit(1)
