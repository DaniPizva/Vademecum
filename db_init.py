##inicializa la base de datos

from db.db import engine
from db.models import Base

def init_db(): #llama a base
    Base.metadata.drop_all(bind=engine)
    print("tablas borradas")
    Base.metadata.create_all(bind=engine)
    print("tablas creadas")
    #que coja todo lo asociado a base, y lo ponga en el motor
    print("Tablas creadas OK")

if __name__ == "__main__":
    init_db()