#tablas en python se llaman models
from __future__ import annotations 

from sqlalchemy import Column, Integer, String, Date, ForeignKey, Numeric, CheckConstraint, Boolean
from sqlalchemy.orm import relationship #para crear una relacion # object relation mapper

from db.db import Base

##--------------------------
##SOlO primary key

class Therapeutic_group(Base):
    __tablename__="therapeutic_groups"

    id = Column(Integer,primary_key=True)
    name = Column(String(100), nullable=False)#no puede ser nulo, para que sea nulo =True

    relat_description_therapeutic_group = relationship("Description", back_populates="therapeutic_group_relation_d") 

    def to_dict(self):#definir un diccionario que devuelva el id y nombre
        return{
            "id": self.id,
            "name": self.name,
        }
    
    
class Laboratory(Base):
    __tablename__="laboratories"

    id = Column(Integer,primary_key=True)
    name = Column(String(100), nullable=False)

    relat_product_laboratory = relationship("Product", back_populates="laboratory_relation_p") 

    def to_dict(self):
        return{
            "id": self.id,
            "name": self.name,
        }

class Generic(Base):
    __tablename__="generics"

    id = Column(Integer,primary_key=True)
    name = Column(String(100), nullable=False)

    relat_product_generic = relationship("Product", back_populates="generic_relation_p") 
   
    def to_dict(self):
        return{
            "id": self.id,
            "name": self.name,
        }
    
##--------------------------
## primary key + Foreign keys

class Description(Base):
    __tablename__="descriptions"

    id = Column(Integer,primary_key=True)
    description = Column(String, nullable=False)#no puede ser nulo, para que sea nulo =True

    therapeutic_group_id = Column(Integer, ForeignKey("therapeutic_groups.id", ondelete="RESTRICT",onupdate="CASCADE"),nullable=False)
    therapeutic_group_relation_d = relationship("Therapeutic_group", back_populates="relat_description_therapeutic_group")

    relat_family_description = relationship("Family", back_populates="description_relation_f") 

    def to_dict(self):#definir un diccionario que devuelva el id y nombre
        return{
            "id": self.id,
            "description": self.description,
            "therapeutic_group_id": self.therapeutic_group_id
        }

class Family(Base):
    __tablename__="families" 

    id = Column(Integer,primary_key=True)
    name = Column(String(100), nullable=False)
    
    description_id = Column(Integer, ForeignKey("descriptions.id", ondelete="RESTRICT",onupdate="CASCADE"),nullable=True)
    description_relation_f = relationship("Description", back_populates="relat_family_description")

    mechanism_of_action = Column(String, nullable=True)

    relat_product_family = relationship("Product", back_populates="family_relation_p") 

    def to_dict(self):
        return{
            "id": self.id,
            "name": self.name,
            "description_id": self.description_id,
            "mechanism_of_action": self.mechanism_of_action

        }
    
class Product(Base):
    __tablename__="products" 

    id = Column(Integer,primary_key=True)
    
    family_id = Column(Integer, ForeignKey("families.id", ondelete="RESTRICT",onupdate="CASCADE"),nullable=False)
    family_relation_p = relationship("Family", back_populates="relat_product_family")

    laboratory_id = Column(Integer, ForeignKey("laboratories.id", ondelete="RESTRICT",onupdate="CASCADE"),nullable=True)
    laboratory_relation_p = relationship("Laboratory", back_populates="relat_product_laboratory")

    generic_id = Column(Integer, ForeignKey("generics.id", ondelete="RESTRICT",onupdate="CASCADE"),nullable=True)
    generic_relation_p = relationship("Generic", back_populates="relat_product_generic")

    commercial_name = Column(String(100), nullable=False)
    concentration = Column(String(100), nullable=True)
    dosage_form = Column(String, nullable=True)
    posology = Column(String, nullable=True)
    notes = Column(String, nullable=True)

    is_active = Column(Boolean, nullable=False, default=True) #true producto activo, false inactivo

    def to_dict(self):
        return{
            "id": self.id,
            "family_id": self.family_id,
            "laboratory_id": self.laboratory_id,
            "generic_id": self.generic_id,
            "commercial_name": self.commercial_name,
            "dosage_form": self.dosage_form,
            "concentration": self.concentration,
            "posology": self.posology,
            "notes": self.notes,
            "is_active": self.is_active,

        }
    


