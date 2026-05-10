# route: db_init.py
from sqlalchemy import text

from db.db import engine
from db.models import Base


def init_db():

    with engine.connect() as connection:

        
        '''connection.execute(
            text("DROP SCHEMA public CASCADE;")
        )
        connection.execute(
            text("CREATE SCHEMA public;")
        )
        connection.commit()

        print("Schema public recreado")
'''
    
    
    Base.metadata.create_all(bind=engine)

    print("Tablas creadas OK")


if __name__ == "__main__":
    init_db()