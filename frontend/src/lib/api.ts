const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const token = typeof window !== "undefined" ? localStorage.getItem("cybersaarthi_token") : null;
  const headers: Record<string, string> = { ...(options.headers as Record<string, string> || {}) };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}/api/v1${endpoint}`, { ...options, headers });
  if (!res.ok) { const errorData = await res.json().catch(() => ({})); throw new Error(errorData.detail || `API Request failed with status ${res.status}`); }
  return res.json();
}
export async function submitCitizenReport(formData: FormData) { return fetchApi("/incidents/submit-full", { method: "POST", body: formData }); }
export async function loginUser(username: string, password: string) { return fetchApi("/auth/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username, password }) }); }
export async function getDashboardStats() { return fetchApi("/investigator/dashboard"); }
export async function getIncidentDetails(id: string) { return fetchApi(`/incidents/${encodeURIComponent(id)}`); }
export async function getIncidentGraph(id: string) { return fetchApi(`/graph/incident/${encodeURIComponent(id)}`); }
export async function searchEntities(query: string) { return fetchApi(`/entities/search?query=${encodeURIComponent(query)}`); }
export async function getClusters() { return fetchApi("/investigator/clusters"); }
export async function getIncidents(params: Record<string, string | number | undefined> = {}) { const qs = new URLSearchParams(); Object.entries(params).forEach(([k,v]) => { if (v !== undefined && v !== "") qs.set(k,String(v)); }); return fetchApi(`/investigator/incidents${qs.toString()?`?${qs}`:""}`); }
export async function getFilteredGraph(params: Record<string, string | number | string[] | undefined> = {}) { const qs = new URLSearchParams(); Object.entries(params).forEach(([k,v]) => { if (v===undefined || v==="") return; if (Array.isArray(v)) v.forEach(x=>qs.append(k,x)); else qs.set(k,String(v)); }); return fetchApi(`/graph/filter${qs.toString()?`?${qs}`:""}`); }
