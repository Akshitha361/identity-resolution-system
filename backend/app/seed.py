# seed.py

import random
import string
from datetime import datetime

from faker import Faker
from sqlalchemy.orm import Session

from app.database import Base, engine, SessionLocal
from app.models import (
    VoterRecord,
    PoliceRecord,
    RationRecord,
    IdentityCluster,
    ClusterMember,
)

fake = Faker("en_IN")

NUM_MASTER_IDENTITIES = 10000

MISSING_FIELD_PROBABILITY = 0.08
SPELLING_MISTAKE_PROBABILITY = 0.15

NAME_PREFIX_VARIANTS = {
    "Mohammed": ["Mohammed", "Mohd", "Md", "Mohd.", "Muhammad"],
    "Mohammad": ["Mohammad", "Mohd", "Md", "Mohd.", "Muhammad"],
    "Syed": ["Syed", "Syd", "S."],
    "Shaik": ["Shaik", "Sk", "Shaikh"],
}

ADDRESS_CITY_VARIANTS = {
    "Hyderabad": ["Hyderabad", "Hyd", "Hyderabad District", "Hyderabad(T.S)"],
    "Secunderabad": ["Secunderabad", "Sec'bad", "Secbad"],
    "Bangalore": ["Bangalore", "Bengaluru", "B'lore"],
    "Chennai": ["Chennai", "Madras", "Chennai(T.N)"],
}

ADDRESS_AREA_VARIANTS = {
    "Tolichowki": ["Tolichowki", "Old Tolichowki", "Toli Chowki"],
    "Banjara Hills": ["Banjara Hills", "Banjara Hls", "B.Hills"],
    "Kukatpally": ["Kukatpally", "KPHB", "Kukatpalli"],
}

DOB_FORMATS = [
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%Y-%m-%d",
    "%d %b %Y",
]

PHONE_FORMATS = [
    "+91{number}",
    "{number}",
    "+91 {spaced}",
    "{spaced}",
    "0{number}",
]


def _random_char():
    return random.choice(string.ascii_lowercase)


def introduce_noise(value: str, mistake_probability: float = SPELLING_MISTAKE_PROBABILITY) -> str:
    """
    Randomly introduces a single character deletion, insertion,
    or replacement into a string, simulating data-entry errors.
    """
    if not value or len(value) < 3:
        return value

    if random.random() > mistake_probability:
        return value

    value_list = list(value)
    index = random.randint(0, len(value_list) - 1)
    mistake_type = random.choice(["delete", "insert", "replace"])

    if mistake_type == "delete":
        del value_list[index]
    elif mistake_type == "insert":
        value_list.insert(index, _random_char())
    elif mistake_type == "replace":
        value_list[index] = _random_char()

    return "".join(value_list)


def maybe_missing(value):
    """Return None with a small probability to simulate missing fields."""
    if random.random() < MISSING_FIELD_PROBABILITY:
        return None
    return value


def vary_name_prefix(full_name: str) -> str:
    """Applies known naming-convention variants (e.g. Mohammed -> Mohd)."""
    parts = full_name.split(" ", 1)
    if not parts:
        return full_name

    first_token = parts[0]
    rest = parts[1] if len(parts) > 1 else ""

    if first_token in NAME_PREFIX_VARIANTS:
        first_token = random.choice(NAME_PREFIX_VARIANTS[first_token])

    return f"{first_token} {rest}".strip()


def vary_address(address: str, district: str) -> str:
    """Applies realistic address abbreviation/variation patterns."""
    area = None
    city = district

    for area_key, variants in ADDRESS_AREA_VARIANTS.items():
        if area_key.lower() in address.lower():
            area = random.choice(variants)
            break

    for city_key, variants in ADDRESS_CITY_VARIANTS.items():
        if city_key.lower() in city.lower():
            city = random.choice(variants)
            break

    if area:
        varied = f"{area}, {city}"
    else:
        varied = f"{address}, {city}"

    return varied


def vary_dob_format(dob: str) -> str:
    """Reformats a DOB string (stored internally as YYYY-MM-DD) into a random format."""
    try:
        parsed = datetime.strptime(dob, "%Y-%m-%d")
    except ValueError:
        return dob

    chosen_format = random.choice(DOB_FORMATS)
    return parsed.strftime(chosen_format)


def vary_phone(phone: str) -> str:
    """Applies realistic phone formatting variations."""
    digits = "".join(filter(str.isdigit, phone))[-10:]
    spaced = f"{digits[:5]} {digits[5:]}"

    chosen_format = random.choice(PHONE_FORMATS)
    return chosen_format.format(number=digits, spaced=spaced)


