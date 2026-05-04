// types/agent.ts
// ---------------
// TypeScript interfaces that mirror the Python AgentResponse model.
// If you add a field to models.py, add it here too.

export interface AgentRequest {
  message: string;
  session_id?: string;
}

// A single chart series for the analytics bar chart
export interface ChartDataPoint {
  label: string;
  value: number;
}

export interface ChartData {
  type: 'bar';
  title: string;
  data: ChartDataPoint[];
}

// Google Maps info passed when campus_info agent ran
export interface MapData {
  lat: number;
  lng: number;
  label: string;
  address: string;
  embed_url: string;
  maps_link: string;
}

// Fact chip: "Founded · 1972"
export interface Chip {
  label: string;
  value: string;
}

// Clickable site card below campus info
export interface LinkCard {
  title: string;
  url: string;
  description: string;
  admissions_url?: string;
}

// All optional display overrides the agent can return
export interface UiHints {
  show_map?: boolean;
  map?: MapData;
  show_info_chips?: boolean;
  chips?: Chip[];
  show_link_card?: boolean;
  link_card?: LinkCard;
  show_charts?: boolean;
  charts?: ChartData[];
}

// A suggestion button shown below a bubble
export interface QuickAction {
  label: string;
  prompt: string;
}

// Full response from POST /agent/query
export interface AgentResponse {
  session_id: string;
  response: string;
  intent: string;
  requires_confirmation: boolean;
  pending_action: string | null;
  agent_tags: string[];
  ui_hints: UiHints;
  quick_actions: QuickAction[];
  data: Record<string, unknown>;
}

// A single message in the chat transcript
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  agent_tags?: string[];
  ui_hints?: UiHints;
  quick_actions?: QuickAction[];
  requires_confirmation?: boolean;
}