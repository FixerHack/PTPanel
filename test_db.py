import psycopg2
from sqlalchemy import create_engine, text

def test_connection():
    print("🧪 Testing database connection...")
    
    # Тест 1: Пряме підключення psycopg2
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="ptpanel", 
            user="ptpanel_user",
            password="ptpanel_password_2024",
            port=5432
        )
        print("✅ psycopg2 connection successful")
        conn.close()
    except Exception as e:
        print(f"❌ psycopg2 failed: {e}")
    
    # Тест 2: SQLAlchemy підключення
    try:
        engine = create_engine('postgresql://ptpanel_user:ptpanel_password_2024@localhost:5432/ptpanel')
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            print(f"✅ SQLAlchemy connection successful: {result.fetchone()[0]}")
    except Exception as e:
        print(f"❌ SQLAlchemy failed: {e}")

if __name__ == '__main__':
    test_connection()