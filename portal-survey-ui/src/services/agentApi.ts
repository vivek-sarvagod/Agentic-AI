// services/agentApi.ts
// ---------------------
// All HTTP calls to portal-survey-agent live here.
// Import { sendAgentMessage } in your page components — never use fetch directly.

import type { AgentRequest, AgentResponse } from '../types/agent';

// Change this to your agent service URL.
// Vite: set VITE_AGENT_URL in .env  →  import.meta.env.VITE_AGENT_URL
// CRA:  set REACT_APP_AGENT_URL     →  process.env.REACT_APP_AGENT_URL
const AGENT_BASE_URL =
  (import.meta as any).env?.VITE_AGENT_BASE_URL ??
  // (process.env as any).REACT_APP_AGENT_BASE_URL ??
  // Use localhost for dev, agent NodePort for production
  (window.location.hostname === 'localhost' 
    ? 'http://localhost:8001' 
    : 'http://3.228.119.194:30083');  // Agent service NodePort

export async function sendAgentMessage(
  message: string,
  sessionId?: string,
): Promise<AgentResponse> {
  const body: AgentRequest = { message, session_id: sessionId };

  const res = await fetch(`${AGENT_BASE_URL}/agent/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Agent error ${res.status}: ${text}`);
  }

  return res.json() as Promise<AgentResponse>;
}

// const AGENT_BASE_URL = import.meta.env.VITE_AGENT_BASE_URL ?? '/agent-api';

// export interface AgentMessage {
//   role: 'user' | 'assistant';
//   content: string;
//   requiresConfirmation?: boolean;
// }

// export interface AgentResponse {
//   session_id: string;
//   response: string;
//   intent: string;
//   requires_confirmation: boolean;
//   pending_action?: string;
//   data: Record<string, unknown>;
// }

// export async function sendAgentMessage(
//   message: string,
//   sessionId?: string
// ): Promise<AgentResponse> {
//   const response = await fetch(`${AGENT_BASE_URL}/agent/query`, {
//     method: 'POST',
//     headers: { 'Content-Type': 'application/json' },
//     body: JSON.stringify({ message, session_id: sessionId }),
//   });

//   if (!response.ok) {
//     const body = await response.text();
//     throw new Error(body || `Agent request failed with status ${response.status}`);
//   }

//   return response.json() as Promise<AgentResponse>;
// }
