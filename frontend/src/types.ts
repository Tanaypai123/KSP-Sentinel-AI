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
  photoSeed: string; // to generate consistent UI placeholder avatars
  status: 'At Large' | 'In Custody' | 'Under Trial' | 'Released';
  riskScore: number; // 0-100
  biometricsMatch: number; // percentage match
  primaryOffense: string;
  notes: string;
  networkConnections: string[]; // names of other people or entities
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
  confidence: number; // 0-100
  tags: string[];
}

export interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  isStreaming?: boolean;
  structuredAnswer?: {
    summary: string;
    timeline?: { time: string; event: string; status: string }[];
    entities?: { name: string; type: string; details: string; risk: 'High' | 'Medium' | 'Low' }[];
    recommendedActions?: string[];
    jsonPayload?: string;
  };
}
