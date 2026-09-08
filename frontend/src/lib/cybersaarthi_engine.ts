export interface Property {
  id: string;
  type: string;
  raw_value: string;
  normalized_value: string;
  confidence: number;
  source: string;
}

export interface Incident {
  id: string;
  description: string;
  timestamp: string;
  source: string;
  category: string;
  location: string;
  properties: Property[];
  ocr_text?: string;
  evidence_filename?: string;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  properties: Record<string, any>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  rel_type: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

const DEMO_UPIS = ["scammer123@upi", "fraudster99@upi", "paytm-fake88@upi", "scam-merchant@upi", "claim-prize@upi"];
const DEMO_PHONES = ["9876543210", "9876500001", "9876500002", "9876500003", "9876500004"];
const DEMO_URLS = ["fakebank.example", "phish-verify-sbi.online", "paytm-kyc-update.net", "fast-cash-loan.in"];
const DEMO_LOCATIONS = ["Kochi", "Bengaluru", "Mumbai", "Delhi", "Hyderabad", "Chennai"];

// Pre-seeded Synthetic Dataset
class CyberSaarthiEngine {
  private incidents: Map<string, Incident> = new Map();
  private properties: Map<string, Property> = new Map(); // key = normalized_value
  private graphNodes: Map<string, GraphNode> = new Map();
  private graphEdges: Set<string> = new Set();
  private edgesList: GraphEdge[] = [];

  constructor() {
    this.seedSyntheticDataset();
  }

  private seedSyntheticDataset() {
    const demoDates = [
      "2026-08-01T10:30:00Z",
      "2026-08-03T14:15:00Z",
      "2026-08-07T09:45:00Z",
      "2026-08-14T16:20:00Z",
      "2026-08-21T11:00:00Z",
      "2026-08-27T18:30:00Z"
    ];

    // Create 6 core incidents in the main demo cluster (INC001, INC004, INC008, INC012, INC017, INC021)
    const demoIds = ["INC001", "INC004", "INC008", "INC012", "INC017", "INC021"];
    demoIds.forEach((incId, idx) => {
      const inc: Incident = {
        id: incId,
        description: `Phishing transaction reported involving fake payment portal and unauthorized debit request.`,
        timestamp: demoDates[idx % demoDates.length],
        source: "SYNTHETIC",
        category: "BANKING_FRAUD",
        location: "Kochi",
        ocr_text: `Payment of ₹${800 + idx * 200} successful to scammer123@upi.\nTransaction ID: TXN900${idx+1}\nContact phone: 9876543210\nLocation: Kochi\nPhishing URL: http://fakebank.example/auth`,
        properties: [
          { id: `p_upi_${idx}`, type: "UPI", raw_value: "scammer123@upi", normalized_value: "scammer123@upi", confidence: 0.99, source: "SYNTHETIC" },
          { id: `p_ph_${idx}`, type: "PHONE", raw_value: "9876543210", normalized_value: "9876543210", confidence: 0.99, source: "SYNTHETIC" },
          { id: `p_url_${idx}`, type: "URL", raw_value: "http://fakebank.example/login", normalized_value: "fakebank.example", confidence: 0.95, source: "SYNTHETIC" },
          { id: `p_loc_${idx}`, type: "LOCATION", raw_value: "Kochi", normalized_value: "Kochi", confidence: 0.92, source: "SYNTHETIC" },
          { id: `p_amt_${idx}`, type: "AMOUNT", raw_value: `₹${800 + idx * 200}`, normalized_value: `${800 + idx * 200}`, confidence: 0.99, source: "SYNTHETIC" },
          { id: `p_txn_${idx}`, type: "TRANSACTION_ID", raw_value: `TXN900${idx+1}`, normalized_value: `TXN900${idx+1}`, confidence: 0.99, source: "SYNTHETIC" }
        ]
      };
      this.addIncidentToGraph(inc);
    });

    // Create 100 additional synthetic incidents across 10 connected clusters
    for (let c = 1; c <= 10; c++) {
      const upi = DEMO_UPIS[c % DEMO_UPIS.length];
      const phone = DEMO_PHONES[c % DEMO_PHONES.length];
      const url = DEMO_URLS[c % DEMO_URLS.length];
      const loc = DEMO_LOCATIONS[c % DEMO_LOCATIONS.length];

      for (let i = 0; i < 10; i++) {
        const count = this.incidents.size + 1;
        const incId = `INC${count < 100 ? '0' : ''}${count < 10 ? '0' : ''}${count}`;
        const day = (i * 3 + c) % 28 + 1;
        const dateStr = `2026-08-${day < 10 ? '0' : ''}${day}T12:00:00Z`;

        const incProps: Property[] = [
          { id: `p_${incId}_1`, type: "UPI", raw_value: upi, normalized_value: upi, confidence: 0.99, source: "SYNTHETIC" },
          { id: `p_${incId}_2`, type: "PHONE", raw_value: phone, normalized_value: phone, confidence: 0.99, source: "SYNTHETIC" },
          { id: `p_${incId}_3`, type: "LOCATION", raw_value: loc, normalized_value: loc, confidence: 0.90, source: "SYNTHETIC" }
        ];

        if (i % 2 === 0) {
          incProps.push({ id: `p_${incId}_4`, type: "URL", raw_value: `http://${url}`, normalized_value: url, confidence: 0.95, source: "SYNTHETIC" });
        }

        const inc: Incident = {
          id: incId,
          description: `Cyber fraud complaint regarding unauthorized digital payment debit via suspicious handle ${upi}.`,
          timestamp: dateStr,
          source: "SYNTHETIC",
          category: ["BANKING_FRAUD", "LOTTERY_SCAM", "JOB_FRAUD", "INVESTMENT_SCAM", "IDENTITY_THEFT"][i % 5],
          location: loc,
          properties: incProps
        };
        this.addIncidentToGraph(inc);
      }
    }
  }

