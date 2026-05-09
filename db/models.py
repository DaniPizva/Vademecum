# db\models.py

#tablas en python se llaman models
from __future__ import annotations 

from sqlalchemy import Column, Integer, String, Date, ForeignKey, Numeric, CheckConstraint, Boolean, JSON, Text, DateTime
from sqlalchemy.orm import relationship #para crear una relacion # object relation mapper
import datetime
from datetime import timezone, datetime
from db.db import Base
class Therapeutic_group(Base):
    __tablename__="therapeutic_groups"

    id = Column(Integer,primary_key=True)
    name = Column(String(100), nullable=False) #no puede ser nulo, para que sea nulo =True

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

    # Información relativa al usuario
    identification = Column(String(15), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    full_name = Column(String(200), nullable=False)
    password_hash = Column(String(255), nullable=False)

    # Estado
    is_active = Column(Boolean, nullable=False, default=True)

    # Fechas
    first_login_at = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True))

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    last_login_at = Column(DateTime(timezone=True))
    deleted_at = Column(DateTime(timezone=True))

    # Relaciones

    roles = relationship(
        "UserRole",
        foreign_keys="UserRole.user_id",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    terms_acceptances = relationship(
        "UserTermsAcceptance",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    password_history = relationship(
        "PasswordHistory",
        back_populates="user"
    )

    security_events = relationship(
        "SecurityEvent",
        back_populates="user"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "identification": self.identification,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,

            "created_at":
                self.created_at.isoformat()
                if self.created_at else None,

            "updated_at":
                self.updated_at.isoformat()
                if self.updated_at else None,

            "first_login_at":
                self.first_login_at.isoformat()
                if self.first_login_at else None,

            "password_changed_at":
                self.password_changed_at.isoformat()
                if self.password_changed_at else None,

            "last_login_at":
                self.last_login_at.isoformat()
                if self.last_login_at else None,

            "deleted_at":
                self.deleted_at.isoformat()
                if self.deleted_at else None
        }


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)

    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    users = relationship(
        "UserRole",
        back_populates="role"
    )


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        primary_key=True
    )

    role_id = Column(
        Integer,
        ForeignKey("roles.id"),
        primary_key=True
    )

    assigned_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    assigned_by = Column(
        Integer,
        ForeignKey("users.id")
    )

    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="roles"
    )

    role = relationship(
        "Role",
        foreign_keys=[role_id],
        back_populates="users"
    )

class TermsVersion(Base):
    __tablename__ = "terms_versions"

    id = Column(Integer, primary_key=True)
    
    #Información y atributos generales
    version = Column(String(50), nullable=False, unique=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String(128), nullable=False)
    
    #Variable de estado
    is_active = Column(Boolean, nullable=False, default=False)
    
    #Fechas y TimeStamps
    effective_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"))

    acceptances = relationship(
        "UserTermsAcceptance",
        back_populates="terms_version"
    )

class UserTermsAcceptance(Base):
    __tablename__ = "user_terms_acceptances"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    terms_version_id = Column(
        Integer,
        ForeignKey("terms_versions.id"),
        nullable=False
    )

    accepted_at = Column(DateTime(timezone=True), nullable=False)

    ip_address = Column(String(45))

    user_agent = Column(Text)

    acceptance_method = Column(String(50))

    user = relationship(
        "User",
        back_populates="terms_acceptances"
    )

    terms_version = relationship(
        "TermsVersion",
        back_populates="acceptances"
    )
    
class PasswordHistory(Base):
    __tablename__ = "password_history"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"))

    password_hash = Column(String(255), nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship(
        "User",
        back_populates="password_history"
    )
    
class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"))

    event_type = Column(String(100), nullable=False)

    ip_address = Column(String(45))

    user_agent = Column(Text)

    event_metadata = Column(JSON)

    created_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship(
        "User",
        back_populates="security_events"
    )