def generate_master_person() -> dict:
    """
    Generates a single hidden 'MasterPerson' record.
    This object is never persisted to the database directly.
    """
    gender = random.choice(["Male", "Female"])

    if gender == "Male":
        full_name = fake.name_male()
        father_name = fake.name_male()
    else:
        full_name = fake.name_female()
        father_name = fake.name_male()

    dob = fake.date_of_birth(minimum_age=18, maximum_age=85).strftime("%Y-%m-%d")

    district = random.choice(list(ADDRESS_CITY_VARIANTS.keys()))
    area = random.choice(list(ADDRESS_AREA_VARIANTS.keys()))
    street = fake.street_address()
    address = f"{street}, {area}"

    phone = fake.msisdn()[-10:]

    return {
        "full_name": full_name,
        "father_name": father_name,
        "date_of_birth": dob,
        "gender": gender,
        "phone": phone,
        "address": address,
        "district": district,
    }


def create_voter_record(master: dict, voter_id: str) -> VoterRecord:
    """Builds a VoterRecord ORM object derived from a MasterPerson with realistic noise."""
    full_name = introduce_noise(vary_name_prefix(master["full_name"]))
    father_name = introduce_noise(vary_name_prefix(master["father_name"]))
    address = vary_address(master["address"], master["district"])
    dob = vary_dob_format(master["date_of_birth"])
    polling_station = f"PS-{fake.random_int(min=1, max=999)}"

    return VoterRecord(
        voter_id=voter_id,
        full_name=full_name,
        father_name=maybe_missing(father_name),
        dob=maybe_missing(dob),
        gender=maybe_missing(master["gender"]),
        address=maybe_missing(address),
        polling_station=maybe_missing(polling_station),
    )


def create_police_record(master: dict, case_reference: str) -> PoliceRecord:
    """Builds a PoliceRecord ORM object derived from a MasterPerson with realistic noise."""
    reported_name = introduce_noise(vary_name_prefix(master["full_name"]))
    father_name = introduce_noise(vary_name_prefix(master["father_name"]))
    address = vary_address(master["address"], master["district"])
    dob = vary_dob_format(master["date_of_birth"])
    phone = vary_phone(master["phone"])
    station = f"{master['district']} PS-{fake.random_int(min=1, max=50)}"

    return PoliceRecord(
        case_reference=case_reference,
        reported_name=reported_name,
        father_name=maybe_missing(father_name),
        dob=maybe_missing(dob),
        phone=maybe_missing(phone),
        address=maybe_missing(address),
        station=maybe_missing(station),
    )


def create_ration_record(master: dict, ration_card: str) -> RationRecord:
    """Builds a RationRecord ORM object derived from a MasterPerson with realistic noise."""
    member_name = introduce_noise(vary_name_prefix(master["full_name"]))
    head_of_family = introduce_noise(vary_name_prefix(master["father_name"]))
    address = vary_address(master["address"], master["district"])
    dob = vary_dob_format(master["date_of_birth"])

    return RationRecord(
        ration_card=ration_card,
        member_name=member_name,
        head_of_family=maybe_missing(head_of_family),
        dob=maybe_missing(dob),
        address=maybe_missing(address),
        district=maybe_missing(master["district"]),
    )


def _select_departments() -> list:
    """
    Decides which of the three departments a given master identity
    will appear in, based on the specified probability distribution.
    """
    roll = random.random()

    if roll < 0.70:
        return ["voter", "police", "ration"]
    elif roll < 0.90:
        return random.sample(["voter", "police", "ration"], 2)
    else:
        return random.sample(["voter", "police", "ration"], 1)


def seed_database(num_identities: int = NUM_MASTER_IDENTITIES) -> None:
    """
    Generates `num_identities` MasterPerson identities and inserts
    corresponding noisy department records into the database.
    MasterPerson objects themselves are never persisted.
    """
    Base.metadata.create_all(bind=engine)

    session: Session = SessionLocal()

    try:
        voter_counter = 1
        police_counter = 1
        ration_counter = 1

        voter_records = []
        police_records = []
        ration_records = []

        for _ in range(num_identities):
            master = generate_master_person()
            departments = _select_departments()

            if "voter" in departments:
                voter_id = f"VOTER{voter_counter:07d}"
                voter_records.append(create_voter_record(master, voter_id))
                voter_counter += 1

            if "police" in departments:
                case_reference = f"FIR{police_counter:07d}"
                police_records.append(create_police_record(master, case_reference))
                police_counter += 1

            if "ration" in departments:
                ration_card = f"RC{ration_counter:07d}"
                ration_records.append(create_ration_record(master, ration_card))
                ration_counter += 1

            if len(voter_records) >= 500:
                session.bulk_save_objects(voter_records)
                voter_records = []

            if len(police_records) >= 500:
                session.bulk_save_objects(police_records)
                police_records = []

            if len(ration_records) >= 500:
                session.bulk_save_objects(ration_records)
                ration_records = []

        if voter_records:
            session.bulk_save_objects(voter_records)
        if police_records:
            session.bulk_save_objects(police_records)
        if ration_records:
            session.bulk_save_objects(ration_records)

        session.commit()

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()