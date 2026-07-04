"""Database seeding script for KSP Sentinel AI.

This script populates reference tables (state, district, unit, employee) and generates
50 realistic FIR records (case_master, complainant_details, victim, accused).
It is idempotent – running it multiple times will not create duplicate rows.
"""

import random
from datetime import date, timedelta

from app.database.connection import SessionLocal
from app.models.masters import State, District, Unit, Employee, UnitType
from app.models.case import (
    CaseMaster,
    ComplainantDetails,
    Victim,
    Accused,
)

# Helper functions ----------------------------------------------------------

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


def seed_reference_data(session):
    """Seed static reference data (state, districts, units, employees)."""
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

    # Sample unit type – simple police station
    from app.models.masters import UnitType
    unit_type = get_or_create(session, UnitType, unit_type_name="Police Station")

    # Units (one per district for simplicity)
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

    # Employees – one per unit
    for i, unit in enumerate(units, start=1):
        get_or_create(
            session,
            Employee,
            first_name=f"Officer{i}",
            district_id=unit.district_id,
            unit_id=unit.unit_id,
        )

    return state, districts, units


def seed_fir_records(session, districts, units):
    """Create 50 FIR (case) records with related entities.
    Each case is linked to a random district/unit/employee.
    """
    employees = session.query(Employee).all()
    for i in range(1, 51):
        crime_no = f"KSP-{i:04d}"
        # Ensure idempotency
        if session.query(CaseMaster).filter_by(crime_no=crime_no).first():
            continue
        district = random.choice(districts)
        unit = next(u for u in units if u.district_id == district.district_id)
        officer = random.choice(employees)
        case = CaseMaster(
            crime_no=crime_no,
            case_no=crime_no,
            crime_registered_date=date.today() - timedelta(days=random.randint(0, 365)),
            police_person_id=officer.employee_id,
            police_station_id=unit.unit_id,
        )
        session.add(case)
        session.flush()  # get case_master_id
        # Complainant
        session.add(
            ComplainantDetails(
                case_master_id=case.case_master_id,
                complainant_name=f"Complainant {i}",
                age_year=random.randint(18, 70),
            )
        )
        # Victim
        session.add(
            Victim(
                case_master_id=case.case_master_id,
                victim_name=f"Victim {i}",
                age_year=random.randint(18, 70),
            )
        )
        # Accused
        session.add(
            Accused(
                case_master_id=case.case_master_id,
                accused_name=f"Accused {i}",
                age_year=random.randint(18, 70),
            )
        )
        session.commit()


def main():
    """Run the seeding process."""
    session = SessionLocal()
    try:
        _, districts, units = seed_reference_data(session)
        seed_fir_records(session, districts, units)
    finally:
        session.close()

if __name__ == "__main__":
    main()
