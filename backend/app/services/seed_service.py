import uuid
import random
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.database import Incident, Evidence, Property, IncidentProperty
from app.services.graph_service import add_incident_to_graph
from app.schemas.pydantic_models import PropertyItem

logger = logging.getLogger(__name__)

# Base Synthetic Datasets
PHONES = [f"98{random.randint(10000000, 99999999)}" for _ in range(29)] + ["9876543210"]
UPIS = [f"scammer{i}@upi" for i in range(1, 20)] + ["scammer123@upi"]
URLS = [f"phish{i}.site" for i in range(1, 19)] + ["fakebank.example", "secure-login-update.com"]
LOCATIONS = ["Kochi", "Cyberabad", "Jamtara", "Delhi", "Mumbai", "Bengaluru", "Jaipur", "Gurugram", "Kolkata", "Mewat", "Hyderabad", "Alwar", "Noida", "Ahmedabad", "Chennai"]
TXNS = [f"TXN{random.randint(1000, 9999)}" for _ in range(19)] + ["TXN9001"]

CRIME_CATEGORIES = [
    "UPI Phishing Scam", "Part-time Job Fraud", "Investment Scam", 
    "Sextortion", "Loan App Harassment", "Lottery Fraud", "Customer Care Scam"
]

def seed_synthetic_dataset(db: Session, num_incidents: int = 120):
    """
    Seeds PostgreSQL and Neo4j with 100+ synthetic cybercrime incidents and 10 connected clusters.
    Injects the specific Demo Scenario indicators.
    """
    # Check if already seeded
    existing_synthetic = db.query(Incident).filter(Incident.source == "SYNTHETIC").count()
    if existing_synthetic >= 50:
        logger.info(f"Dataset already contains {existing_synthetic} synthetic incidents. Skipping seed.")
        return {"status": "skipped", "count": existing_synthetic}

    logger.info(f"Seeding {num_incidents} synthetic cybercrime incidents into CyberSaarthi...")

    base_date = datetime(2026, 8, 1)

    # Dictionary to cache created Property DB objects by (type, norm)
    property_cache: dict[tuple[str, str], Property] = {}

    def get_or_create_prop(ptype: str, raw: str, norm: str) -> Property:
        key = (ptype, norm)
        if key in property_cache:
            return property_cache[key]
        
        prop = db.query(Property).filter(Property.type == ptype, Property.normalized_value == norm).first()
        if not prop:
            prop = Property(
                id=str(uuid.uuid4()),
                type=ptype,
                raw_value=raw,
                normalized_value=norm,
                created_at=datetime.utcnow()
            )
            db.add(prop)
            db.flush()
        property_cache[key] = prop
        return prop

    created_incidents = []

    # Explicit Demo Scenario Incidents (INC001, INC004, INC008, INC012, INC017, INC021)
    demo_clusters = [
        {
            "id": "INC001",
            "desc": "Victim reported losing ₹5,000 after clicking suspicious SMS link demanding electricity bill payment.",
            "days_offset": 0,
            "props": [("UPI", "scammer123@upi"), ("LOCATION", "Kochi"), ("AMOUNT", "5000"), ("DATE", "01 Aug 2026")]
        },
        {
            "id": "INC004",
            "desc": "Fraudulent caller pretending to be SBI customer executive lured victim into transferring money.",
            "days_offset": 2,
            "props": [("UPI", "scammer123@upi"), ("PHONE", "9876543210"), ("LOCATION", "Kochi"), ("AMOUNT", "12000"), ("DATE", "03 Aug 2026")]
        },
        {
            "id": "INC008",
            "desc": "Part-time job scam offering Telegram tasks leading to fraudulent banking website payment.",
            "days_offset": 6,
            "props": [("UPI", "scammer123@upi"), ("PHONE", "9876543210"), ("URL", "fakebank.example"), ("LOCATION", "Cyberabad"), ("AMOUNT", "25000")]
        },
        {
            "id": "INC012",
            "desc": "Fake investment portal asking users to deposit funds into UPI scammer account.",
            "days_offset": 10,
            "props": [("UPI", "scammer123@upi"), ("URL", "fakebank.example"), ("LOCATION", "Delhi"), ("AMOUNT", "18000")]
        },
        {
            "id": "INC017",
            "desc": "Customer care helpline scam targeting Senior Citizen. Phone call redirected victim to malicious URL.",
            "days_offset": 15,
            "props": [("UPI", "scammer123@upi"), ("PHONE", "9876543210"), ("URL", "fakebank.example"), ("LOCATION", "Kochi"), ("TRANSACTION_ID", "TXN9000")]
        },
        {
            "id": "INC021",
            "desc": "Online marketplace buyer scammed via fake QR code containing scammer UPI ID.",
            "days_offset": 20,
            "props": [("UPI", "scammer123@upi"), ("LOCATION", "Mumbai"), ("AMOUNT", "4500")]
        }
    ]

    for item in demo_clusters:
        if db.query(Incident).filter(Incident.id == item["id"]).first():
            continue
        inc_date = base_date + timedelta(days=item["days_offset"])
        inc = Incident(
            id=item["id"],
            description=item["desc"],
            timestamp=inc_date.strftime("%d %b %Y"),
            source="SYNTHETIC",
            category="UPI Phishing Scam",
            location=dict(item["props"]).get("LOCATION", "Kochi"),
            status="INVESTIGATING",
            created_at=inc_date
        )
        db.add(inc)
        db.flush()

        # Add Evidence placeholder
        ev = Evidence(
            id=str(uuid.uuid4()),
            incident_id=inc.id,
            file_name=f"evidence_{inc.id.lower()}.png",
            file_type="image/png",
            storage_path=f"uploads/synthetic_{inc.id.lower()}.png",
            sha256_hash=f"synthetic_hash_{inc.id.lower()}",
            ocr_text=item["desc"],
            created_at=inc_date
        )
        db.add(ev)

        # Link properties
        prop_items = []
        for ptype, val in item["props"]:
            p_obj = get_or_create_prop(ptype, val, val.lower() if ptype in ["UPI", "EMAIL", "URL"] else val)
            ip = IncidentProperty(incident_id=inc.id, property_id=p_obj.id, confidence=0.99, source="SYNTHETIC")
            db.add(ip)
            prop_items.append(PropertyItem(
                id=p_obj.id,
                type=ptype,
                raw_value=val,
                normalized_value=p_obj.normalized_value,
                confidence=0.99,
                source="SYNTHETIC"
            ))

        # Sync to Neo4j
        add_incident_to_graph(inc.id, inc.timestamp, inc.category, prop_items)
        created_incidents.append(inc.id)

    # Generate remaining ~110 incidents into 9 additional clusters
    for i in range(7, num_incidents + 1):
        inc_id = f"INC{i:03d}"
        if db.query(Incident).filter(Incident.id == inc_id).first():
            continue
        days_offset = random.randint(0, 30)
        inc_date = base_date + timedelta(days=days_offset)

        cluster_idx = (i % 9) + 1
        cluster_phone = PHONES[cluster_idx % len(PHONES)]
        cluster_upi = UPIS[cluster_idx % len(UPIS)]
        cluster_url = URLS[cluster_idx % len(URLS)]
        cluster_loc = LOCATIONS[cluster_idx % len(LOCATIONS)]

        category = random.choice(CRIME_CATEGORIES)
        amount = str(random.choice([500, 1000, 2500, 5000, 15000, 45000, 80000]))

        desc = f"Reported cyber incident involving {category} originating from {cluster_loc}. Scammer used phone {cluster_phone} and payment portal {cluster_upi}."

        inc = Incident(
            id=inc_id,
            description=desc,
            timestamp=inc_date.strftime("%d %b %Y"),
            source="SYNTHETIC",
            category=category,
            location=cluster_loc,
            status="NEW" if i > 90 else "INVESTIGATING",
            created_at=inc_date
        )
        db.add(inc)
        db.flush()

        # Evidence
        ev = Evidence(
            id=str(uuid.uuid4()),
            incident_id=inc.id,
            file_name=f"evidence_{inc_id.lower()}.png",
            file_type="image/png",
            storage_path=f"uploads/synthetic_{inc_id.lower()}.png",
            sha256_hash=f"hash_{inc_id.lower()}",
            ocr_text=desc,
            created_at=inc_date
        )
        db.add(ev)

        # Build 3-4 properties per incident
        props_data = [
            ("PHONE", cluster_phone),
            ("UPI", cluster_upi),
            ("LOCATION", cluster_loc),
            ("AMOUNT", amount)
        ]
        if i % 2 == 0:
            props_data.append(("URL", cluster_url))
        if i % 3 == 0:
            props_data.append(("TRANSACTION_ID", TXNS[i % len(TXNS)]))

        prop_items = []
        for ptype, val in props_data:
            p_obj = get_or_create_prop(ptype, val, val.lower() if ptype in ["UPI", "EMAIL", "URL"] else val)
            ip = IncidentProperty(incident_id=inc.id, property_id=p_obj.id, confidence=0.95, source="SYNTHETIC")
            db.add(ip)
            prop_items.append(PropertyItem(
                id=p_obj.id,
                type=ptype,
                raw_value=val,
                normalized_value=p_obj.normalized_value,
                confidence=0.95,
                source="SYNTHETIC"
            ))

        add_incident_to_graph(inc.id, inc.timestamp, inc.category, prop_items)
        created_incidents.append(inc.id)

    db.commit()
    logger.info(f"Successfully seeded {len(created_incidents)} synthetic incidents with connected clusters!")
    return {"status": "success", "count": len(created_incidents)}