  public addIncidentToGraph(inc: Incident) {
    this.incidents.set(inc.id, inc);

    // Incident Node
    const incNodeId = inc.id;
    if (!this.graphNodes.has(incNodeId)) {
      this.graphNodes.set(incNodeId, {
        id: incNodeId,
        label: "Incident",
        type: "Incident",
        properties: {
          id: inc.id,
          description: inc.description,
          timestamp: inc.timestamp,
          category: inc.category,
          location: inc.location
        }
      });
    }

    // Property Nodes & Edges
    inc.properties.forEach(p => {
      const propNodeId = `${p.type}:${p.normalized_value}`;
      if (!this.graphNodes.has(propNodeId)) {
        this.graphNodes.set(propNodeId, {
          id: propNodeId,
          label: p.type,
          type: p.type,
          properties: {
            raw_value: p.raw_value,
            normalized_value: p.normalized_value,
            type: p.type
          }
        });
      }

      // Edge
      const relType = `HAS_${p.type}`;
      const edgeKey = `${incNodeId}->${propNodeId}`;
      if (!this.graphEdges.has(edgeKey)) {
        this.graphEdges.add(edgeKey);
        this.edgesList.push({
          id: edgeKey,
          source: incNodeId,
          target: propNodeId,
          rel_type: relType
        });
      }
    });
  }

  public processEvidenceUpload(file: File, description: string, location: string): Promise<Incident> {
    return new Promise((resolve) => {
      const nextNum = this.incidents.size + 1;
      const incId = `INC${nextNum < 100 ? '0' : ''}${nextNum < 10 ? '0' : ''}${nextNum}`;
      
      // OCR Text Extraction Simulation / Regex Detection
      const mockOcrText = `
Your payment of ₹800 was successful.
UPI ID: scammer123@upi
Transaction ID: TXN9001
Contact: 9876543210
Location: ${location || "Kochi"}
Website: http://fakebank.example/login
      `.trim();

      const extractedProps: Property[] = [
        { id: `pr_${Date.now()}_1`, type: "UPI", raw_value: "scammer123@upi", normalized_value: "scammer123@upi", confidence: 0.99, source: "OCR" },
        { id: `pr_${Date.now()}_2`, type: "PHONE", raw_value: "9876543210", normalized_value: "9876543210", confidence: 0.99, source: "OCR" },
        { id: `pr_${Date.now()}_3`, type: "TRANSACTION_ID", raw_value: "TXN9001", normalized_value: "TXN9001", confidence: 0.99, source: "OCR" },
        { id: `pr_${Date.now()}_4`, type: "URL", raw_value: "http://fakebank.example/login", normalized_value: "fakebank.example", confidence: 0.95, source: "OCR" },
        { id: `pr_${Date.now()}_5`, type: "LOCATION", raw_value: location || "Kochi", normalized_value: location || "Kochi", confidence: 0.92, source: "OCR" },
        { id: `pr_${Date.now()}_6`, type: "AMOUNT", raw_value: "₹800", normalized_value: "800", confidence: 0.99, source: "OCR" }
      ];

      const newInc: Incident = {
        id: incId,
        description: description || "Reported cybercrime evidence screenshot.",
        timestamp: new Date().toISOString(),
        source: "CITIZEN_REPORT",
        category: "CYBER_FRAUD",
        location: location || "Kochi",
        ocr_text: mockOcrText,
        evidence_filename: file.name,
        properties: extractedProps
      };

      this.addIncidentToGraph(newInc);
      resolve(newInc);
    });
  }

