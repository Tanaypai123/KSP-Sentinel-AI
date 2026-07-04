from typing import List, Optional
from datetime import date
from sqlalchemy import String, Integer, Boolean, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class State(Base):
    __tablename__ = "state"

    state_id: Mapped[int] = mapped_column("StateID", Integer, primary_key=True)
    state_name: Mapped[str] = mapped_column("StateName", String(100), nullable=False)
    nationality_id: Mapped[Optional[int]] = mapped_column("NationalityID", Integer, nullable=True)
    active: Mapped[bool] = mapped_column("Active", Boolean, default=True, server_default="true")

    # Relationships
    districts: Mapped[List["District"]] = relationship(back_populates="state")
    units: Mapped[List["Unit"]] = relationship(back_populates="state")
    courts: Mapped[List["Court"]] = relationship(back_populates="state")


class District(Base):
    __tablename__ = "district"

    district_id: Mapped[int] = mapped_column("DistrictID", Integer, primary_key=True)
    district_name: Mapped[str] = mapped_column("DistrictName", String(100), nullable=False, index=True)
    state_id: Mapped[int] = mapped_column("StateID", Integer, ForeignKey("state.StateID", ondelete="CASCADE"), nullable=False)
    active: Mapped[bool] = mapped_column("Active", Boolean, default=True, server_default="true")

    # Relationships
    state: Mapped["State"] = relationship(back_populates="districts")
    units: Mapped[List["Unit"]] = relationship(back_populates="district")
    courts: Mapped[List["Court"]] = relationship(back_populates="district")
    employees: Mapped[List["Employee"]] = relationship(back_populates="district")


class UnitType(Base):
    __tablename__ = "unit_type"

    unit_type_id: Mapped[int] = mapped_column("UnitTypeID", Integer, primary_key=True)
    unit_type_name: Mapped[str] = mapped_column("UnitTypeName", String(100), nullable=False)
    city_dist_state: Mapped[Optional[str]] = mapped_column("CityDistState", String(100), nullable=True)

    # Relationships
    units: Mapped[List["Unit"]] = relationship(back_populates="unit_type")


class Unit(Base):
    __tablename__ = "unit"

    unit_id: Mapped[int] = mapped_column("UnitID", Integer, primary_key=True)
    unit_name: Mapped[str] = mapped_column("UnitName", String(150), nullable=False, index=True)
    type_id: Mapped[Optional[int]] = mapped_column("TypeID", Integer, ForeignKey("unit_type.UnitTypeID", ondelete="SET NULL"), nullable=True)
    parent_unit: Mapped[Optional[int]] = mapped_column("ParentUnit", Integer, ForeignKey("unit.UnitID", ondelete="SET NULL"), nullable=True)
    nationality_id: Mapped[Optional[int]] = mapped_column("NationalityID", Integer, nullable=True)
    state_id: Mapped[Optional[int]] = mapped_column("StateID", Integer, ForeignKey("state.StateID", ondelete="SET NULL"), nullable=True)
    district_id: Mapped[Optional[int]] = mapped_column("DistrictID", Integer, ForeignKey("district.DistrictID", ondelete="SET NULL"), nullable=True)
    active: Mapped[bool] = mapped_column("Active", Boolean, default=True, server_default="true")

    # Relationships
    unit_type: Mapped[Optional["UnitType"]] = relationship(back_populates="units")
    district: Mapped[Optional["District"]] = relationship(back_populates="units")
    state: Mapped[Optional["State"]] = relationship(back_populates="units")
    employees: Mapped[List["Employee"]] = relationship(back_populates="unit")
    
    # Self-referencing relationship for parent unit hierarchy
    parent: Mapped[Optional["Unit"]] = relationship("Unit", remote_side=[unit_id], backref="sub_units")


class Court(Base):
    __tablename__ = "court"

    court_id: Mapped[int] = mapped_column("CourtID", Integer, primary_key=True)
    court_name: Mapped[str] = mapped_column("CourtName", String(150), nullable=False, index=True)
    district_id: Mapped[Optional[int]] = mapped_column("DistrictID", Integer, ForeignKey("district.DistrictID", ondelete="SET NULL"), nullable=True)
    state_id: Mapped[Optional[int]] = mapped_column("StateID", Integer, ForeignKey("state.StateID", ondelete="SET NULL"), nullable=True)
    active: Mapped[bool] = mapped_column("Active", Boolean, default=True, server_default="true")

    # Relationships
    district: Mapped[Optional["District"]] = relationship(back_populates="courts")
    state: Mapped[Optional["State"]] = relationship(back_populates="courts")


