import datetime
import random

SYNTHETIC_PHONES = [f"98765{i:05d}" for i in range(1000, 1030)]
SYNTHETIC_UPIS = [f"scammer{i}@upi" for i in range(100, 120)]
SYNTHETIC_UPIS[0] = "scammer123@upi" # Demo scenario UPI
SYNTHETIC_PHONES[0] = "9876543210"   # Demo scenario phone

SYNTHETIC_URLS = [
    "fakebank.example",
    "phish-verify-sbi.online",
    "paytm-kyc-update.net",
    "fast-cash-loan.in",
    "lottery-win-claim.xyz",
    "gpay-reward-claim.info",
    "secure-portal-auth.com",
    "police-cyber-fine.online",
    "electricity-bill-pay.site",
    "customer-care-help.net"
] + [f"phish{i}.example" for i in range(10)]

SYNTHETIC_LOCATIONS = [
    "Kochi", "Bengaluru", "Mumbai", "Delhi", "Hyderabad",
    "Chennai", "Kolkata", "Pune", "Ahmedabad", "Jaipur",
    "Thiruvananthapuram", "Kozhikode", "Thrissur", "Ludhiana", "Noida"
]

SYNTHETIC_TXNS = [f"TXN{i:04d}" for i in range(9000, 9020)]
SYNTHETIC_TXNS[0] = "TXN9001"

def generate_synthetic_dataset(count=120):
    incidents = []
    
    # 1. Generate core demo cluster (INC001, INC004, INC008, INC012, INC017, INC021)
    demo_incident_ids = ["INC001", "INC004", "INC008", "INC012", "INC017", "INC021"]
    start_date = datetime.datetime(2026, 8, 1)
    
    for idx, inc_id in enumerate(demo_incident_ids):
        inc_date = start_date + datetime.timedelta(days=idx * 4)
        incidents.append({
            "id": inc_id,
            "description": f"Phishing incident reported involving fake bank website and unauthorized UPI debit request of ₹{800 + idx*200}.",
            "timestamp": inc_date.isoformat(),
            "source": "SYNTHETIC",
            "category": "BANKING_FRAUD",
            "location": "Kochi",
            "properties": [
                {"type": "UPI", "raw_value": "scammer123@upi", "normalized_value": "scammer123@upi", "confidence": 0.99, "source": "SYNTHETIC"},
                {"type": "PHONE", "raw_value": "9876543210", "normalized_value": "9876543210", "confidence": 0.99, "source": "SYNTHETIC"},
                {"type": "URL", "raw_value": "http://fakebank.example/login", "normalized_value": "fakebank.example", "confidence": 0.95, "source": "SYNTHETIC"},
                {"type": "LOCATION", "raw_value": "Kochi", "normalized_value": "Kochi", "confidence": 0.92, "source": "SYNTHETIC"},
                {"type": "AMOUNT", "raw_value": f"₹{800 + idx*200}", "normalized_value": str(800 + idx*200), "confidence": 0.99, "source": "SYNTHETIC"},
                {"type": "TRANSACTION_ID", "raw_value": f"TXN900{idx+1}", "normalized_value": f"TXN900{idx+1}", "confidence": 0.99, "source": "SYNTHETIC"}
            ]
        })

    # 2. Generate 9 additional connected clusters (INC022 to INC120)
    for c in range(2, 11):
        cluster_upi = SYNTHETIC_UPIS[c % len(SYNTHETIC_UPIS)]
        cluster_phone = SYNTHETIC_PHONES[c % len(SYNTHETIC_PHONES)]
        cluster_url = SYNTHETIC_URLS[c % len(SYNTHETIC_URLS)]
        cluster_loc = SYNTHETIC_LOCATIONS[c % len(SYNTHETIC_LOCATIONS)]

        for item in range(10):
            num = len(incidents) + 1
            inc_id = f"INC{num:03d}"
            inc_date = start_date + datetime.timedelta(days=random.randint(1, 30))
            
            # Shared properties to form cluster graph
            inc_props = [
                {"type": "UPI", "raw_value": cluster_upi, "normalized_value": cluster_upi, "confidence": 0.99, "source": "SYNTHETIC"},
                {"type": "PHONE", "raw_value": cluster_phone, "normalized_value": cluster_phone, "confidence": 0.99, "source": "SYNTHETIC"},
                {"type": "LOCATION", "raw_value": cluster_loc, "normalized_value": cluster_loc, "confidence": 0.90, "source": "SYNTHETIC"}
            ]

            if item % 2 == 0:
                inc_props.append({"type": "URL", "raw_value": f"http://{cluster_url}", "normalized_value": cluster_url, "confidence": 0.95, "source": "SYNTHETIC"})
            if item % 3 == 0:
                txn_val = SYNTHETIC_TXNS[(c + item) % len(SYNTHETIC_TXNS)]
                inc_props.append({"type": "TRANSACTION_ID", "raw_value": txn_val, "normalized_value": txn_val, "confidence": 0.99, "source": "SYNTHETIC"})

            incidents.append({
                "id": inc_id,
                "description": f"Cyber fraud complaint regarding unauthorized digital payment debit via suspicious handle {cluster_upi}.",
                "timestamp": inc_date.isoformat(),
                "source": "SYNTHETIC",
                "category": random.choice(["BANKING_FRAUD", "LOTTERY_SCAM", "JOB_FRAUD", "INVESTMENT_SCAM", "IDENTITY_THEFT"]),
                "location": cluster_loc,
                "properties": inc_props
            })

    return incidents
