from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class CpuSpecification(Base):
    __tablename__ = "cpu_specifications"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    socket = Column(String(50), nullable=False)
    core_count = Column(Integer, nullable=False)
    thread_count = Column(Integer, nullable=False)
    base_clock_ghz = Column(Numeric(4, 2), nullable=False)
    boost_clock_ghz = Column(Numeric(4, 2), nullable=False)
    tdp_watts = Column(Integer, nullable=False)
    architecture = Column(String(100), nullable=True)
    integrated_graphics = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("Product", back_populates="cpu_spec")


class GpuSpecification(Base):
    __tablename__ = "gpu_specifications"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    chipset = Column(String(100), nullable=False)
    vram_gb = Column(Integer, nullable=False)
    memory_type = Column(String(50), nullable=False)
    core_clock_mhz = Column(Integer, nullable=True)
    boost_clock_mhz = Column(Integer, nullable=False)
    length_mm = Column(Integer, nullable=False)
    tdp_watts = Column(Integer, nullable=False)
    recommended_psu_watts = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("Product", back_populates="gpu_spec")


class MotherboardSpecification(Base):
    __tablename__ = "motherboard_specifications"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    socket = Column(String(50), nullable=False)
    chipset = Column(String(50), nullable=False)
    form_factor = Column(String(50), nullable=False)
    memory_type = Column(String(50), nullable=False)
    memory_slots = Column(Integer, nullable=False)
    max_memory_gb = Column(Integer, nullable=False)
    pcie_version = Column(String(50), nullable=True)
    wifi = Column(Boolean, default=False, nullable=False)
    max_memory_speed_mhz = Column(Integer, nullable=True)
    supported_storage_interfaces = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("Product", back_populates="motherboard_spec")


class MemorySpecification(Base):
    __tablename__ = "memory_specifications"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    memory_type = Column(String(50), nullable=False)
    capacity_gb = Column(Integer, nullable=False)
    speed_mhz = Column(Integer, nullable=False)
    module_count = Column(Integer, nullable=False)
    cas_latency = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("Product", back_populates="memory_spec")


class StorageSpecification(Base):
    __tablename__ = "storage_specifications"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    storage_type = Column(String(50), nullable=False)
    capacity_gb = Column(Integer, nullable=False)
    interface = Column(String(50), nullable=False)
    form_factor = Column(String(50), nullable=False)
    read_speed_mbps = Column(Integer, nullable=True)
    write_speed_mbps = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("Product", back_populates="storage_spec")


class PsuSpecification(Base):
    __tablename__ = "psu_specifications"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    wattage = Column(Integer, nullable=False)
    efficiency_rating = Column(String(50), nullable=False)
    modularity = Column(String(50), nullable=False)
    form_factor = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("Product", back_populates="psu_spec")


class CaseSpecification(Base):
    __tablename__ = "case_specifications"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    case_type = Column(String(50), nullable=False)
    supported_motherboard_form_factors = Column(JSON, nullable=False)
    max_gpu_length_mm = Column(Integer, nullable=False)
    max_cpu_cooler_height_mm = Column(Integer, nullable=False)
    psu_form_factor = Column(String(50), nullable=False)
    drive_bays = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("Product", back_populates="case_spec")


class CoolingSpecification(Base):
    __tablename__ = "cooling_specifications"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    cooler_type = Column(String(50), nullable=False)
    supported_sockets = Column(JSON, nullable=False)
    radiator_size_mm = Column(Integer, nullable=True)
    fan_size_mm = Column(Integer, nullable=True)
    max_tdp_watts = Column(Integer, nullable=True)
    height_mm = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("Product", back_populates="cooling_spec")