class OccupationMaster(Base):
    __tablename__ = "occupation_master"

    occupation_id: Mapped[int] = mapped_column("OccupationID", Integer, primary_key=True)
    occupation_name: Mapped[str] = mapped_column("OccupationName", String(100), nullable=False)


class ReligionMaster(Base):
    __tablename__ = "religion_master"

    religion_id: Mapped[int] = mapped_column("ReligionID", Integer, primary_key=True)
    religion_name: Mapped[str] = mapped_column("ReligionName", String(100), nullable=False)


class CasteMaster(Base):
    __tablename__ = "caste_master"

    caste_master_id: Mapped[int] = mapped_column("caste_master_id", Integer, primary_key=True)
    caste_master_name: Mapped[str] = mapped_column("caste_master_name", String(100), nullable=False)


class Rank(Base):
    __tablename__ = "rank"

    rank_id: Mapped[int] = mapped_column("RankID", Integer, primary_key=True)
    rank_name: Mapped[str] = mapped_column("RankName", String(100), nullable=False)
    hierarchy: Mapped[Optional[int]] = mapped_column("Hierarchy", Integer, nullable=True)
    active: Mapped[bool] = mapped_column("Active", Boolean, default=True, server_default="true")

    # Relationships
    employees: Mapped[List["Employee"]] = relationship(back_populates="rank")


class Designation(Base):
    __tablename__ = "designation"

    designation_id: Mapped[int] = mapped_column("DesignationID", Integer, primary_key=True)
    designation_name: Mapped[str] = mapped_column("DesignationName", String(100), nullable=False)
    active: Mapped[bool] = mapped_column("Active", Boolean, default=True, server_default="true")
    sort_order: Mapped[Optional[int]] = mapped_column("SortOrder", Integer, nullable=True)

    # Relationships
    employees: Mapped[List["Employee"]] = relationship(back_populates="designation")


class Employee(Base):
    __tablename__ = "employee"

    employee_id: Mapped[int] = mapped_column("EmployeeID", Integer, primary_key=True)
    district_id: Mapped[Optional[int]] = mapped_column("DistrictID", Integer, ForeignKey("district.DistrictID", ondelete="SET NULL"), nullable=True)
    unit_id: Mapped[Optional[int]] = mapped_column("UnitID", Integer, ForeignKey("unit.UnitID", ondelete="SET NULL"), nullable=True)
    rank_id: Mapped[Optional[int]] = mapped_column("RankID", Integer, ForeignKey("rank.RankID", ondelete="SET NULL"), nullable=True)
    designation_id: Mapped[Optional[int]] = mapped_column("DesignationID", Integer, ForeignKey("designation.DesignationID", ondelete="SET NULL"), nullable=True)
    kgid: Mapped[Optional[str]] = mapped_column("KGID", String(50), unique=True, nullable=True, index=True)
    first_name: Mapped[str] = mapped_column("FirstName", String(100), nullable=False)
    employee_dob: Mapped[Optional[date]] = mapped_column("EmployeeDOB", Date, nullable=True)
    gender_id: Mapped[Optional[int]] = mapped_column("GenderID", Integer, nullable=True)
    blood_group_id: Mapped[Optional[int]] = mapped_column("BloodGroupID", Integer, nullable=True)
    physically_challenged: Mapped[Optional[bool]] = mapped_column("PhysicallyChallenged", Boolean, default=False, server_default="false")
    appointment_date: Mapped[Optional[date]] = mapped_column("AppointmentDate", Date, nullable=True)

    # Relationships
    district: Mapped[Optional["District"]] = relationship(back_populates="employees")
    unit: Mapped[Optional["Unit"]] = relationship(back_populates="employees")
    rank: Mapped[Optional["Rank"]] = relationship(back_populates="employees")
    designation: Mapped[Optional["Designation"]] = relationship(back_populates="employees")
