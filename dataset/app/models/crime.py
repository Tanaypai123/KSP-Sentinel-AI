from typing import List, Optional
from sqlalchemy import String, Integer, Boolean, ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class CaseCategory(Base):
    __tablename__ = "case_category"

    case_category_id: Mapped[int] = mapped_column("CaseCategoryID", Integer, primary_key=True)
    lookup_value: Mapped[str] = mapped_column("LookupValue", String(100), nullable=False)


class GravityOffence(Base):
    __tablename__ = "gravity_offence"

    gravity_offence_id: Mapped[int] = mapped_column("GravityOffenceID", Integer, primary_key=True)
    lookup_value: Mapped[str] = mapped_column("LookupValue", String(100), nullable=False)


class CaseStatusMaster(Base):
    __tablename__ = "case_status_master"

    case_status_id: Mapped[int] = mapped_column("CaseStatusID", Integer, primary_key=True)
    case_status_name: Mapped[str] = mapped_column("CaseStatusName", String(100), nullable=False)


class CrimeHead(Base):
    __tablename__ = "crime_head"

    crime_head_id: Mapped[int] = mapped_column("CrimeHeadID", Integer, primary_key=True)
    crime_group_name: Mapped[str] = mapped_column("CrimeGroupName", String(150), nullable=False, index=True)
    active: Mapped[bool] = mapped_column("Active", Boolean, default=True, server_default="true")

    # Relationships
    sub_heads: Mapped[List["CrimeSubHead"]] = relationship(back_populates="crime_head")
    act_sections: Mapped[List["CrimeHeadActSection"]] = relationship(back_populates="crime_head")


class CrimeSubHead(Base):
    __tablename__ = "crime_sub_head"

    crime_sub_head_id: Mapped[int] = mapped_column("CrimeSubHeadID", Integer, primary_key=True)
    crime_head_id: Mapped[int] = mapped_column("CrimeHeadID", Integer, ForeignKey("crime_head.CrimeHeadID", ondelete="CASCADE"), nullable=False)
    crime_head_name: Mapped[str] = mapped_column("CrimeHeadName", String(150), nullable=False)
    seq_id: Mapped[Optional[int]] = mapped_column("SeqID", Integer, nullable=True)

    # Relationships
    crime_head: Mapped["CrimeHead"] = relationship(back_populates="sub_heads")


class Act(Base):
    __tablename__ = "act"

    act_code: Mapped[str] = mapped_column("ActCode", String(50), primary_key=True)
    act_description: Mapped[str] = mapped_column("ActDescription", String(250), nullable=False)
    short_name: Mapped[str] = mapped_column("ShortName", String(100), nullable=False)
    active: Mapped[bool] = mapped_column("Active", Boolean, default=True, server_default="true")

    # Relationships
    sections: Mapped[List["Section"]] = relationship(back_populates="act")


class Section(Base):
    __tablename__ = "section"

    act_code: Mapped[str] = mapped_column("ActCode", String(50), ForeignKey("act.ActCode", ondelete="CASCADE"), primary_key=True)
    section_code: Mapped[str] = mapped_column("SectionCode", String(50), primary_key=True)
    section_description: Mapped[str] = mapped_column("SectionDescription", String(500), nullable=False)
    active: Mapped[bool] = mapped_column("Active", Boolean, default=True, server_default="true")

    # Relationships
    act: Mapped["Act"] = relationship(back_populates="sections")
    crime_head_linkages: Mapped[List["CrimeHeadActSection"]] = relationship(back_populates="section_rel")


class CrimeHeadActSection(Base):
    __tablename__ = "crime_head_act_section"

    crime_head_id: Mapped[int] = mapped_column("CrimeHeadID", Integer, ForeignKey("crime_head.CrimeHeadID", ondelete="CASCADE"), primary_key=True)
    act_code: Mapped[str] = mapped_column("ActCode", String(50), primary_key=True)
    section_code: Mapped[str] = mapped_column("SectionCode", String(50), primary_key=True)

    # Composite Foreign Key mapping to Section(act_code, section_code)
    __table_args__ = (
        ForeignKeyConstraint(
            ["ActCode", "SectionCode"],
            ["section.ActCode", "section.SectionCode"],
            ondelete="CASCADE"
        ),
    )

    # Relationships
    crime_head: Mapped["CrimeHead"] = relationship(back_populates="act_sections")
    section_rel: Mapped["Section"] = relationship(back_populates="crime_head_linkages")
