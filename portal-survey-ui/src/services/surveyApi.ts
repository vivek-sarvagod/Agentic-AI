// const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
const BASE_URL =
  (import.meta as any).env?.VITE_API_BASE_URL ??
  // (process.env as any).REACT_APP_AGENT_BASE_URL ??
  // Use localhost for dev, agent NodePort for production
  (window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : 'http://3.228.119.194:30082');  // Agent service NodePort

// ── Frontend model (camelCase) ────────────────────────────────────────────
// Matches what the form and components use internally.

export interface SurveyData {
  firstName: string;
  lastName: string;
  streetAddress: string;
  city: string;
  state: string;
  zip: string;
  telephone: string;
  email: string;
  surveyDate: string;
  campusLikes: string[];
  interestSource: string;
  recommendation: string;
  raffle?: string;
  comments?: string;
}

export interface Survey extends SurveyData {
  id: number;
}

// ── Backend schema types (snake_case, matches OpenAPI spec) ───────────────
// POST /api/surveys  →  SurveyCreateRequest (all required)
// PUT  /api/surveys/{id}  →  SurveyUpdateRequest (all optional / nullable)
// Responses  →  SurveyResponse

interface ApiSurveyCreate {
  first_name: string;
  last_name: string;
  street_address: string;
  city: string;
  state: string;
  zip_code: string;
  telephone: string;
  email: string;
  date_of_survey: string;   // "YYYY-MM-DD"
  liked_most: string[];
  interest_source: string;
  recommendation: string;   // "Very Likely" | "Likely" | "Unlikely"
  raffle?: string;          // Optional raffle numbers
  comments?: string;        // Optional comments
}

// PUT accepts the same shape but every field is nullable/optional
type ApiSurveyUpdate = Partial<ApiSurveyCreate>;

interface ApiSurveyResponse {
  id: number;
  first_name: string;
  last_name: string;
  street_address: string;
  city: string;
  state: string;
  zip_code: string;
  telephone: string;
  email: string;
  date_of_survey: string;
  liked_most: string[];
  interest_source: string;
  recommendation: string;
  raffle?: string;
  comments?: string;
}

// GET /api/surveys returns { total, surveys }
interface ApiSurveyListResponse {
  total: number;
  surveys: ApiSurveyResponse[];
}

// DELETE /api/surveys/{id} returns { message }
interface ApiMessageResponse {
  message: string;
}

// ── Recommendation value maps ─────────────────────────────────────────────

const RECOMMENDATION_TO_API: Record<string, string> = {
  veryLikely: 'Very Likely',
  likely: 'Likely',
  unlikely: 'Unlikely',
};

const RECOMMENDATION_FROM_API: Record<string, string> = {
  'Very Likely': 'veryLikely',
  Likely: 'likely',
  Unlikely: 'unlikely',
};

// ── Transforms ────────────────────────────────────────────────────────────

function toApiCreate(data: SurveyData): ApiSurveyCreate {
  return {
    first_name: data.firstName,
    last_name: data.lastName,
    street_address: data.streetAddress,
    city: data.city,
    state: data.state,
    zip_code: data.zip,
    telephone: data.telephone,
    email: data.email,
    date_of_survey: data.surveyDate,
    liked_most: data.campusLikes,
    interest_source: data.interestSource,
    recommendation: RECOMMENDATION_TO_API[data.recommendation] ?? data.recommendation,
    raffle: data.raffle || undefined,
    comments: data.comments || undefined,
  };
}

// PUT uses the same field mapping; cast to Partial for the update endpoint
function toApiUpdate(data: SurveyData): ApiSurveyUpdate {
  return toApiCreate(data);
}

function fromApiResponse(raw: ApiSurveyResponse): Survey {
  return {
    id: raw.id,
    firstName: raw.first_name,
    lastName: raw.last_name,
    streetAddress: raw.street_address,
    city: raw.city,
    state: raw.state,
    zip: raw.zip_code,
    telephone: raw.telephone,
    email: raw.email,
    surveyDate: raw.date_of_survey,
    campusLikes: raw.liked_most,
    interestSource: raw.interest_source,
    recommendation: RECOMMENDATION_FROM_API[raw.recommendation] ?? raw.recommendation,
    raffle: raw.raffle || '',
    comments: raw.comments || '',
  };
}

// ── HTTP helper ───────────────────────────────────────────────────────────

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Request failed with status ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// ── API surface ───────────────────────────────────────────────────────────

export const surveyApi = {
  /** GET /api/surveys → { total, surveys: [...] } */
  getAll: (): Promise<Survey[]> =>
    fetch(`${BASE_URL}/api/surveys`)
      .then((res) => handleResponse<ApiSurveyListResponse>(res))
      .then((data) => data.surveys.map(fromApiResponse)),

  /** POST /api/surveys → SurveyResponse (201) */
  create: (data: SurveyData): Promise<Survey> =>
    fetch(`${BASE_URL}/api/surveys`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(toApiCreate(data)),
    })
      .then((res) => handleResponse<ApiSurveyResponse>(res))
      .then(fromApiResponse),

  /** PUT /api/surveys/{id} → SurveyResponse (200) */
  update: (id: number, data: SurveyData): Promise<Survey> =>
    fetch(`${BASE_URL}/api/surveys/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(toApiUpdate(data)),
    })
      .then((res) => handleResponse<ApiSurveyResponse>(res))
      .then(fromApiResponse),

  /** DELETE /api/surveys/{id} → { message } (200) */
  remove: (id: number): Promise<string> =>
    fetch(`${BASE_URL}/api/surveys/${id}`, { method: 'DELETE' })
      .then((res) => handleResponse<ApiMessageResponse>(res))
      .then((data) => data.message),
};
