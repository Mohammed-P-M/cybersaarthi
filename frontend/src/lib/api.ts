const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const token = typeof window !== "undefined" ? localStorage.getItem("cybersaarthi_token") : null;
  
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `API Request failed with status ${res.status}`);
  }

  return res.json();
}

export async function submitCitizenReport(formData: FormData) {
  const res = await fetch(`${API_BASE}/incidents/submit-full`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to submit report");
  }
  return res.json();
}

export async function loginUser(username: string, password: str) {
  return fetchApi("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
}

export async function getDashboardStats() {
  return fetchApi("/investigator/dashboard");
}

export async function getIncidentDetails(id: string) {
  return fetchApi(`/incidents/${id}`);
}

export async function getIncidentGraph(id: string) {
  return fetchApi(`/graph/incident/${id}`);
}

export async function getEntityDetails(type: string, value: string) {
  return fetchApi(`/entities/${encodeURIComponent(type)}/${encodeURIComponent(value)}`);
}

export async function searchEntities(query: string) {
  return fetchApi(`/entities/search?query=${encodeURIComponent(query)}`);
}

export async function getClusters() {
  return fetchApi("/investigator/clusters");
}
