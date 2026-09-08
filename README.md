# CyberSaarthi — OCR to Knowledge Graph Intelligence Platform

**SIH 2026 Prototype** | Obsidian-style knowledge graph for cybercrime intelligence

---

## Architecture

```
IMAGE → OCR → PROPERTY EXTRACTION → NORMALIZATION → PostgreSQL → Neo4j → GRAPH TRAVERSAL → INTERACTIVE NETWORK
```

### Tech Stack

| Layer     | Technology                              |
|-----------|-----------------------------------------|
| Frontend  | Next.js 14, TypeScript, Tailwind CSS, Cytoscape.js, Recharts, Lucide Icons |
| Backend   | Python, FastAPI, SQLAlchemy, Pydantic   |
| Database  | PostgreSQL (structured), Neo4j (graph)  |
| OCR       | PaddleOCR (with fallback parser)        |
| AI        | MockAIProvider / LLMProvider (configurable) |

---

## Quick Start (Frontend Only — No Docker Required)

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**

The frontend ships with a **built-in CyberSaarthi Engine** containing 100+ synthetic incidents and 10+ connected clusters. The complete demo workflow (upload → OCR → extraction → graph) works out of the box without any backend services.

---

## Docker Compose (Full Stack)

```bash
docker compose up --build
```

Services:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000 (Swagger docs at /docs)
- **Neo4j Browser**: http://localhost:7474
- **PostgreSQL**: localhost:5432

---

## Demo Scenario

The synthetic dataset is pre-loaded with these shared indicators:

| Indicator | Value | Appears In |
|-----------|-------|------------|
| UPI       | scammer123@upi | INC001, INC004, INC008, INC012, INC017, INC021 |
| Phone     | 9876543210 | INC001, INC004, INC008, INC012, INC017, INC021 |
| URL       | fakebank.example | INC001, INC004, INC008, INC012, INC017, INC021 |
| Location  | Kochi | INC001, INC004, INC008, INC012, INC017, INC021 |

Upload a new screenshot → the system automatically connects it to these existing clusters.

---

## Pages

| Route | Description |
|-------|-------------|
| `/` | Citizen Evidence Upload Portal |
| `/result/[id]` | Extraction Results & Historical Matches |
| `/investigator` | Intelligence Dashboard with Analytics |
| `/investigator/network` | Interactive Cytoscape.js Knowledge Graph |
| `/investigator/network/[incidentId]` | Per-Incident Network Graph |
| `/investigator/incidents/[id]` | Full Incident Detail View |

---

## API Endpoints (Backend)

```
POST   /api/v1/incidents
POST   /api/v1/incidents/{id}/evidence
GET    /api/v1/incidents/{id}
GET    /api/v1/entities/search?q=...
GET    /api/v1/graph/incident/{id}
GET    /api/v1/investigator/dashboard
GET    /api/v1/investigator/incidents
```

---

## Security

- JWT authentication ready
- Role-based access structure
- SHA-256 evidence hashing
- File validation & size limits
- Audit logging
- Environment variable configuration
- All data marked `source = SYNTHETIC`

---

## License

SIH 2026 Prototype — For demonstration purposes only.
