"""
Database seeding script for KSP Sentinel AI.

- Seeds master tables (CrimeHead, CrimeSubHead, Act, Section, CaseCategory,
  GravityOffence, CaseStatusMaster, Court) if empty.
- Generates at least 1000 realistic CaseMaster records with full related
  entities (Complainant, Victim, Accused, ActSectionAssociation).
- Idempotent: existing records (identified by unique crime_no) are skipped.
"""

import random
import string
from datetime import date, datetime, timedelta

from sqlalchemy import func

from app.database.connection import SessionLocal
from app.models.masters import (
    Court,
    State,
    District,
    Unit,
    Employee,
    UnitType,
)

from app.models.crime import (
    CrimeHead,
    CrimeSubHead,
    GravityOffence,
    CaseCategory,
    CaseStatusMaster,
    Act,
    Section,
)
from app.models.case import (
    CaseMaster,
    ComplainantDetails,
    Victim,
    Accused,
    ActSectionAssociation,
)

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def get_or_create(session, model, defaults=None, **kwargs):
    """Return an instance of *model* matching *kwargs*, creating it if needed.
    ``defaults`` is a dict of attributes to set on creation.
    """
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    params = dict(kwargs)
    if defaults:
        params.update(defaults)
    instance = model(**params)
    session.add(instance)
    session.commit()
    session.refresh(instance)
    return instance

# ---------------------------------------------------------------------------
# Master table seeding (only if tables are empty)
# ---------------------------------------------------------------------------

def seed_master_tables(session):
    # CrimeHead and sub‑heads
    crime_heads_data = {
        "Theft": ["Petty Theft", "Burglary"],
        "Murder": ["Culpable homicide", "Murder"],
        "Assault": ["Simple Assault", "Aggravated Assault"],
        "Rape": ["Sexual assault", "Gang rape"],
        "Robbery": ["Armed robbery", "Mugging"],
    }
    for head, subheads in crime_heads_data.items():
        head_obj = get_or_create(session, CrimeHead, crime_group_name=head)
        for sub in subheads:
            get_or_create(
                session,
                CrimeSubHead,
                crime_head_id=head_obj.crime_head_id,
                crime_head_name=sub,
            )

    # Act and sections (using IPC as example)
    act_obj = get_or_create(session, Act, act_code="IPC", act_description="Indian Penal Code", short_name="IPC")
    ipc_sections = ["302", "307", "376", "379", "420"]
    for sec in ipc_sections:
        get_or_create(
            session,
            Section,
            act_code=act_obj.act_code,
            section_code=sec,
            section_description=f"Section {sec} of IPC",
        )

    # Case categories
    case_categories = ["Category A", "Category B", "Category C"]
    for cat in case_categories:
        get_or_create(session, CaseCategory, lookup_value=cat)

    # Gravity offences
    gravities = ["Minor", "Major", "Severe"]
    for g in gravities:
        get_or_create(session, GravityOffence, lookup_value=g)

    # Case status master
    statuses = ["Open", "Closed", "Pending", "Under Investigation"]
    for s in statuses:
        get_or_create(session, CaseStatusMaster, case_status_name=s)

    # Courts – one per district (re‑use districts from reference data)
    districts = session.query(District).all()
    for district in districts:
        get_or_create(
            session,
            Court,
            court_name=f"{district.district_name} District Court",
            district_id=district.district_id,
            state_id=district.state_id,
        )

# ---------------------------------------------------------------------------
# Reference data seeding (state, districts, units, employees)
# ---------------------------------------------------------------------------

def seed_reference_data(session):
    # State – Karnataka (unique by name)
    state = get_or_create(session, State, state_name="Karnataka")

    # Sample districts (unique by name within state)
    district_names = [
        "Bengaluru Urban",
        "Mysuru",
        "Mangalore",
        "Hubli",
        "Belgaum",
    ]
    districts = []
    for name in district_names:
        districts.append(
            get_or_create(session, District, district_name=name, state_id=state.state_id)
        )

    # Unit type – Police Station
    unit_type = get_or_create(session, UnitType, unit_type_name="Police Station")

    # Units – one per district for simplicity
    units = []
    for district in districts:
        unit = get_or_create(
            session,
            Unit,
            unit_name=f"{district.district_name} Police Station",
            type_id=unit_type.unit_type_id,
            district_id=district.district_id,
            state_id=state.state_id,
        )
        units.append(unit)

    # Employees – one per unit (officer) – ensures unique officer names
    for i, unit in enumerate(units, start=1):
        get_or_create(
            session,
            Employee,
            first_name=f"Officer{i}",
            district_id=unit.district_id,
            unit_id=unit.unit_id,
        )

    return state, districts, units

# ---------------------------------------------------------------------------
# Helper for realistic random data
# ---------------------------------------------------------------------------

