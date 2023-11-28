from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


generic_interaction = Table(
    "generic_interaction",
    Base.metadata,
    Column("generic_id", Integer, ForeignKey("generic.id")),
    Column("interaction_id", Integer, ForeignKey("interaction.id")),
)


class Generic(Base):
    __tablename__ = "generic"
    id = Column(Integer, primary_key=True)
    rxcui = Column(Integer, unique=True, index=True)
    name = Column(String(50), index=True)
    interactions = relationship(
        "Interaction", secondary=generic_interaction, back_populates="generics"
    )

    def __repr__(self):
        return f"Generic(rxcui={self.rxcui}, name={self.name})"


class Interaction(Base):
    __tablename__ = "interaction"
    id = Column(Integer, primary_key=True)
    description = Column(String)
    severity = Column(String(20))
    source_name = Column(String(10))
    source_urls = Column(String)

    generics = relationship(
        "Generic", secondary=generic_interaction, back_populates="interactions"
    )

    def __repr__(self):
        return f"Interaction(description={self.description}, severity={self.severity}, source_name={self.source_name})"
