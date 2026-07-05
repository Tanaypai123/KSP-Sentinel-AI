"""Compatibility Report – Verified ORM Relationships and Columns

The following information is extracted directly from the SQLAlchemy model files
under ``app/models``.  Only attributes that exist in the source code are listed;
no assumptions or invented names are made.

---

**CaseMaster** (``app/models/case.py``)
- **Attributes (mapped_column)**:
  - ``case_master_id`` – primary key
  - ``crime_no`` – unique FIR identifier
  - ``case_no``
  - ``crime_registered_date`` – ``Date``
  - ``police_person_id`` (FK → ``employee.EmployeeID``)
  - ``police_station_id`` (FK → ``unit.UnitID``)
  - ``case_category_id`` (FK → ``case_category.CaseCategoryID``)
  - ``gravity_offence_id`` (FK → ``gravity_offence.GravityOffenceID``)
  - ``crime_major_head_id`` (FK → ``crime_head.CrimeHeadID``)
  - ``crime_minor_head_id`` (FK → ``crime_sub_head.CrimeSubHeadID``)
  - ``case_status_id`` (FK → ``case_status_master.CaseStatusID``)
  - ``court_id`` (FK → ``court.CourtID``)
  - ``incident_from_date``, ``incident_to_date``, ``info_received_ps_date`` (DateTime)
  - ``latitude`` (Numeric)
  - ``longitude`` (Numeric)
  - ``brief_facts`` (String)
- **Relationships**:
  - ``police_person`` → ``Employee`` (foreign_keys=[police_person_id])
  - ``police_station`` → ``Unit``
  - ``case_category`` → ``CaseCategory``
  - ``gravity_offence`` → ``GravityOffence``
  - ``crime_major_head`` → ``CrimeHead``
  - ``crime_minor_head`` → ``CrimeSubHead``
  - ``case_status`` → ``CaseStatusMaster``
  - ``court`` → ``Court``
  - ``complainants`` → ``ComplainantDetails`` (back_populates="case_master")
  - ``victims`` → ``Victim`` (back_populates="case_master")
  - ``accused_links`` → ``Accused`` (back_populates="case_master")
  - ``arrests`` → ``ArrestSurrender`` (back_populates="case_master")
  - ``chargesheets`` → ``ChargesheetDetails`` (back_populates="case_master")
  - ``act_sections`` → ``ActSectionAssociation`` (back_populates="case_master")

**Accused** (``app/models/case.py``)
- **Attributes**:
  - ``accused_master_id`` – primary key
  - ``case_master_id`` (FK → ``case_master.CaseMasterID``)
  - ``accused_name`` (String)
  - ``age_year`` (Integer, optional)
  - ``gender_id`` (Integer, optional)
  - ``person_id`` (String, optional)
- **Relationships**:
  - ``case_master`` → ``CaseMaster`` (back_populates="accused_links")
  - ``arrests`` → ``ArrestSurrender`` (secondary="inv_arrestsurrenderaccused", back_populates="accused_persons")

**Victim** (``app/models/case.py``)
- **Attributes**:
  - ``victim_master_id`` – primary key
  - ``case_master_id`` (FK → ``case_master.CaseMasterID``)
  - ``victim_name`` (String)
  - ``age_year`` (Integer, optional)
  - ``gender_id`` (Integer, optional)
  - ``victim_police`` (String, optional)
- **Relationships**:
  - ``case_master`` → ``CaseMaster`` (back_populates="victims")

**ComplainantDetails** (``app/models/case.py``)
- **Attributes**:
  - ``complainant_id`` – primary key
  - ``case_master_id`` (FK → ``case_master.CaseMasterID``)
  - ``complainant_name`` (String)
  - ``age_year`` (Integer, optional)
  - ``occupation_id`` (FK → ``occupation_master.OccupationID``)
  - ``religion_id`` (FK → ``religion_master.ReligionID``)
  - ``caste_id`` (FK → ``caste_master.caste_master_id``)
  - ``gender_id`` (Integer, optional)
- **Relationships**:
  - ``case_master`` → ``CaseMaster`` (back_populates="complainants")
  - ``occupation`` → ``OccupationMaster``
  - ``religion`` → ``ReligionMaster``
  - ``caste`` → ``CasteMaster``

**CrimeHead** (``app/models/crime.py``)
- **Attributes**:
  - ``crime_head_id`` – primary key
  - ``crime_group_name`` (String)
  - ``active`` (Boolean)
- **Relationships**:
  - ``sub_heads`` → ``CrimeSubHead`` (back_populates="crime_head")
  - ``act_sections`` → ``CrimeHeadActSection`` (back_populates="crime_head")

---

All subsequent code must reference only the attributes and relationships listed
above.
"""