def random_name(prefix: str, idx: int) -> str:
    return f"{prefix} {idx} {random.choice(['A', 'B', 'C', 'D'])}"

def random_lat_lon() -> tuple:
    # Karnataka approx lat 12.0‑15.5, lon 74.0‑78.5
    lat = round(random.uniform(12.0, 15.5), 6)
    lon = round(random.uniform(74.0, 78.5), 6)
    return lat, lon

def random_brief_facts() -> str:
    words = [
        "theft",
        "assault",
        "burglary",
        "robbery",
        "murder",
        "rape",
        "property",
        "dispute",
        "night",
        "victim",
        "police",
        "investigation",
    ]
    return " ".join(random.sample(words, k=8)).capitalize() + "."

# ---------------------------------------------------------------------------
# Case seeding – generate at least 1000 cases with full related entities
# ---------------------------------------------------------------------------

def seed_case_records(session, districts, units):
    employees = session.query(Employee).all()
    crime_heads = session.query(CrimeHead).all()
    case_categories = session.query(CaseCategory).all()
    gravities = session.query(GravityOffence).all()
    statuses = session.query(CaseStatusMaster).all()
    courts = session.query(Court).all()
    sections = session.query(Section).filter(Section.act_code == "IPC").all()

    total_cases = 1000
    for i in range(1, total_cases + 1):
        crime_no = f"KSP-{i:06d}"
        # Idempotency – skip if already present
        if session.query(CaseMaster).filter_by(crime_no=crime_no).first():
            continue

        district = random.choice(districts)
        unit = next(u for u in units if u.district_id == district.district_id)
        officer = random.choice(employees)
        crime_head = random.choice(crime_heads)
        # Random sub‑head belonging to the selected head
        sub_head = (
            session.query(CrimeSubHead)
            .filter_by(crime_head_id=crime_head.crime_head_id)
            .order_by(func.random())
            .first()
        )
        case_category = random.choice(case_categories)
        gravity = random.choice(gravities)
        status = random.choice(statuses)
        court = random.choice(courts)
        crime_registered_date = date.today() - timedelta(days=random.randint(0, 730))
        incident_from = datetime.combine(crime_registered_date, datetime.min.time()) - timedelta(days=random.randint(0, 30))
        incident_to = incident_from + timedelta(days=random.randint(0, 5))
        lat, lon = random_lat_lon()
        brief = random_brief_facts()

        case = CaseMaster(
            crime_no=crime_no,
            case_no=crime_no,
            crime_registered_date=crime_registered_date,
            police_person_id=officer.employee_id,
            police_station_id=unit.unit_id,
            crime_major_head_id=crime_head.crime_head_id,
            crime_minor_head_id=sub_head.crime_sub_head_id if sub_head else None,
            case_category_id=case_category.case_category_id,
            gravity_offence_id=gravity.gravity_offence_id,
            case_status_id=status.case_status_id,
            court_id=court.court_id,
            incident_from_date=incident_from,
            incident_to_date=incident_to,
            latitude=lat,
            longitude=lon,
            brief_facts=brief,
        )
        session.add(case)
        session.flush()  # obtain case_master_id

        # Complainant – single per case
        session.add(
            ComplainantDetails(
                case_master_id=case.case_master_id,
                complainant_name=random_name("Complainant", i),
                age_year=random.randint(18, 70),
            )
        )

        # Victims – 1‑3 per case
        victim_count = random.randint(1, 3)
        for v in range(victim_count):
            session.add(
                Victim(
                    case_master_id=case.case_master_id,
                    victim_name=random_name("Victim", i * 10 + v),
                    age_year=random.randint(5, 80),
                    gender_id=random.choice([1, 2]),
                )
            )

        # Accused – 1‑2 per case
        accused_count = random.randint(1, 2)
        for a in range(accused_count):
            session.add(
                Accused(
                    case_master_id=case.case_master_id,
                    accused_name=random_name("Accused", i * 10 + a),
                    age_year=random.randint(18, 70),
                    gender_id=random.choice([1, 2]),
                )
            )

        # Act‑Section association – attach 1‑3 sections randomly
        assoc_sections = random.sample(sections, k=random.randint(1, 3))
        for sec in assoc_sections:
            session.add(
                ActSectionAssociation(
                    case_master_id=case.case_master_id,
                    act_code=sec.act_code,
                    section_code=sec.section_code,
                )
            )

        session.commit()

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    """Run the full seeding process."""
    session = SessionLocal()
    try:
        # Seed reference data (states, districts, units, employees)
        _, districts, units = seed_reference_data(session)
        # Seed master lookup tables if empty
        seed_master_tables(session)
        # Seed case records
        seed_case_records(session, districts, units)
    finally:
        session.close()

if __name__ == "__main__":
    main()
