from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    DateTime,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


# ==========================
# VOTER DATABASE TABLE
# ==========================

class VoterRecord(Base):
    __tablename__ = "voter_records"

    id = Column(Integer, primary_key=True, index=True)
    voter_id = Column(String, unique=True, nullable=False, index=True)

    full_name = Column(String, nullable=False)
    father_name = Column(String)
    dob = Column(String)
    gender = Column(String)
    address = Column(String)
    polling_station = Column(String)


# ==========================
# POLICE DATABASE TABLE
# ==========================

class PoliceRecord(Base):
    __tablename__ = "police_records"

    id = Column(Integer, primary_key=True, index=True)
    case_reference = Column(String, unique=True, nullable=False, index=True)

    reported_name = Column(String, nullable=False)
    father_name = Column(String)
    dob = Column(String)
    phone = Column(String)
    address = Column(String)
    station = Column(String)


# ==========================
# RATION DATABASE TABLE
# ==========================

class RationRecord(Base):
    __tablename__ = "ration_records"

    id = Column(Integer, primary_key=True, index=True)
    ration_card = Column(String, unique=True, nullable=False, index=True)

    member_name = Column(String, nullable=False)
    head_of_family = Column(String)
    dob = Column(String)
    address = Column(String)
    district = Column(String)


# ==========================
# AI GENERATED IDENTITY CLUSTERS
# ==========================

class IdentityCluster(Base):
    __tablename__ = "identity_clusters"

    id = Column(Integer, primary_key=True, index=True)

    confidence_score = Column(Float)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    members = relationship(
        "ClusterMember",
        back_populates="cluster",
        cascade="all, delete-orphan",
    )


# ==========================
# RECORDS BELONGING TO A CLUSTER
# ==========================

class ClusterMember(Base):
    __tablename__ = "cluster_members"

    id = Column(Integer, primary_key=True, index=True)

    cluster_id = Column(
        Integer,
        ForeignKey("identity_clusters.id"),
        nullable=False
    )

    source_type = Column(String, nullable=False)

    source_record_id = Column(Integer, nullable=False)

    similarity_score = Column(Float)

    cluster = relationship(
        "IdentityCluster",
        back_populates="members"
    )