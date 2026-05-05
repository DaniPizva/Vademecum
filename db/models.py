# db\models.py
#tablas en python se llaman models
from __future__ import annotations 

from sqlalchemy import Column, Integer, String, Date, ForeignKey, Numeric, CheckConstraint, Boolean, Text
from sqlalchemy.orm import relationship #para crear una relacion # object relation mapper

from db.db import Base

##--------------------------
##SOlO primary key

class Therapeutic_group(Base):
    __tablename__="therapeutic_groups"

    id = Column(Integer,primary_key=True)
    name = Column(String(100), nullable=False)#no puede ser nulo, para que sea nulo =True

    relat_description_therapeutic_group = relationship("Description", back_populates="therapeutic_group_relation_d",passive_deletes=True
) 

    def to_dict(self):#definir un diccionario que devuelva el id y nombre
        return{
            "id": self.id,
            "name": self.name,
        }
    
# Passive deletes ----> se usa para cuando una tabla tiene un relación con otra, y la que lleva el foreign key de la otra se ponga en null si se borra el registro de la tabla principal
class Laboratory(Base):
    __tablename__="laboratories"

    id = Column(Integer,primary_key=True)
    name = Column(String(100), nullable=False)

    relat_product_laboratory = relationship("Product", back_populates="laboratory_relation_p",passive_deletes=True
) 

    def to_dict(self):
        return{
            "id": self.id,
            "name": self.name,
        }

class Generic(Base):
    __tablename__="generics"

    id = Column(Integer,primary_key=True)
    name = Column(String(100), nullable=False)

    relat_product_generic = relationship("Product", back_populates="generic_relation_p",passive_deletes=True) 
   
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

    therapeutic_group_id = Column(Integer, ForeignKey("therapeutic_groups.id", ondelete="RESTRICT"),nullable=False)
    therapeutic_group_relation_d = relationship("Therapeutic_group", back_populates="relat_description_therapeutic_group")

    relat_family_description = relationship("Family", back_populates="description_relation_f",passive_deletes=True) 

    def to_dict(self, include_therapeutic_group: bool = False):#definir un diccionario que devuelva el id y nombre
        data = {
            "id": self.id,
            "description": self.description,
            "therapeutic_group_id": self.therapeutic_group_id
        }

        if include_therapeutic_group and self.therapeutic_group_relation_d:
            data["therapeutic_group"] = self.therapeutic_group_relation_d.to_dict()

        return data

class Family(Base):
    __tablename__="families" 

    id = Column(Integer,primary_key=True)
    name = Column(String(100), nullable=False)
    
    description_id = Column(Integer, ForeignKey("descriptions.id", ondelete="RESTRICT"),nullable=True)
    description_relation_f = relationship("Description", back_populates="relat_family_description")

    mechanism_of_action = Column(String, nullable=True)

    relat_product_family = relationship("Product", back_populates="family_relation_p",passive_deletes=True
 ) 

    def to_dict(self, include_description: bool = False,
        include_therapeutic_group: bool = False):
        data = {
            "id": self.id,
            "name": self.name,
            "description_id": self.description_id,
            "mechanism_of_action": self.mechanism_of_action
        }

        if include_description and self.description_relation_f:
            data["description"] = self.description_relation_f.to_dict(
                include_therapeutic_group=include_therapeutic_group
            )

        return data
    
class Product(Base):
    __tablename__="products" 

    id = Column(Integer,primary_key=True)
    
    family_id = Column(Integer, ForeignKey("families.id", ondelete="RESTRICT"),nullable=False)
    family_relation_p = relationship("Family", back_populates="relat_product_family")

    laboratory_id = Column(Integer, ForeignKey("laboratories.id", ondelete="RESTRICT"),nullable=True)
    laboratory_relation_p = relationship("Laboratory", back_populates="relat_product_laboratory")

    generic_id = Column(Integer, ForeignKey("generics.id", ondelete="RESTRICT"),nullable=True)
    generic_relation_p = relationship("Generic", back_populates="relat_product_generic")

    commercial_name = Column(String(100), nullable=False)
    concentration = Column(String(100), nullable=True)
    dosage_form = Column(String, nullable=True)
    posology = Column(String, nullable=True)
    notes = Column(String, nullable=True)

    is_active = Column(Boolean, nullable=False, default=True) #true producto activo, false inactivo

    def to_dict(
        self,
        include_family: bool = False,
        include_laboratory: bool = False,
        include_generic: bool = False,
        include_description: bool = False,
        include_therapeutic_group: bool = False
    ):
        data = {
            "id": self.id,
            "family_id": self.family_id,
            "laboratory_id": self.laboratory_id,
            "generic_id": self.generic_id,
            "commercial_name": self.commercial_name,
            "concentration": self.concentration,
            "dosage_form": self.dosage_form,
            "posology": self.posology,
            "notes": self.notes,
            "is_active": self.is_active,
            "image": getattr(self,"image", None)
        }

        if include_family and self.family_relation_p:
            data["family"] = self.family_relation_p.to_dict(
                include_description=include_description,
                include_therapeutic_group=include_therapeutic_group
            )

        if include_laboratory and self.laboratory_relation_p:
            data["laboratory"] = self.laboratory_relation_p.to_dict()

        if include_generic and self.generic_relation_p:
            data["generic"] = self.generic_relation_p.to_dict()

        return data

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    identification = Column(String(15), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    full_name = Column(String(200), nullable=False)
    password_hash = Column(String(200), nullable=False)
    is_active = Column(Integer, nullable=False, default=1)
    terms_accepted = Column(Boolean, nullable=False, default=False)
    must_change_password = Column(Boolean, nullable=False, default=True)
    first_login_at = Column(Date, nullable=True)
    password_changed_at = Column(Date, nullable=True)

    # restricción para garantizar el patron del correo : -> "@ces.edu.co ; @uces.edu.co"
    __table_args__ = (
        CheckConstraint(
            "email ~* '^[A-Za-z0-9._%+-]+@(uces\\.edu\\.co|ces\\.edu\\.co)$'",
            name="email_domain_check"
        ),
    )

    # relationships
    relat_user_id = relationship("Users_roles", back_populates="user_id_relationship")

    def to_dict(self):
        return {
            "id": self.id,
            "identification": self.identification,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "terms_accepted": self.terms_accepted,
            "must_change_password": self.must_change_password,
            "first_login_at": self.first_login_at.isoformat() if self.first_login_at else None,
            "password_changed_at": self.password_changed_at.isoformat() if self.password_changed_at else None,
        }
        
       
class Roles(Base):
    __tablename__ = "roles"

    id  = Column(Integer, primary_key=True)
    nombre= Column(Text, nullable=False)
    description = Column(Text, nullable=False, unique=True)

    #Relaciones
    relat_role_id = relationship('Users_roles', back_populates="role_id_relationship")
    
    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "description": self.description
        }
        

class Users_roles(Base):
    #Nombre de tabla
    __tablename__ = "users_roles"
    #Atributos
    user_id = Column(Integer, ForeignKey('users.id', ondelete="RESTRICT", onupdate="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey('roles.id', ondelete= "RESTRICT", onupdate = "CASCADE"), primary_key=True)

    #Relaciones
    user_id_relationship = relationship("User", back_populates="relat_user_id")
    role_id_relationship = relationship("Roles", back_populates="relat_role_id")
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "role_id": self.role_id
        }