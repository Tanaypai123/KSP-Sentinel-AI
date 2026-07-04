from typing import List, Optional
from datetime import date, datetime
from sqlalchemy import String, Integer, Boolean, Date, DateTime, Numeric, ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class CaseMaster(Base):
    __tablename__ = "case_master"

    case_master_id: Mapped[int] = mapped_column("CaseMasterID", Integer, primary_key=True)
    crime_no: Mapped[str] = mapped_column("CrimeNo", String(100), unique=True, nullable=False, index=True)
    case_no: Mapped[str] = mapped_column("CaseNo", String(100), nullable=False, index=True)
    crime_registered_date: Mapped[date] = mapped_column("CrimeRegisteredDate", Date, nullable=False)
    
    # Foreign Keys
    police_person_id: Mapped[Optional[int]] = mapped_column("PolicePersonID", Integer, ForeignKey("employee.EmployeeID", ondelete="SET NULL"), nullable=True)
    police_station_id: Mapped[Optional[int]] = mapped_column("PoliceStationID", Integer, ForeignKey("unit.UnitID", ondelete="SET NULL"), nullable=True)
    case_category_id: Mapped[Optional[int]] = mapped_column("CaseCategoryID", Integer, ForeignKey("case_category.CaseCategoryID", ondelete="SET NULL"), nullable=True)
    gravity_offence_id: Mapped[Optional[int]] = mapped_column("GravityOffenceID", Integer, ForeignKey("gravity_offence.GravityOffenceID", ondelete="SET NULL"), nullable=True)
    crime_major_head_id: Mapped[Optional[int]] = mapped_column("CrimeMajorHeadID", Integer, ForeignKey("crime_head.CrimeHeadID", ondelete="SET NULL"), nullable=True)
    crime_minor_head_id: Mapped[Optional[int]] = mapped_column("CrimeMinorHeadID", Integer, ForeignKey("crime_sub_head.CrimeSubHeadID", ondelete="SET NULL"), nullable=True)
    case_status_id: Mapped[Optional[int]] = mapped_column("CaseStatusID", Integer, ForeignKey("case_status_master.CaseStatusID", ondelete="SET NULL"), nullable=True)
    court_id: Mapped[Optional[int]] = mapped_column("CourtID", Integer, ForeignKey("court.CourtID", ondelete="SET NULL"), nullable=True)

    # Occurrence & Location Columns (Direct in CaseMaster in ER diagram)
    incident_from_date: Mapped[Optional[datetime]] = mapped_column("IncidentFromDate", DateTime, nullable=True)
    incident_to_date: Mapped[Optional[datetime]] = mapped_column("IncidentToDate", DateTime, nullable=True)
    info_received_ps_date: Mapped[Optional[datetime]] = mapped_column("InfoReceivedPSDate", DateTime, nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column("latitude", Numeric(10, 8), nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column("longitude", Numeric(11, 8), nullable=True)
    brief_facts: Mapped[Optional[str]] = mapped_column("BriefFacts", String, nullable=True)

    # Relationships
    police_person: Mapped[Optional["Employee"]] = relationship("Employee", foreign_keys=[police_person_id])
    police_station: Mapped[Optional["Unit"]] = relationship("Unit")
    case_category: Mapped[Optional["CaseCategory"]] = relationship("CaseCategory")
    gravity_offence: Mapped[Optional["GravityOffence"]] = relationship("GravityOffence")
    crime_major_head: Mapped[Optional["CrimeHead"]] = relationship("CrimeHead")
    crime_minor_head: Mapped[Optional["CrimeSubHead"]] = relationship("CrimeSubHead")
    case_status: Mapped[Optional["CaseStatusMaster"]] = relationship("CaseStatusMaster")
    court: Mapped[Optional["Court"]] = relationship("Court")

    # One-to-Many
    complainants: Mapped[List["ComplainantDetails"]] = relationship(back_populates="case_master")
    victims: Mapped[List["Victim"]] = relationship(back_populates="case_master")
    accused_links: Mapped[List["Accused"]] = relationship(back_populates="case_master")
    arrests: Mapped[List["ArrestSurrender"]] = relationship(back_populates="case_master")
    chargesheets: Mapped[List["ChargesheetDetails"]] = relationship(back_populates="case_master")
    act_sections: Mapped[List["ActSectionAssociation"]] = relationship(back_populates="case_master")


class ComplainantDetails(Base):
    __tablename__ = "complainant_details"

    complainant_id: Mapped[int] = mapped_column("ComplainantID", Integer, primary_key=True)
    case_master_id: Mapped[int] = mapped_column("CaseMasterID", Integer, ForeignKey("case_master.CaseMasterID", ondelete="CASCADE"), nullable=False)
    complainant_name: Mapped[str] = mapped_column("ComplainantName", String(150), nullable=False, index=True)
    age_year: Mapped[Optional[int]] = mapped_column("AgeYear", Integer, nullable=True)
    
    # Lookup references
    occupation_id: Mapped[Optional[int]] = mapped_column("OccupationID", Integer, ForeignKey("occupation_master.OccupationID", ondelete="SET NULL"), nullable=True)
    religion_id: Mapped[Optional[int]] = mapped_column("ReligionID", Integer, ForeignKey("religion_master.ReligionID", ondelete="SET NULL"), nullable=True)
    caste_id: Mapped[Optional[int]] = mapped_column("CasteID", Integer, ForeignKey("caste_master.caste_master_id", ondelete="SET NULL"), nullable=True)
    gender_id: Mapped[Optional[int]] = mapped_column("GenderID", Integer, nullable=True)

    # Relationships
    case_master: Mapped["CaseMaster"] = relationship(back_populates="complainants")
    occupation: Mapped[Optional["OccupationMaster"]] = relationship("OccupationMaster")
    religion: Mapped[Optional["ReligionMaster"]] = relationship("ReligionMaster")
    caste: Mapped[Optional["CasteMaster"]] = relationship("CasteMaster")


class ActSectionAssociation(Base):
    __tablename__ = "act_section_association"

    case_master_id: Mapped[int] = mapped_column("CaseMasterID", Integer, ForeignKey("case_master.CaseMasterID", ondelete="CASCADE"), primary_key=True)
    act_code: Mapped[str] = mapped_column("ActID", String(50), primary_key=True)
    section_code: Mapped[str] = mapped_column("SectionID", String(50), primary_key=True)
    act_order_id: Mapped[Optional[int]] = mapped_column("ActOrderID", Integer, nullable=True)
    section_order_id: Mapped[Optional[int]] = mapped_column("SectionOrderID", Integer, nullable=True)

    # Composite Foreign Key mapping to Section(act_code, section_code)
    __table_args__ = (
        ForeignKeyConstraint(
            ["ActID", "SectionID"],
            ["section.ActCode", "section.SectionCode"],
            ondelete="CASCADE"
        ),
    )

    # Relationships
    case_master: Mapped["CaseMaster"] = relationship(back_populates="act_sections")
    section: Mapped["Section"] = relationship("Section")


class Victim(Base):
    __tablename__ = "victim"

    victim_master_id: Mapped[int] = mapped_column("VictimMasterID", Integer, primary_key=True)
    case_master_id: Mapped[int] = mapped_column("CaseMasterID", Integer, ForeignKey("case_master.CaseMasterID", ondelete="CASCADE"), nullable=False)
    victim_name: Mapped[str] = mapped_column("VictimName", String(150), nullable=False, index=True)
    age_year: Mapped[Optional[int]] = mapped_column("AgeYear", Integer, nullable=True)
    gender_id: Mapped[Optional[int]] = mapped_column("GenderID", Integer, nullable=True)
    victim_police: Mapped[Optional[str]] = mapped_column("VictimPolice", String(10), nullable=True) # e.g. "1" or "0"

    # Relationships
    case_master: Mapped["CaseMaster"] = relationship(back_populates="victims")


class Accused(Base):
    __tablename__ = "accused"

    accused_master_id: Mapped[int] = mapped_column("AccusedMasterID", Integer, primary_key=True)
    case_master_id: Mapped[int] = mapped_column("CaseMasterID", Integer, ForeignKey("case_master.CaseMasterID", ondelete="CASCADE"), nullable=False)
    accused_name: Mapped[str] = mapped_column("AccusedName", String(150), nullable=False, index=True)
    age_year: Mapped[Optional[int]] = mapped_column("AgeYear", Integer, nullable=True)
    gender_id: Mapped[Optional[int]] = mapped_column("GenderID", Integer, nullable=True)
    person_id: Mapped[Optional[str]] = mapped_column("PersonID", String(50), nullable=True)

    # Relationships
    case_master: Mapped["CaseMaster"] = relationship(back_populates="accused_links")
    arrests: Mapped[List["ArrestSurrender"]] = relationship(
        "ArrestSurrender",
        secondary="inv_arrestsurrenderaccused",
        back_populates="accused_persons"
    )


class ArrestSurrender(Base):
    __tablename__ = "arrest_surrender"

    arrest_surrender_id: Mapped[int] = mapped_column("ArrestSurrenderID", Integer, primary_key=True)
    case_master_id: Mapped[int] = mapped_column("CaseMasterID", Integer, ForeignKey("case_master.CaseMasterID", ondelete="CASCADE"), nullable=False)
    arrest_surrender_type_id: Mapped[Optional[int]] = mapped_column("ArrestSurrenderTypeID", Integer, nullable=True)
    arrest_surrender_date: Mapped[Optional[date]] = mapped_column("ArrestSurrenderDate", Date, nullable=True)
    
    # Location reference
    arrest_surrender_state_id: Mapped[Optional[int]] = mapped_column("ArrestSurrenderStateId", Integer, ForeignKey("state.StateID", ondelete="SET NULL"), nullable=True)
    arrest_surrender_district_id: Mapped[Optional[int]] = mapped_column("ArrestSurrenderDistrictId", Integer, ForeignKey("district.DistrictID", ondelete="SET NULL"), nullable=True)
    police_station_id: Mapped[Optional[int]] = mapped_column("PoliceStationID", Integer, ForeignKey("unit.UnitID", ondelete="SET NULL"), nullable=True)
    
    # Employee reference
    io_id: Mapped[Optional[int]] = mapped_column("IOID", Integer, ForeignKey("employee.EmployeeID", ondelete="SET NULL"), nullable=True)
    court_id: Mapped[Optional[int]] = mapped_column("CourtID", Integer, ForeignKey("court.CourtID", ondelete="SET NULL"), nullable=True)
    accused_master_id: Mapped[Optional[int]] = mapped_column("AccusedMasterID", Integer, ForeignKey("accused.AccusedMasterID", ondelete="SET NULL"), nullable=True)
    
    # Flags
    is_accused: Mapped[Optional[bool]] = mapped_column("IsAccused", Boolean, default=True, server_default="true")
    is_complainant_accused: Mapped[Optional[bool]] = mapped_column("IsComplainantAccused", Boolean, default=False, server_default="false")

    # Relationships
    case_master: Mapped["CaseMaster"] = relationship(back_populates="arrests")
    state: Mapped[Optional["State"]] = relationship("State")
    district: Mapped[Optional["District"]] = relationship("District")
    police_station: Mapped[Optional["Unit"]] = relationship("Unit")
    io_officer: Mapped[Optional["Employee"]] = relationship("Employee", foreign_keys=[io_id])
    court: Mapped[Optional["Court"]] = relationship("Court")
    
    accused_persons: Mapped[List["Accused"]] = relationship(
        "Accused",
        secondary="inv_arrestsurrenderaccused",
        back_populates="arrests"
    )


class InvArrestSurrenderAccused(Base):
    __tablename__ = "inv_arrestsurrenderaccused"

    arrest_surrender_id: Mapped[int] = mapped_column("ArrestSurrenderID", Integer, ForeignKey("arrest_surrender.ArrestSurrenderID", ondelete="CASCADE"), primary_key=True)
    accused_master_id: Mapped[int] = mapped_column("AccusedMasterID", Integer, ForeignKey("accused.AccusedMasterID", ondelete="CASCADE"), primary_key=True)


class ChargesheetDetails(Base):
    __tablename__ = "chargesheet_details"

    csid: Mapped[int] = mapped_column("CSID", Integer, primary_key=True)
    case_master_id: Mapped[int] = mapped_column("CaseMasterID", Integer, ForeignKey("case_master.CaseMasterID", ondelete="CASCADE"), nullable=False)
    csdate: Mapped[Optional[datetime]] = mapped_column("csdate", DateTime, nullable=True)
    cstype: Mapped[Optional[str]] = mapped_column("cstype", String(10), nullable=True)
    police_person_id: Mapped[Optional[int]] = mapped_column("PolicePersonID", Integer, ForeignKey("employee.EmployeeID", ondelete="SET NULL"), nullable=True)

    # Relationships
    case_master: Mapped["CaseMaster"] = relationship(back_populates="chargesheets")
    police_person: Mapped[Optional["Employee"]] = relationship("Employee")
