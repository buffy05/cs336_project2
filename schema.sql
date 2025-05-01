-- Schema definition extracted from Project 1 for LLM context in Project 2

-- Reference Tables --

CREATE TABLE State (
    state_code SMALLINT PRIMARY KEY,
    state_name TEXT NOT NULL,
    state_abbr TEXT NOT NULL
);

CREATE TABLE County (
    county_code SMALLINT NOT NULL,
    state_code SMALLINT NOT NULL REFERENCES State(state_code),
    county_name TEXT NOT NULL,
    PRIMARY KEY (county_code, state_code)
);

CREATE TABLE MSAMDLookup (
    msamd NUMERIC PRIMARY KEY,
    msamd_name TEXT NOT NULL
);

CREATE TABLE Agency (
    agency_code SMALLINT PRIMARY KEY, 
    agency_abbr TEXT NOT NULL, 
    agency_name TEXT NOT NULL
); 

CREATE TABLE LoanType (
    loan_type SMALLINT PRIMARY KEY, 
    loan_type_name TEXT NOT NULL
); 

CREATE TABLE PropertyType (
    property_type SMALLINT PRIMARY KEY, 
    property_type_name TEXT NOT NULL
); 

CREATE TABLE LoanPurpose (
    loan_purpose SMALLINT PRIMARY KEY, 
    loan_purpose_name TEXT NOT NULL
); 

CREATE TABLE OwnerOccupancy (
    owner_occupancy SMALLINT PRIMARY KEY, 
    owner_occupancy_name TEXT NOT NULL
); 

CREATE TABLE PreapprovalStatus (
    preapproval SMALLINT PRIMARY KEY, 
    preapproval_name TEXT NOT NULL
);  

CREATE TABLE ActionTaken (
    action_taken SMALLINT PRIMARY KEY, 
    action_taken_name TEXT NOT NULL
); 

CREATE TABLE Ethnicity (
    applicant_ethnicity SMALLINT PRIMARY KEY, 
    applicant_ethnicity_name TEXT NOT NULL
); 

CREATE TABLE Race (
    applicant_race SMALLINT PRIMARY KEY, 
    applicant_race_name TEXT NOT NULL
); 

CREATE TABLE Sex (
    applicant_sex SMALLINT PRIMARY KEY, 
    applicant_sex_name TEXT NOT NULL
);  

CREATE TABLE PurchaserType (
    purchaser_type SMALLINT PRIMARY KEY, 
    purchaser_type_name TEXT NOT NULL
); 

CREATE TABLE DenialReason (
    denial_reason SMALLINT PRIMARY KEY, 
    denial_reason_name TEXT NOT NULL
); 

CREATE TABLE HOEPAStatus (
    hoepa_status SMALLINT PRIMARY KEY, 
    hoepa_status_name TEXT NOT NULL
); 

CREATE TABLE LienStatus (
    lien_status SMALLINT PRIMARY KEY, 
    lien_status_name TEXT NOT NULL
); 

CREATE TABLE Location (
    location_id SERIAL PRIMARY KEY,
    census_tract_number NUMERIC NOT NULL,
    county_code SMALLINT NOT NULL,
    state_code SMALLINT NOT NULL,
    msamd NUMERIC REFERENCES MSAMDLookup(msamd),
    population INT,
    minority_population NUMERIC,
    hud_median_family_income INT,
    tract_to_msamd_income NUMERIC,
    number_of_owner_occupied_units INT,
    number_of_1_to_4_family_units INT,
    FOREIGN KEY (county_code, state_code) REFERENCES County(county_code, state_code),
    CONSTRAINT location_unique_key UNIQUE (census_tract_number, county_code, state_code)
);

CREATE TABLE Application (
    application_id SERIAL PRIMARY KEY,
    as_of_year SMALLINT,
    respondent_id TEXT,
    agency_code SMALLINT REFERENCES Agency(agency_code),
    loan_type SMALLINT REFERENCES LoanType(loan_type),
    property_type SMALLINT REFERENCES PropertyType(property_type),
    loan_purpose SMALLINT REFERENCES LoanPurpose(loan_purpose),
    owner_occupancy SMALLINT REFERENCES OwnerOccupancy(owner_occupancy),
    loan_amount_000s INT,
    preapproval SMALLINT REFERENCES PreapprovalStatus(preapproval),
    action_taken SMALLINT REFERENCES ActionTaken(action_taken),
    applicant_ethnicity SMALLINT REFERENCES Ethnicity(applicant_ethnicity),
    co_applicant_ethnicity SMALLINT REFERENCES Ethnicity(applicant_ethnicity),
    applicant_sex SMALLINT REFERENCES Sex(applicant_sex),
    co_applicant_sex SMALLINT REFERENCES Sex(applicant_sex),
    applicant_income_000s INT,
    purchaser_type SMALLINT REFERENCES PurchaserType(purchaser_type),
    denial_reason_1 SMALLINT REFERENCES DenialReason(denial_reason),
    denial_reason_2 SMALLINT REFERENCES DenialReason(denial_reason),
    denial_reason_3 SMALLINT REFERENCES DenialReason(denial_reason),
    rate_spread NUMERIC,
    hoepa_status SMALLINT REFERENCES HOEPAStatus(hoepa_status),
    lien_status SMALLINT REFERENCES LienStatus(lien_status),
    application_date_indicator SMALLINT,
    sequence_number INT,
    location_id INT REFERENCES Location(location_id)
);

CREATE TABLE ApplicantRace (
    application_id INT NOT NULL REFERENCES Application(application_id),
    race_code SMALLINT NOT NULL REFERENCES Race(applicant_race),
    race_number SMALLINT NOT NULL,
    PRIMARY KEY (application_id, race_number)
);

CREATE TABLE CoApplicantRace (
    application_id INT NOT NULL REFERENCES Application(application_id),
    race_code SMALLINT NOT NULL REFERENCES Race(applicant_race),
    race_number SMALLINT NOT NULL,
    PRIMARY KEY (application_id, race_number)
);
