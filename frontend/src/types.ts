export interface FIR {
  id: string;
  caseNumber: string;
  title: string;
  underSection: string; // e.g. "IPC Section 302" or "BNS Section 103"
  status: 'Investigation' | 'Open' | 'Closed' | 'Under Review';
  dateRegistered: string;
  complainant: string;
  details: string;
  summary: string;
  officersAssigned: string[];
  location: string;
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
}

export interface Accused {
  id: string;
  name: string;
  age: number;
  photoSeed: string;
  status: 'At Large' | 'In Custody' | 'Under Trial' | 'Released';
  riskScore: number;
  biometricsMatch: number;
  primaryOffense: string;
  notes: string;
  networkConnections: string[];
  lastKnownLocation: string;
  phoneNumbers: string[];
  associates: string[];
}

export interface Notification {
  id: string;
  text: string;
  time: string;
  severity: 'critical' | 'warning' | 'info';
  unread: boolean;
}

export interface Alert {
  id: string;
  type: 'CRITICAL' | 'WARNING' | 'INFO';
  text: string;
  timestamp: string;
  location?: string;
}

export interface CourtHearing {
  id: string;
  caseNumber: string;
  accusedName: string;
  courtName: string;
  hearingDate: string;
  bench: string;
  status: 'Scheduled' | 'Adjourned' | 'Completed';
}

export interface AIInsight {
  id: string;
  title: string;
  description: string;
  confidence: number;
  tags: string[];
}

// ---------------------------------------------------------------------------
// Backend API types  (POST /api/v1/chat/query)
// ---------------------------------------------------------------------------

export type BackendIntent =
  | 'SEARCH_CASES'
  | 'SEARCH_ACCUSED'
  | 'SEARCH_VICTIMS'
  | 'AGGREGATE_COUNT'
  | 'CRIME_TREND'
  | 'HOTSPOT'
  | 'PREDICT_CRIME'
  | 'REPORTS'
  | 'FIR_LOOKUP'
  | 'MOST_WANTED'
  | 'REPEAT_OFFENDERS';

export interface PredictionResult {
  predicted_cases: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'UNKNOWN';
  confidence: number;
  trend: string;
  reasoning: string;
  historical_counts: { year: number; month: number; count: number }[];
  forecast_month: string;
  model_used: string;
  data_points_used: number;
}

export interface BackendResponse {
  success: boolean;
  query: string;
  intent: BackendIntent;
  entities: Record<string, any>;
  summary?: string | null;
  count?: number;
  results?: Record<string, any>[];
  prediction?: PredictionResult;
  insights?: string[];
  recommended_queries?: string[];
  explanation?: {
    intent: string;
    entities: Record<string, any>;
    reasoning: string;
    filters: string[];
    sql_summary: string;
    algorithm?: string;
    confidence?: number;
    trend_direction?: string;
    risk_level?: string;
    historical_data_used?: string;
  };
  metadata?: {
    query: string;
    confidence?: number;
    raw_results_count?: number;
    query_time_ms: number;
    cache_hit: boolean;
    rows_scanned?: number;
    rows_returned?: number;
    trend_analytics?: {
      growth_percentage: number;
      moving_average: number;
      highest_month: string;
      lowest_month: string;
      peak_month: string;
      declining_trend: boolean;
      stable_trend: boolean;
    };
  };
  error?: string;
}

// ---------------------------------------------------------------------------
// Chat message type (used in AIWorkspace)
// ---------------------------------------------------------------------------

export interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  isStreaming?: boolean;
  isKannada?: boolean;
  // Legacy structured answer (mock data)
  structuredAnswer?: {
    summary: string;
    timeline?: { time: string; event: string; status: string }[];
    entities?: { name: string; type: string; details: string; risk: 'High' | 'Medium' | 'Low' }[];
    recommendedActions?: string[];
    jsonPayload?: string;
  };
  // Real backend response (set when query hits the live API)
  backendPayload?: BackendResponse;
}
