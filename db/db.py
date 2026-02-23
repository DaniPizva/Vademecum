#configura la conexion con la base de datos

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine #motor de busqueda
from sqlalchemy.orm import sessionmaker , declarative_base


load_dotenv()#este abre/accede la info del.env , carga la url de nuestra bd 

DATABASE_URL = os.getenv("DB_URL")
print(DATABASE_URL)

engine = create_engine(
    DATABASE_URL
)

SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False,
    bind=engine
) #cuando vayamols a insertar un dato, nosotros lo avisamos. #tipo hacer una consulta, nosotros indicamos, no lo hace manual
Base = declarative_base()

print("Connected to DB OK") #ya tenemos conexion con la base de datos, se puede consultar