  public getIncident(id: string): Incident | undefined {
    return this.incidents.get(id);
  }

  public getAllIncidents(): Incident[] {
    return Array.from(this.incidents.values());
  }

  public getIncidentGraph(incidentId: string): GraphData {
    const subNodes = new Set<string>();
    const subEdges: GraphEdge[] = [];

    if (this.graphNodes.has(incidentId)) {
      subNodes.add(incidentId);
    }

    const connectedPropIds = new Set<string>();
    this.edgesList.forEach(e => {
      if (e.source === incidentId) {
        subEdges.push(e);
        connectedPropIds.add(e.target);
      }
    });

    connectedPropIds.forEach(propId => {
      subNodes.add(propId);
      this.edgesList.forEach(e => {
        if (e.target === propId) {
          subNodes.add(e.source);
          if (!subEdges.includes(e)) {
            subEdges.push(e);
          }
        }
      });
    });

    const nodesList = Array.from(subNodes)
      .map(id => this.graphNodes.get(id))
      .filter((n): n is GraphNode => n !== undefined);

    return { nodes: nodesList, edges: subEdges };
  }

  public getGlobalGraph(limitIncidents = 30): GraphData {
    const incs = Array.from(this.incidents.values()).slice(0, limitIncidents);
    const incIds = new Set(incs.map(i => i.id));
    const subNodes = new Set<string>(incIds);
    const subEdges: GraphEdge[] = [];

    this.edgesList.forEach(e => {
      if (incIds.has(e.source)) {
        subNodes.add(e.target);
        subEdges.push(e);
      }
    });

    const nodesList = Array.from(subNodes)
      .map(id => this.graphNodes.get(id))
      .filter((n): n is GraphNode => n !== undefined);

    return { nodes: nodesList, edges: subEdges };
  }

  public getDashboardStats() {
    const total = this.incidents.size;
    const propMap = new Map<string, number>();

    this.edgesList.forEach(e => {
      propMap.set(e.target, (propMap.get(e.target) || 0) + 1);
    });

    const mostConnected = Array.from(propMap.entries())
      .map(([propId, count]) => {
        const node = this.graphNodes.get(propId);
        return {
          id: propId,
          type: node?.type || "PROPERTY",
          value: node?.properties.normalized_value || propId,
          count
        };
      })
      .sort((a, b) => b.count - a.count)
      .slice(0, 8);

    const recents = Array.from(this.incidents.values())
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, 8);

    return {
      total_incidents: total,
      unique_properties: this.graphNodes.size - total,
      connected_clusters: 10,
      new_incidents: 14,
      most_connected_properties: mostConnected,
      recent_incidents: recents
    };
  }

  public getPropertyStats(propId: string) {
    const connectedIncidents: Incident[] = [];
    const connectedPhones = new Set<string>();
    const connectedUrls = new Set<string>();
    const connectedLocations = new Set<string>();

    const targetPropNode = this.graphNodes.get(propId);
    if (!targetPropNode) return null;

    // Find incidents linked to this property
    const linkedIncIds = this.edgesList
      .filter(e => e.target === propId)
      .map(e => e.source);

    linkedIncIds.forEach(incId => {
      const inc = this.incidents.get(incId);
      if (inc) {
        connectedIncidents.push(inc);
        inc.properties.forEach(p => {
          if (p.type === "PHONE") connectedPhones.add(p.normalized_value);
          if (p.type === "URL") connectedUrls.add(p.normalized_value);
          if (p.type === "LOCATION") connectedLocations.add(p.normalized_value);
        });
      }
    });

    const timestamps = connectedIncidents.map(i => new Date(i.timestamp).getTime());
    const minDate = timestamps.length ? new Date(Math.min(...timestamps)).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : "N/A";
    const maxDate = timestamps.length ? new Date(Math.max(...timestamps)).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : "N/A";

    return {
      node: targetPropNode,
      connectedIncidentsCount: connectedIncidents.length,
      connectedIncidents,
      connectedPhonesCount: connectedPhones.size,
      connectedUrlsCount: connectedUrls.size,
      connectedLocationsCount: connectedLocations.size,
      firstObserved: minDate,
      lastObserved: maxDate
    };
  }
}

export const cyberEngine = new CyberSaarthiEngine();
