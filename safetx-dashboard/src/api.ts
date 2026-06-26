// File: src/api.ts
// Cliente de API centralizado. Antes, cada componente fazia fetch direto
// para "http://localhost:8000" hardcoded e sem nenhum header de autenticação
// — agora a URL vem de uma env var e o token JWT é injetado automaticamente.

export const API_BASE_URL: string =
  (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";

const TOKEN_KEY = "safetx_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof URLSearchParams)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // resposta sem corpo JSON, mantém a mensagem padrão
    }
    throw new ApiError(detail, response.status);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

// === Auth ===
export async function login(username: string, password: string): Promise<string> {
  const body = new URLSearchParams({ username, password });
  const data = await request<{ access_token: string }>("/token", {
    method: "POST",
    body,
  });
  setToken(data.access_token);
  return data.access_token;
}

export async function register(username: string, email: string, password: string): Promise<void> {
  await request("/register", {
    method: "POST",
    body: JSON.stringify({ username, email, password }),
  });
}

// === Transações ===
export interface TransactionInput {
  sender: string;
  recipient: string;
  amount_eth: number;
}

export type RiskLevel = "safe" | "suspicious" | "high-risk";

export function analyzeTransaction(tx: TransactionInput): Promise<RiskLevel> {
  return request<RiskLevel>("/analyze", {
    method: "POST",
    body: JSON.stringify(tx),
  });
}

export interface Transaction {
  id: number;
  sender: string;
  recipient: string;
  amount_eth: number;
  risk: string;
  timestamp: string;
}

export interface HistoryPage {
  items: Transaction[];
  page: number;
  limit: number;
  total: number;
  total_pages: number;
}

export function getHistory(page: number, limit = 10): Promise<HistoryPage> {
  return request<HistoryPage>(`/history?page=${page}&limit=${limit}`);
}

export interface ReclassificationInput {
  new_risk: RiskLevel;
  reason: string;
}

export function reclassify(txId: number, payload: ReclassificationInput): Promise<{ status: string; tx_id: number }> {
  return request(`/reclassify/${txId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export interface ReclassificationLog {
  id: number;
  tx_id: number;
  old_risk: string;
  new_risk: string;
  reason: string;
  reclassified_by: string;
}

export function getReclassifications(): Promise<ReclassificationLog[]> {
  return request<ReclassificationLog[]>("/reclassifications");
}
