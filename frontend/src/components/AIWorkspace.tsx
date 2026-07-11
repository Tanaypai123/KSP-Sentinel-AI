import { useState, useRef, useEffect, memo, Fragment, createContext, useContext } from 'react';
import { jsPDF } from 'jspdf';
import { detectKannada, translateToEnglish, translateToKannada } from '../services/translationService';
import {
  Send,
  Sparkles,
  RefreshCw,
  Paperclip,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  BarChart3,
  MapPin,
  Users,
  ChevronLeft,
  ChevronRight,
  Shield,
  Clock,
  Compass,
  Download,
  Database,
  Search,
  Activity,
  Mic,
  MicOff,
  Maximize,
  Minimize,
  FileText,
  User,
  ChevronDown,
  ChevronUp,
  CheckCheck,
  Calendar,
  Filter,
  Info,
  X
} from 'lucide-react';
import type { Message, BackendResponse, PredictionResult } from '../types';
import { sendChatMessage } from '../services/chatService';
import api from '../services/api';
import { t } from '../services/i18n';
import { ErrorBoundary } from './ErrorBoundary';

// ---------------------------------------------------------------------------
// Language Context
// ---------------------------------------------------------------------------
const LangContext = createContext<'en' | 'kn'>('en');

// ---------------------------------------------------------------------------
// Static query pills defined in module scope
// ---------------------------------------------------------------------------
const suggestedQueries = {
  crimeSearch: ['Show theft in Mysuru', 'Show murder in Bengaluru Urban'],
  analytics: ['Crime trend in Bengaluru Urban', 'Count assault cases'],
  prediction: ['Predict theft next month in Mysuru'],
  hotspots: ['Top hotspots'],
};

// ---------------------------------------------------------------------------
// A. Simulated Streaming Text Component (Character-by-Character)
// ---------------------------------------------------------------------------
interface StreamedTextProps {
  text: string;
  speed?: number;
  onComplete?: () => void;
  onUpdate?: () => void;
}

export function StreamedText({ text, speed = 8, onComplete, onUpdate }: StreamedTextProps) {
  const [displayedText, setDisplayedText] = useState('');
  
  // Defensively ensure text is a string
  const safeText = typeof text === 'string' ? text : (text ? JSON.stringify(text) : '');

  useEffect(() => {
    let index = 0;
    let rafId: number;
    const interval = setInterval(() => {
      setDisplayedText((prev) => prev + safeText.charAt(index));
      index++;
      rafId = requestAnimationFrame(() => {
        onUpdate?.();
      });
      if (index >= safeText.length) {
        clearInterval(interval);
        cancelAnimationFrame(rafId);
        onComplete?.();
      }
    }, speed);

    return () => {
      clearInterval(interval);
      cancelAnimationFrame(rafId);
    };
  }, [safeText, speed, onComplete, onUpdate]);

  return <span className="font-sans text-sm md:text-base leading-relaxed text-neutral-250 whitespace-pre-wrap">{displayedText}</span>;
}

// ---------------------------------------------------------------------------
// B. Dynamic Staged Status Loader
// ---------------------------------------------------------------------------
function SequencedStatusLoader({ stage = 0 }: { stage?: number }) {

  const stages = [
    "Analyzing natural language query parameters...",
    "Compiling parameterized SQL & executing database search...",
    "Formatting records & computing analytics pipelines..."
  ];

  return (
    <div className="mr-auto items-start max-w-[80%] flex flex-col space-y-2 animate-pulse font-mono">
      <span className="text-xs font-mono text-cyan-405 font-bold uppercase tracking-wider animate-pulse">
        {stage === 0 ? "➔ Parsing Query" : stage === 1 ? "➔ Running Database Scan" : "➔ Model Computation"}
      </span>
      <div className="p-4 bg-neutral-905 border border-neutral-800 rounded-xl rounded-tl-none space-y-3 w-80 shadow-lg">
        <div className="flex items-center space-x-2.5">
          <span className="w-2.5 h-2.5 rounded-full bg-cyan-500 animate-ping" />
          <span className="text-xs font-semibold text-neutral-300">{stages[stage]}</span>
        </div>
        <div className="h-1.5 w-full bg-neutral-950 rounded-full overflow-hidden">
          <div 
            className="h-full bg-cyan-500 rounded-full transition-all duration-700"
            style={{ width: stage === 0 ? "30%" : stage === 1 ? "70%" : "95%" }}
          />
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 1. CasesTable (SEARCH_CASES / SEARCH_VICTIMS) with Pagination & Sorting
// ---------------------------------------------------------------------------
function CasesTableRaw({ records }: { records: Record<string, any>[] }) {
  const [currentPage, setCurrentPage] = useState(1);
  const [sortField, setSortField] = useState('crime_registered_date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [expandedRow, setExpandedRow] = useState<number | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const pageSize = 5;

  const lang = useContext(LangContext);
  if (!Array.isArray(records) || records.length === 0) {
    return (
      <div className="p-8 text-center border border-neutral-800 rounded-xl bg-neutral-950/40">
        <Database className="w-8 h-8 text-neutral-500 mx-auto mb-2" />
        <p className="text-sm text-neutral-450 font-mono">{t('No cases matched database query filters.', lang)}</p>
      </div>
    );
  }

  // Filter rows
  const statusLabels: Record<number, string> = {
    1: 'Investigation',
    2: 'Under Trial',
    3: 'Closed',
    4: 'Under Review',
  };

  const filtered = records.filter((r) => {
    if (filterStatus === 'ALL') return true;
    const label = statusLabels[r?.status] || 'Unknown';
    return label === filterStatus;
  });

  // Sort rows
  const parseDate = (d: string) => {
    if (!d) return 0;
    const parts = d.split(/[-/]/);
    if (parts.length === 3 && parts[0].length === 2 && parts[2].length === 4) {
      return new Date(`${parts[2]}-${parts[1]}-${parts[0]}`).getTime();
    }
    return new Date(d).getTime() || 0;
  };

  const sorted = [...filtered].sort((a, b) => {
    const valA = a[sortField] ?? '';
    const valB = b[sortField] ?? '';
    
    if (sortField.includes('date')) {
      const dateA = parseDate(valA as string);
      const dateB = parseDate(valB as string);
      if (dateA < dateB) return sortOrder === 'asc' ? -1 : 1;
      if (dateA > dateB) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    }

    if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
    if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
    return 0;
  });

  // Paginate
  const totalPages = Math.ceil(sorted.length / pageSize) || 1;
  const startIndex = (currentPage - 1) * pageSize;
  const pageRows = sorted.slice(startIndex, startIndex + pageSize);

  const toggleSort = (field: string) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
    setCurrentPage(1);
  };

  const exportCSV = () => {
    if (!Array.isArray(records) || records.length === 0) return;
    const headers = ['CrimeNo', 'CaseNo', 'RegisteredDate', 'Status', 'Facts'];
    const rows = records.map((r) => [
      r?.crime_no || '',
      r?.case_no || '',
      r?.crime_registered_date || '',
      statusLabels[r?.status] || 'Unknown',
      (r?.brief_facts || '').replace(/"/g, '""'),
    ]);
    const csvContent =
      [headers.join(','), ...rows.map((e) => e.map((x) => `"${x}"`).join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `fir_cases_export_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4">
      {/* Table Header Filter controls */}
      <div className="flex items-center justify-between text-xs font-mono">
        <div className="flex items-center space-x-2">
          <span className="text-neutral-450 uppercase">Filter Status:</span>
          <select
            value={filterStatus}
            onChange={(e) => {
              setFilterStatus(e.target.value);
              setCurrentPage(1);
            }}
            className="bg-neutral-900 border border-neutral-800 text-xs font-mono text-neutral-200 rounded-lg px-3 py-1 focus:outline-none focus:border-cyan-500 cursor-pointer"
          >
            <option value="ALL">All Statuses</option>
            <option value="Investigation">Investigation</option>
            <option value="Under Trial">Under Trial</option>
            <option value="Closed">Closed</option>
            <option value="Under Review">Under Review</option>
          </select>
        </div>
        <button
          onClick={exportCSV}
          className="px-3 py-1 border border-neutral-800 rounded-lg text-xs font-mono hover:bg-neutral-900 text-neutral-350 hover:text-white flex items-center space-x-1.5 transition cursor-pointer"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Export CSV</span>
        </button>
      </div>

      <div className="rounded-xl border border-neutral-800 bg-neutral-950/20 overflow-hidden shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs md:text-sm font-mono">
            <thead>
              <tr className="border-b border-neutral-800 bg-neutral-900/40 text-neutral-400">
                <th
                  onClick={() => toggleSort('crime_no')}
                  className="px-4 py-3 cursor-pointer hover:text-white transition select-none"
                >
                  Crime No {sortField === 'crime_no' && (sortOrder === 'asc' ? '▲' : '▼')}
                </th>
                <th className="px-4 py-3">Case No</th>
                <th
                  onClick={() => toggleSort('crime_registered_date')}
                  className="px-4 py-3 cursor-pointer hover:text-white transition select-none"
                >
                  Date {sortField === 'crime_registered_date' && (sortOrder === 'asc' ? '▲' : '▼')}
                </th>
                <th className="px-4 py-3 text-center">Status</th>
                <th className="px-4 py-3 text-center">Details</th>
              </tr>
            </thead>
            <tbody>
              {pageRows.map((row, idx) => {
                const globalIdx = startIndex + idx;
                const dateStr = row.crime_registered_date || '—';
                const label = statusLabels[row.status] || 'Unknown';
                const isExpanded = expandedRow === globalIdx;

                const badgeColors: Record<string, string> = {
                  Investigation: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
                  'Under Trial': 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
                  Closed: 'bg-emerald-500/10 text-emerald-450 border-emerald-500/20',
                  'Under Review': 'bg-purple-500/10 text-purple-400 border-purple-500/20',
                };

                return (
                  <Fragment key={globalIdx}>
                    <tr className="border-b border-neutral-900 hover:bg-neutral-900/20 transition duration-150">
                      <td className="px-4 py-3.5 font-semibold text-neutral-200">{row.crime_no}</td>
                      <td className="px-4 py-3.5 text-neutral-350">{row.case_no}</td>
                      <td className="px-4 py-3.5 text-neutral-400">{dateStr}</td>
                      <td className="px-4 py-3.5 text-center">
                        <span
                          className={`text-xs font-bold px-2.5 py-1 rounded border ${
                            badgeColors[label] || 'bg-neutral-800 text-neutral-400 border-neutral-700'
                          }`}
                        >
                          {label}
                        </span>
                      </td>
                      <td className="px-4 py-3.5 text-center">
                        <button
                          onClick={() => setExpandedRow(isExpanded ? null : globalIdx)}
                          className="px-2.5 py-1 rounded border border-neutral-800 hover:bg-neutral-900 hover:border-neutral-700 transition text-xs cursor-pointer"
                        >
                          {isExpanded ? 'Hide' : 'View'}
                        </button>
                      </td>
                    </tr>
                    {isExpanded && (
                      <tr className="bg-neutral-950/65">
                        <td colSpan={5} className="px-4 py-4 border-b border-neutral-900 text-sm">
                          {row.fir_summary && (
                            <div className="text-xs font-mono text-cyan-400 font-bold mb-2 uppercase">
                              Summary: {row.fir_summary}
                            </div>
                          )}
                          <div className="text-neutral-350 leading-relaxed font-sans">
                            <span className="font-bold text-neutral-300 font-mono block text-xs uppercase mb-1.5">
                              Statement of Facts:
                            </span>
                            {row.brief_facts || 'No brief facts registered.'}
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Pagination bar */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-neutral-900 bg-neutral-900/10 text-xs">
          <span className="text-neutral-500 font-mono">
            Showing {startIndex + 1} - {Math.min(startIndex + pageSize, sorted.length)} of {sorted.length} records
          </span>
          <div className="flex items-center space-x-1.5">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-1 rounded border border-neutral-850 bg-neutral-950 hover:bg-neutral-900 transition disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-2.5 text-neutral-350 font-bold font-mono">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-1 rounded border border-neutral-850 bg-neutral-950 hover:bg-neutral-900 transition disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 2. FIRLookupDossierRaw (Palantir-style specific FIR dashboard)
// ---------------------------------------------------------------------------
function FIRLookupDossierRaw({ records, onQueryAction }: { records: Record<string, any>[]; onQueryAction?: (q: string) => void }) {
  const [expandedFacts, setExpandedFacts] = useState(false);
  const lang = useContext(LangContext);
  
  if (!Array.isArray(records) || records.length === 0) {
    return (
      <div className="p-8 text-center border border-neutral-800 rounded-xl bg-neutral-950/40">
        <FileText className="w-8 h-8 text-neutral-500 mx-auto mb-2" />
        <p className="text-sm text-neutral-450 font-mono">{t('FIR not found or records empty.', lang)}</p>
      </div>
    );
  }

  const fir = records[0];
  const summaryText = `FIR ${fir?.crime_no || 'Unknown'} was registered on ${fir?.crime_registered_date || 'an unknown date'} at ${fir?.police_station_name || 'an unknown station'}. The case is currently classified as ${fir?.crime_group_name || 'an unknown category'} and status is ${fir?.status_name || 'Not Available'}.`;

  const statusStr = (fir?.status_name || fir?.status || 'Not Available').toString().toUpperCase();
  let statusBadge = 'bg-neutral-800 text-neutral-400 border-neutral-700';
  if (statusStr.includes('OPEN') || statusStr.includes('INVESTIGATION')) statusBadge = 'bg-amber-500/10 text-amber-400 border-amber-500/20';
  if (statusStr.includes('CLOSED')) statusBadge = 'bg-emerald-500/10 text-emerald-450 border-emerald-500/20';
  if (statusStr.includes('PENDING') || statusStr.includes('REVIEW')) statusBadge = 'bg-purple-500/10 text-purple-400 border-purple-500/20';
  if (statusStr.includes('CHARGE SHEET')) statusBadge = 'bg-rose-500/10 text-rose-400 border-rose-500/20';

  const formatVal = (v: any) => v && v !== 'null' && v !== 'Unknown' && v !== 'undefined' ? String(v) : 'Not Available';

  // Extract Mock Victims & Accused safely (simulate if array exists, else empty)
  // The backend might return victims or accused inside the FIR object if it's a deep lookup.
  const victims = Array.isArray(fir?.victims) ? fir.victims : [];
  const accused = Array.isArray(fir?.accused) ? fir.accused : [];

  return (
    <div className="space-y-4 font-sans animate-in fade-in slide-in-from-bottom-2 duration-500 fill-mode-both">
      {/* AI Summary Banner */}
      <div className="p-4 rounded-xl border border-cyan-500/20 bg-gradient-to-r from-cyan-950/20 to-neutral-900/60 shadow-[0_0_15px_rgba(6,182,212,0.05)] flex items-start space-x-3">
        <Sparkles className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5 animate-pulse" />
        <div>
          <span className="block text-[10px] font-mono text-cyan-500 uppercase tracking-wider font-bold mb-1">Intelligence Summary</span>
          <p className="text-sm text-neutral-200 leading-relaxed">{summaryText}</p>
        </div>
      </div>

      {/* Core FIR Information */}
      <div className="rounded-xl border border-neutral-800 bg-neutral-950 overflow-hidden shadow-lg">
        <div className="bg-neutral-900/60 px-4 py-3 border-b border-neutral-800 flex items-center space-x-2">
          <Shield className="w-4 h-4 text-neutral-400" />
          <span className="text-xs font-mono font-bold text-neutral-300 uppercase tracking-wider">FIR Information</span>
        </div>
        <div className="p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-y-4 gap-x-6 text-sm">
          <div>
            <span className="block text-[10px] font-mono text-neutral-500 uppercase">FIR Number</span>
            <span className="font-mono font-bold text-white">{formatVal(fir?.crime_no)}</span>
          </div>
          <div>
            <span className="block text-[10px] font-mono text-neutral-500 uppercase">Case Number</span>
            <span className="font-mono text-neutral-300">{formatVal(fir?.case_no)}</span>
          </div>
          <div>
            <span className="block text-[10px] font-mono text-neutral-500 uppercase">Crime Type</span>
            <span className="text-rose-400 font-bold">{formatVal(fir?.crime_group_name)}</span>
          </div>
          <div>
            <span className="block text-[10px] font-mono text-neutral-500 uppercase">Registration Date</span>
            <span className="text-neutral-300">{formatVal(fir?.crime_registered_date)}</span>
          </div>
          <div>
            <span className="block text-[10px] font-mono text-neutral-500 uppercase">Case Status</span>
            <span className={`inline-block mt-0.5 text-[9px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider ${statusBadge}`}>
              {statusStr}
            </span>
          </div>
          <div>
            <span className="block text-[10px] font-mono text-neutral-500 uppercase">Police Station</span>
            <span className="text-neutral-300">{formatVal(fir?.police_station_name)}</span>
          </div>
          <div>
            <span className="block text-[10px] font-mono text-neutral-500 uppercase">District</span>
            <span className="text-neutral-300">{formatVal(fir?.district_name)}</span>
          </div>
          <div>
            <span className="block text-[10px] font-mono text-neutral-500 uppercase">Investigating Officer</span>
            <span className="text-neutral-300">{formatVal(fir?.io_name)}</span>
          </div>
          <div>
            <span className="block text-[10px] font-mono text-neutral-500 uppercase">Coordinates</span>
            <span className="font-mono text-neutral-400 text-xs">
              Lat: {formatVal(fir?.latitude)}, Lng: {formatVal(fir?.longitude)}
            </span>
          </div>
        </div>
      </div>

      {/* Grid for Accused & Victims */}
      {(accused.length > 0 || victims.length > 0) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {accused.length > 0 && (
            <div className="rounded-xl border border-neutral-800 bg-neutral-950 overflow-hidden shadow-lg">
              <div className="bg-neutral-900/60 px-4 py-3 border-b border-neutral-800 flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-rose-500" />
                <span className="text-xs font-mono font-bold text-neutral-300 uppercase tracking-wider">Accused ({accused.length})</span>
              </div>
              <div className="p-3 space-y-2 max-h-60 overflow-y-auto custom-scrollbar">
                {accused.map((a: any, i: number) => (
                  <div key={i} className="flex items-center space-x-3 p-2 rounded-lg bg-neutral-900/40 border border-neutral-800/50">
                    <div className="w-10 h-10 rounded bg-neutral-800 flex items-center justify-center overflow-hidden flex-shrink-0">
                       <img src={a?.photo || `https://ui-avatars.com/api/?name=${encodeURIComponent(formatVal(a?.name))}&background=random`} alt="Accused" className="w-full h-full object-cover opacity-80" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-bold text-neutral-200 truncate">{formatVal(a?.name)}</div>
                      <div className="text-[10px] font-mono text-neutral-500">
                        {formatVal(a?.age)} yrs • {formatVal(a?.gender)}
                      </div>
                    </div>
                    <span className="text-[9px] font-bold px-2 py-0.5 rounded border border-rose-500/20 bg-rose-500/10 text-rose-400 uppercase tracking-wider whitespace-nowrap">
                      {formatVal(a?.status)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {victims.length > 0 && (
            <div className="rounded-xl border border-neutral-800 bg-neutral-950 overflow-hidden shadow-lg">
              <div className="bg-neutral-900/60 px-4 py-3 border-b border-neutral-800 flex items-center space-x-2">
                <User className="w-4 h-4 text-emerald-500" />
                <span className="text-xs font-mono font-bold text-neutral-300 uppercase tracking-wider">Victims ({victims.length})</span>
              </div>
              <div className="p-3 space-y-2 max-h-60 overflow-y-auto custom-scrollbar">
                {victims.map((v: any, i: number) => (
                  <div key={i} className="flex items-center space-x-3 p-2 rounded-lg bg-neutral-900/40 border border-neutral-800/50">
                    <div className="w-10 h-10 rounded bg-neutral-800 flex items-center justify-center overflow-hidden flex-shrink-0">
                       <img src={v?.photo || `https://ui-avatars.com/api/?name=${encodeURIComponent(formatVal(v?.name))}&background=random`} alt="Victim" className="w-full h-full object-cover opacity-80" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-bold text-neutral-200 truncate">{formatVal(v?.name)}</div>
                      <div className="text-[10px] font-mono text-neutral-500">
                        {formatVal(v?.age)} yrs • {formatVal(v?.gender)}
                      </div>
                    </div>
                    <span className="text-[9px] font-bold px-2 py-0.5 rounded border border-neutral-700 bg-neutral-800 text-neutral-400 uppercase tracking-wider whitespace-nowrap">
                      {formatVal(v?.status)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Brief Facts Accordion */}
      <div className="rounded-xl border border-neutral-800 bg-neutral-950 overflow-hidden shadow-lg">
        <button 
          onClick={() => setExpandedFacts(!expandedFacts)}
          className="w-full bg-neutral-900/60 px-4 py-3 border-b border-neutral-800 flex items-center justify-between cursor-pointer hover:bg-neutral-900/80 transition"
        >
          <div className="flex items-center space-x-2">
            <FileText className="w-4 h-4 text-neutral-400" />
            <span className="text-xs font-mono font-bold text-neutral-300 uppercase tracking-wider">Statement of Facts</span>
          </div>
          {expandedFacts ? <ChevronUp className="w-4 h-4 text-neutral-500" /> : <ChevronDown className="w-4 h-4 text-neutral-500" />}
        </button>
        {expandedFacts && (
          <div className="p-4 bg-neutral-950 text-sm leading-relaxed text-neutral-300 font-sans whitespace-pre-wrap">
            {fir?.brief_facts && fir.brief_facts !== 'null' && fir.brief_facts !== 'undefined' ? fir.brief_facts : 'No statement of facts available.'}
          </div>
        )}
      </div>

      {/* Recommended Actions */}
      <div className="pt-2">
        <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider block mb-2 font-bold">Recommended Actions</span>
        <div className="flex flex-wrap gap-2">
          {['Find Related Cases', 'Show Nearby Crimes', 'Analyze Network', 'View Hotspots'].map((action, i) => (
            <button
              key={i}
              onClick={() => onQueryAction?.(action)}
              className="px-3 py-1.5 rounded-lg border border-cyan-500/20 bg-cyan-950/20 text-cyan-400 hover:bg-cyan-900/40 transition text-xs font-mono cursor-pointer flex items-center space-x-1.5 shadow-[0_0_10px_rgba(6,182,212,0.05)]"
            >
              <Search className="w-3 h-3" />
              <span>{action}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 3. AggregateCard (Numerical aggregated dashboard display)
// ---------------------------------------------------------------------------
function AggregateCardRaw({ count, entities }: { count: number; entities: Record<string, any> }) {
  const lang = useContext(LangContext);
  const label = entities.crime_head ? String(entities.crime_head).toUpperCase() : 'TOTAL INVESTIGATION';
  const location = entities.district ? String(entities.district) : 'State-level';

  return (
    <div className="mt-3 p-6 rounded-2xl border border-cyan-500/20 bg-gradient-to-r from-cyan-950/5 to-neutral-900/60 shadow-[0_4px_25px_rgba(6,182,212,0.04)] text-center relative overflow-hidden">
      <span className="absolute -right-6 -bottom-6 w-24 h-24 rounded-full bg-cyan-500/5 blur-xl pointer-events-none" />
      <span className="text-xs font-mono text-neutral-500 uppercase tracking-widest block mb-1">
        {t('Count', lang)}
      </span>
      <div className="text-5xl font-extrabold text-white mt-2 drop-shadow-[0_0_10px_rgba(255,255,255,0.15)]">
        {count}
      </div>
      <div className="text-xs font-mono text-cyan-405 mt-2.5 uppercase tracking-wide font-bold">
        {label} Cases in {location}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 3. Upgraded Interactive ChartWrapper with Tooltips, Legends, and Exporter
// ---------------------------------------------------------------------------
function CrimeTypeBarChart({ data }: { data: Record<string, any>[] }) {
  const chartData = Array.isArray(data) ? data.map((d) => ({
    label: d?.crime_group_name ?? d?.crime_group ?? 'Other',
    value: Number(d?.count ?? d?.total ?? 0),
  })) : [];

  const max = Math.max(...chartData.map((d) => d.value), 1);

  return (
    <div className="space-y-4">
      {chartData.slice(0, 5).map((d, i) => {
        const pct = (d.value / max) * 100;
        return (
          <div key={i} className="space-y-1.5">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-neutral-350 truncate max-w-[80%] font-semibold">{d.label}</span>
              <span className="text-purple-400 font-bold">{d.value} cases</span>
            </div>
            <div className="h-2.5 w-full rounded-full bg-neutral-900 border border-neutral-850 overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-purple-600 to-purple-400 shadow-[0_0_8px_rgba(168,85,247,0.4)] transition-all duration-500"
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function TimelineLineChartRaw({ data, isArea = false }: { data: Record<string, any>[]; isArea?: boolean }) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  const chartData = Array.isArray(data) ? data.map((d) => {
    let label = '';
    if (d?.year && d?.month) label = `${d.year}-${String(d.month).padStart(2, '0')}`;
    else if (d?.date) label = d.date;
    else if (d?.label) label = d.label;
    else label = 'N/A';
    return { label, value: Number(d?.count ?? d?.total ?? 0) };
  }) : [];

  const max = Math.max(...chartData.map((d) => d.value), 1);
  const width = 500;
  const height = 110;
  const padding = 20;

  const points = chartData.map((d, i) => {
    const x = padding + (i / (chartData.length - 1 || 1)) * (width - 2 * padding);
    const y = height - padding - (d.value / max) * (height - 2 * padding);
    return { x, y };
  });

  const pathD = points.reduce((acc, p, i) => {
    return i === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`;
  }, '');

  const areaD =
    points.length > 0
      ? `${pathD} L ${points[points.length - 1].x} ${height - padding} L ${points[0].x} ${height - padding} Z`
      : '';

  return (
    <div className="space-y-1 relative">
      <svg className="w-full h-28 overflow-visible" viewBox={`0 0 ${width} ${height}`}>
        <defs>
          <linearGradient id="purpleFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="rgba(168, 85, 247, 0.35)" />
            <stop offset="100%" stopColor="rgba(168, 85, 247, 0.0)" />
          </linearGradient>
        </defs>

        {/* Horizontal grid lines */}
        <line
          x1={padding}
          y1={height - padding}
          x2={width - padding}
          y2={height - padding}
          stroke="rgba(255,255,255,0.06)"
          strokeWidth="1"
        />
        <line
          x1={padding}
          y1={padding}
          x2={width - padding}
          y2={padding}
          stroke="rgba(255,255,255,0.02)"
          strokeWidth="1"
        />

        {/* Gradient area */}
        {isArea && areaD && <path d={areaD} fill="url(#purpleFill)" />}

        {/* Path line */}
        {pathD && (
          <path
            d={pathD}
            fill="none"
            stroke="#a855f7"
            strokeWidth="2.5"
            strokeLinecap="round"
            className="drop-shadow-[0_0_6px_rgba(168,85,247,0.5)]"
          />
        )}

        {/* Coordinate plot rings */}
        {points.map((p, i) => (
          <g
            key={i}
            onMouseEnter={() => setHoveredIdx(i)}
            onMouseLeave={() => setHoveredIdx(null)}
            className="group cursor-pointer"
          >
            <circle cx={p.x} cy={p.y} r="3.5" fill="#ffffff" stroke="#a855f7" strokeWidth="1.5" />
            <circle
              cx={p.x}
              cy={p.y}
              r="8"
              fill="rgba(168,85,247,0.2)"
              stroke="rgba(168,85,247,0.5)"
              className="opacity-0 group-hover:opacity-100 transition duration-150"
            />
          </g>
        ))}
      </svg>

      {/* Hover tooltip */}
      {hoveredIdx !== null && chartData[hoveredIdx] && (
        <div className="absolute top-0 left-1/2 transform -translate-x-1/2 bg-neutral-950/90 border border-purple-500/20 px-3 py-1 rounded text-xs font-mono text-purple-300 pointer-events-none shadow-lg">
          {chartData[hoveredIdx].label}: <span className="font-bold text-white">{chartData[hoveredIdx].value} cases</span>
        </div>
      )}

      {/* Month/Period labels */}
      <div className="flex justify-between text-xs font-mono text-neutral-500 px-2.5 mt-1">
        <span>{chartData[0]?.label}</span>
        <span>{chartData[Math.floor(chartData.length / 2)]?.label}</span>
        <span>{chartData[chartData.length - 1]?.label}</span>
      </div>
    </div>
  );
}

function DonutPieChartRaw({ data }: { data: Record<string, any>[] }) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  const chartData = Array.isArray(data) ? data.map((d) => ({
    label: d?.crime_group_name ?? d?.crime_group ?? d?.label ?? 'Other',
    value: Number(d?.count ?? d?.total ?? d?.value ?? 0),
  })) : [];

  const total = chartData.reduce((sum, d) => sum + d.value, 0) || 1;
  const radius = 36;
  const circ = 2 * Math.PI * radius;

  // HSL mapped colors for aesthetic variety
  const colors = [
    'stroke-purple-500 text-purple-400',
    'stroke-cyan-500 text-cyan-400',
    'stroke-emerald-500 text-emerald-400',
    'stroke-rose-500 text-rose-400',
    'stroke-amber-500 text-amber-400',
  ];

  let accumulatedPercent = 0;

  return (
    <div className="grid grid-cols-5 gap-4 items-center">
      {/* SVG Canvas (Span 2) */}
      <div className="col-span-2 flex justify-center relative">
        <svg className="w-28 h-28 transform -rotate-90 overflow-visible" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r={radius} fill="none" stroke="rgba(255,255,255,0.02)" strokeWidth="8" />
          {chartData.map((d, i) => {
            const pct = d.value / total;
            const strokeLength = pct * circ;
            const strokeOffset = circ - strokeLength + accumulatedPercent * circ;
            accumulatedPercent -= pct;

            return (
              <circle
                key={i}
                cx="50"
                cy="50"
                r={radius}
                fill="none"
                className={`transition-all duration-300 ${colors[i % colors.length].split(' ')[0]} ${
                  hoveredIdx === i ? 'stroke-[10px]' : 'stroke-[7px]'
                } cursor-pointer`}
                strokeWidth="7"
                strokeDasharray={circ}
                strokeDashoffset={strokeOffset}
                strokeLinecap="round"
                onMouseEnter={() => setHoveredIdx(i)}
                onMouseLeave={() => setHoveredIdx(null)}
              />
            );
          })}
        </svg>

        {/* Tooltip text in middle of donut */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center pointer-events-none">
          <span className="text-sm font-mono font-bold text-white">
            {hoveredIdx !== null ? chartData[hoveredIdx].value : total}
          </span>
          <span className="text-[9px] font-mono text-neutral-500 uppercase">
            {hoveredIdx !== null ? 'Count' : 'Total'}
          </span>
        </div>
      </div>

      {/* Interactive Legend (Span 3) */}
      <div className="col-span-3 space-y-1.5 text-xs font-mono">
        {chartData.slice(0, 5).map((d, i) => (
          <div
            key={i}
            className={`flex items-center justify-between p-1.5 rounded-lg transition duration-150 ${
              hoveredIdx === i ? 'bg-neutral-900/60 border border-neutral-850' : 'border border-transparent'
            }`}
            onMouseEnter={() => setHoveredIdx(i)}
            onMouseLeave={() => setHoveredIdx(null)}
          >
            <div className="flex items-center space-x-2 min-w-0">
              <span className={`w-2 h-2 rounded-full ${colors[i % colors.length].split(' ')[0]} bg-current`} />
              <span className="text-neutral-300 truncate font-semibold">{d.label}</span>
            </div>
            <span className="text-neutral-450 font-bold ml-1.5">
              {d.value} ({Math.round((d.value / total) * 100)}%)
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function UniversalChartContainerRaw({ data }: { data: Record<string, any>[] }) {
  const lang = useContext(LangContext);
  const [chartType, setChartType] = useState<'AREA' | 'LINE' | 'BAR' | 'DONUT'>('AREA');

  const exportCSV = () => {
    if (!data || data.length === 0) return;
    const headers = ['Category', 'Value'];
    const rows = data.map((d) => [
      d.crime_group_name ?? d.crime_group ?? d.month ?? d.period ?? 'Unknown',
      d.count ?? d.total ?? 0,
    ]);
    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((e) => e.map((x) => `"${x}"`).join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `chart_data_export_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-4">
      {/* Selector buttons */}
      <div className="flex items-center justify-between border-b border-neutral-900 pb-2.5">
        <div className="flex space-x-2">
          {(['AREA', 'LINE', 'BAR', 'DONUT'] as const).map((type) => (
            <button
              key={type}
              onClick={() => setChartType(type)}
              className={`px-3 py-1 border text-xs font-mono rounded-lg transition cursor-pointer ${
                chartType === type
                  ? 'border-purple-500/30 bg-purple-950/20 text-purple-400'
                  : 'border-neutral-850 bg-neutral-950 text-neutral-500 hover:text-white'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
        <button
          onClick={exportCSV}
          className="px-2.5 py-1 border border-neutral-850 rounded-lg text-xs font-mono hover:bg-neutral-900 text-neutral-450 hover:text-white flex items-center space-x-1.5 cursor-pointer"
        >
          <Download className="w-3.5 h-3.5" />
          <span>{t('CSV Data', lang)}</span>
        </button>
      </div>

      {/* Render selected chart */}
      <div className="p-1">
        {chartType === 'AREA' && <TimelineLineChart data={data} isArea={true} />}
        {chartType === 'LINE' && <TimelineLineChart data={data} isArea={false} />}
        {chartType === 'BAR' && <CrimeTypeBarChart data={data} />}
        {chartType === 'DONUT' && <DonutPieChart data={data} />}
      </div>
    </div>
  );
}



// ---------------------------------------------------------------------------
// 4. HotspotCard (Interactive Coordinates Mini Map + Details Table)
// ---------------------------------------------------------------------------
interface HotspotItem {
  latitude: number | string;
  longitude: number | string;
  location?: string;
  count: number | string;
  ranking?: number;
  risk_level?: string;
  crime_density?: string;
}

function HotspotCardRaw({ results, summary }: { results?: Record<string, any>[]; summary?: string | null }) {
  const lang = useContext(LangContext);
  const [hoveredStation, setHoveredStation] = useState<string | null>(null);

  if (!results || results.length === 0) {
    return (
      <div className="mt-3 p-8 text-center border border-neutral-800 rounded-xl bg-neutral-950/40">
        <MapPin className="w-8 h-8 text-neutral-600 mx-auto mb-2" />
        <p className="text-sm text-neutral-450 font-mono">{t('No coordinates found for hotspot mapping.', lang)}</p>
      </div>
    );
  }

  // Parse coordinates with ranks
  const parsedHotspots: HotspotItem[] = results
    .map((r) => ({
      latitude: parseFloat(String(r.latitude)),
      longitude: parseFloat(String(r.longitude)),
      location: r.location ?? r.police_station ?? 'Karnataka Sector',
      count: parseInt(String(r.count ?? 1)),
      ranking: r.ranking,
      risk_level: r.risk_level,
      crime_density: r.crime_density,
    }))
    .filter((h) => !isNaN(h.latitude) && !isNaN(h.longitude));

  return (
    <div className="mt-3 rounded-2xl border border-rose-500/20 bg-rose-950/5 p-5 space-y-4 shadow-[0_4px_25px_rgba(244,63,94,0.05)]">
      <div className="flex items-center justify-between border-b border-neutral-800 pb-2.5">
        <div className="flex items-center space-x-2">
          <MapPin className="w-5 h-5 text-rose-400" />
          <span className="text-xs font-mono font-bold tracking-wider text-rose-400 uppercase">
            {t('Crime Hotspots', lang)}
          </span>
        </div>
        <span className="text-[10px] font-mono text-neutral-500 uppercase">{t('Geolocation Mapping', lang)}</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-5">
        {/* Interactive SVG map canvas - Span 2 */}
        <div className="md:col-span-2 rounded-xl border border-neutral-800 bg-black/40 overflow-hidden relative min-h-[170px] flex items-center justify-center">
          <span className="absolute top-2.5 left-2.5 text-[9px] font-mono text-neutral-500">Radar Plot Outline</span>
          <HotspotMiniMap hotspots={parsedHotspots} hoveredStation={hoveredStation} />
        </div>

        {/* Hotspot details table - Span 3 */}
        <div className="md:col-span-3 rounded-xl border border-neutral-800 bg-neutral-900/30 overflow-hidden max-h-[170px] overflow-y-auto">
          <table className="w-full text-xs font-mono">
            <thead>
              <tr className="border-b border-neutral-800 bg-neutral-900/40 text-neutral-400">
                <th className="px-3 py-2 text-left uppercase">Location</th>
                <th className="px-3 py-2 text-left uppercase">Risk / density</th>
                <th className="px-3 py-2 text-center uppercase">Count</th>
              </tr>
            </thead>
            <tbody>
              {parsedHotspots.slice(0, 5).map((h, i) => {
                const rankColors: Record<number, string> = {
                  1: 'text-rose-400 font-bold',
                  2: 'text-rose-350',
                  3: 'text-rose-300',
                };
                const riskBadge = h.risk_level || 'LOW';

                return (
                  <tr
                    key={i}
                    className={`border-b border-neutral-900 hover:bg-neutral-900/20 transition cursor-help ${
                      hoveredStation === h.location ? 'bg-neutral-900/40' : ''
                    }`}
                    onMouseEnter={() => setHoveredStation(h.location || null)}
                    onMouseLeave={() => setHoveredStation(null)}
                  >
                    <td className="px-3 py-2.5 truncate max-w-[100px]">
                      <span className={rankColors[h.ranking || 0] || 'text-neutral-250'}>
                        {h.ranking ? `${h.ranking}. ` : ''}
                        {h.location}
                      </span>
                    </td>
                    <td className="px-3 py-2.5">
                      <span className="text-[10px] border border-neutral-850 px-2 py-0.5 rounded-lg text-neutral-400 bg-neutral-950 font-bold uppercase">
                        {riskBadge}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 text-center text-rose-400 font-bold">{h.count}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {summary && (
        <div className="rounded-xl border border-neutral-800 bg-neutral-950/40 p-3 flex items-start space-x-2.5">
          <Compass className="w-4 h-4 text-rose-400 mt-0.5 flex-shrink-0" />
          <p className="text-xs md:text-sm text-neutral-350 leading-relaxed font-sans">{summary}</p>
        </div>
      )}
    </div>
  );
}

// Sub-component: Geolocation SVG Mini Map (scales Karnataka coordinates)
function HotspotMiniMap({ hotspots, hoveredStation }: { hotspots: HotspotItem[]; hoveredStation: string | null }) {
  const minLat = 11.5;
  const maxLat = 18.5;
  const minLon = 74.0;
  const maxLon = 78.5;

  const width = 200;
  const height = 150;

  const getXY = (lat: number, lon: number) => {
    const x = ((lon - minLon) / (maxLon - minLon)) * width;
    const y = height - ((lat - minLat) / (maxLat - minLat)) * height;
    return { x, y };
  };

  return (
    <svg width={width} height={height} className="overflow-visible">
      <defs>
        <pattern id="miniGrid" width="20" height="20" patternUnits="userSpaceOnUse">
          <rect width="20" height="20" fill="none" stroke="rgba(255,255,255,0.015)" strokeWidth="0.5" />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#miniGrid)" />

      <path
        d="M 20 120 Q 50 80 90 90 T 140 60 T 180 30"
        fill="none"
        stroke="rgba(244,63,94,0.08)"
        strokeWidth="1.5"
        strokeDasharray="3 6"
      />

      {hotspots.map((h, i) => {
        const { x, y } = getXY(Number(h.latitude), Number(h.longitude));
        const cx = Math.max(10, Math.min(x, width - 10));
        const cy = Math.max(10, Math.min(y, height - 10));
        const isHovered = hoveredStation === h.location;

        return (
          <g key={i} className="group">
            <circle
              cx={cx}
              cy={cy}
              r={isHovered ? 18 : 12}
              className="fill-rose-500/10 stroke-rose-500/20 stroke-[0.5px] animate-ping"
              style={{ animationDuration: isHovered ? '2s' : '3.5s' }}
            />
            <circle
              cx={cx}
              cy={cy}
              r={isHovered ? 6 : 4}
              fill="#f43f5e"
              className="stroke-white stroke-[1.5px] transition-all duration-300"
            />
          </g>
        );
      })}
    </svg>
  );
}

// ---------------------------------------------------------------------------
// 5. PredictionCard (Vibrant Metrics Gauge & G-Trend Line)
// ---------------------------------------------------------------------------
function PredictionCardRaw({ p }: { p: PredictionResult }) {
  const lang = useContext(LangContext);
  const confColour =
    p.confidence >= 75
      ? 'text-emerald-455 stroke-emerald-500'
      : p.confidence >= 50
      ? 'text-amber-455 stroke-amber-500'
      : 'text-rose-400 stroke-rose-500';

  const r = 26;
  const circ = 2 * Math.PI * r;
  const strokeDashoffset = circ - (p.confidence / 100) * circ;

  return (
    <div className="mt-3 rounded-2xl border border-cyan-500/20 bg-gradient-to-r from-cyan-950/5 to-neutral-900/60 p-5 space-y-4 shadow-[0_4px_25px_rgba(6,182,212,0.06)] relative overflow-hidden">
      <span className="absolute -left-6 -bottom-6 w-24 h-24 rounded-full bg-cyan-500/5 blur-xl pointer-events-none" />

      {/* Header */}
      <div className="flex items-center justify-between border-b border-neutral-800 pb-2.5">
        <div className="flex items-center space-x-2">
          <Shield className="w-5 h-5 text-cyan-400 animate-pulse" />
          <span className="text-xs font-mono font-bold tracking-wider text-cyan-405 uppercase">
            {t('Prediction Dashboard', lang)}
          </span>
        </div>
        <span className="text-xs font-mono text-neutral-500 uppercase tracking-wide">
          Target: {p.forecast_month}
        </span>
      </div>

      {/* Main Stats Segment */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        {/* Expected count */}
        <div className="rounded-xl border border-neutral-800 bg-neutral-950/40 p-4 text-center flex flex-col justify-center">
          <span className="text-[10px] font-mono text-neutral-500 uppercase">{t('Predicted Cases', lang)}</span>
          <div className="text-4xl font-extrabold text-white mt-1.5 drop-shadow-[0_0_8px_rgba(255,255,255,0.15)]">
            {p.predicted_cases}
          </div>
          <span className="text-[9px] font-mono text-neutral-550 mt-1 uppercase">{t('Estimated Volume', lang)}</span>
        </div>

        {/* Radial Confidence Gauge */}
        <div className="rounded-xl border border-neutral-800 bg-neutral-950/40 p-3 flex flex-col items-center justify-center">
          <span className="text-[10px] font-mono text-neutral-500 uppercase mb-2">{t('Confidence Level', lang)}</span>
          <div className="relative w-16 h-16 flex items-center justify-center">
            <svg className="w-full h-full transform -rotate-90">
              <circle cx="32" cy="32" r={r} fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth="4" />
              <circle
                cx="32"
                cy="32"
                r={r}
                fill="none"
                className={`${confColour} transition-all duration-1000`}
                strokeWidth="4"
                strokeDasharray={circ}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute text-xs font-mono font-bold text-neutral-200">{p.confidence}%</div>
          </div>
        </div>

        {/* Growth trend */}
        <div className="rounded-xl border border-neutral-800 bg-neutral-950/40 p-4 text-center flex flex-col items-center justify-center">
          <span className="text-[10px] font-mono text-neutral-500 uppercase">{t('Growth Trend', lang)}</span>
          <div className="flex items-center space-x-2 mt-2">
            <TrendIcon trend={p.trend} />
            <span className="text-base font-bold text-neutral-200">{p.trend}</span>
          </div>
          <span className="text-[9px] font-mono text-neutral-550 mt-1.5 uppercase font-semibold">OLS Regression</span>
        </div>

        {/* Risk Badge */}
        <div className="rounded-xl border border-neutral-800 bg-neutral-950/40 p-4 text-center flex flex-col items-center justify-center">
          <span className="text-[10px] font-mono text-neutral-500 uppercase">{t('Risk Level', lang)}</span>
          <div className="mt-2.5">
            <RiskBadge level={p.risk_level} />
          </div>
          <span className="text-[9px] font-mono text-neutral-555 mt-2 uppercase font-semibold">Density Limit</span>
        </div>
      </div>

      {/* Model context */}
      <div className="flex items-center justify-between text-xs font-mono text-neutral-550 pt-1">
        <span>Estimator: {p.model_used}</span>
        <span>Timeline: {p.data_points_used} months analyzed</span>
      </div>

      {/* Reasoning log */}
      <div className="rounded-xl border border-neutral-800 bg-neutral-950/30 p-4 flex items-start space-x-3">
        <Clock className="w-5 h-5 text-cyan-405 mt-0.5 flex-shrink-0" />
        <div>
          <span className="block text-[10px] font-mono text-neutral-500 uppercase mb-0.5">Analytic Reasoning</span>
          <p className="text-xs md:text-sm text-neutral-350 leading-relaxed font-sans">{p.reasoning}</p>
        </div>
      </div>

      {/* Sparkline mini chart */}
      {p.historical_counts.length > 0 && (
        <div className="space-y-2">
          <span className="block text-xs font-mono text-neutral-500 uppercase tracking-wide">
            Historical Sparkline
          </span>
          <div className="flex items-end space-x-1.5 h-10">
            {Array.isArray(p?.historical_counts) && p.historical_counts.slice(-15).map((h, i) => {
              const max = Math.max(...p.historical_counts.map((x) => x.count || 0), 1);
              const height = `${Math.max((h.count / max) * 100, 5)}%`;
              return (
                <div
                  key={i}
                  title={`${h.year}-${String(h.month).padStart(2, '0')}: ${h.count}`}
                  className="flex-1 rounded bg-cyan-500/25 hover:bg-cyan-400/50 transition cursor-help animate-fadeIn"
                  style={{ height }}
                />
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// Helpers for prediction card
function RiskBadge({ level }: { level: string }) {
  const colours: Record<string, string> = {
    HIGH: 'bg-rose-500/10 text-rose-400 border-rose-500/20 shadow-[0_0_6px_rgba(244,63,94,0.1)]',
    MEDIUM: 'bg-amber-500/10 text-amber-455 border-amber-500/20 shadow-[0_0_6px_rgba(245,158,11,0.1)]',
    LOW: 'bg-emerald-500/10 text-emerald-455 border-emerald-500/20 shadow-[0_0_6px_rgba(10,185,129,0.1)]',
    UNKNOWN: 'bg-neutral-800/20 text-neutral-455 border-neutral-700/20',
  };
  return (
    <span
      className={`text-xs font-mono font-bold uppercase px-3.5 py-1.5 rounded-full border ${
        colours[level] ?? colours.UNKNOWN
      }`}
    >
      {level}
    </span>
  );
}

function TrendIcon({ trend }: { trend: string }) {
  if (trend === 'Increasing') return <TrendingUp className="w-5 h-5 text-rose-400 animate-bounce" />;
  if (trend === 'Decreasing') return <TrendingDown className="w-5 h-5 text-emerald-400" />;
  return <Minus className="w-5 h-5 text-neutral-400" />;
}

// ---------------------------------------------------------------------------
// 6. AccusedCardGrid (SEARCH_ACCUSED profile cards & empty state)
// ---------------------------------------------------------------------------


function AccusedCardGridRaw({ records }: { records: Record<string, any>[] }) {
  const lang = useContext(LangContext);
  if (!Array.isArray(records) || records.length === 0) {
    return (
      <div className="mt-3 p-8 text-center border border-neutral-800 rounded-xl bg-neutral-950/40">
        <Users className="w-8 h-8 text-neutral-600 mx-auto mb-2" />
        <p className="text-sm text-neutral-455 font-mono">{t('No accused matches found in the system registry.', lang)}</p>
      </div>
    );
  }

  return (
    <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-4">
      {records.slice(0, 10).map((acc, i) => {
        const name = acc?.name || acc?.accused_name || 'Unknown';
        const photoUrl = acc?.photo || `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=random`;
        const riskScore = acc?.risk_score;
        const caseCount = acc?.cases || 1;
        const crimeCategory = acc?.crime_types || acc?.crime_category || 'Unknown';
        const district = acc?.district || acc?.district_name || 'Unknown';
        const policeStation = acc?.police_station_name || 'N/A';
        const status = acc?.status_name || 'Unknown';
        
        let riskColor = 'text-green-400 bg-green-500/10 border-green-500/20';
        let riskLabel = 'LOW RISK';
        if (riskScore >= 75 || caseCount >= 3) {
          riskColor = 'text-rose-400 bg-rose-500/10 border-rose-500/20';
          riskLabel = 'HIGH RISK';
        } else if (riskScore >= 40 || caseCount > 1) {
          riskColor = 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20';
          riskLabel = 'MED RISK';
        }

        return (
          <div
            key={i}
            className="rounded-2xl border border-neutral-800 bg-neutral-900/30 p-4 hover:border-cyan-500/25 transition duration-200 flex flex-col"
          >
            <div className="flex items-start gap-4">
              <div className="w-16 h-16 rounded-xl border border-neutral-800 bg-neutral-950 flex items-center justify-center overflow-hidden flex-shrink-0">
                <img src={photoUrl} alt={name} className="w-full h-full object-cover" />
              </div>

              <div className="flex-1 min-w-0 space-y-1.5 text-xs">
                <div className="flex items-start justify-between">
                  <span className="block text-sm font-bold text-white truncate pr-2">
                    {name}
                  </span>
                  {(riskScore !== undefined || caseCount > 1) && (
                    <span className={`text-[9px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider ${riskColor}`}>
                      {riskLabel}
                    </span>
                  )}
                </div>
                
                <div className="text-xs font-mono text-neutral-450 space-x-2">
                  <span>Age: {acc.age_year ?? 'Unk'}</span>
                  <span>•</span>
                  <span>{acc.gender_id === 1 ? 'Male' : acc.gender_id === 2 ? 'Female' : 'Unk'}</span>
                  <span>•</span>
                  <span>Cases: <span className="font-bold text-cyan-400">{caseCount}</span></span>
                </div>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-neutral-800/60 grid grid-cols-2 gap-y-3 text-xs font-mono">
              <div>
                <span className="block text-[10px] text-neutral-500 uppercase tracking-wider mb-0.5">Crime Type</span>
                <span className="text-neutral-300 truncate block pr-2" title={crimeCategory}>{crimeCategory}</span>
              </div>
              <div>
                <span className="block text-[10px] text-neutral-500 uppercase tracking-wider mb-0.5">Status</span>
                <span className="text-neutral-300 truncate block pr-2">{status}</span>
              </div>
              <div className="col-span-2">
                <span className="block text-[10px] text-neutral-500 uppercase tracking-wider mb-0.5">Location</span>
                <span className="text-neutral-300 truncate block pr-2" title={`${district} / ${policeStation}`}>{district} {policeStation !== 'N/A' && `- ${policeStation}`}</span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// 8. Dynamic Insights Display Card
// ---------------------------------------------------------------------------
function InsightsBlock({ insights }: { insights: string[] }) {
  const lang = useContext(LangContext);
  return (
    <div className="mt-4 grid grid-cols-1 gap-2.5">
      {Array.isArray(insights) && insights.map((ins, idx) => (
        <div
          key={idx}
          className="p-4 rounded-xl border border-cyan-500/10 bg-cyan-950/5 flex items-start space-x-3 shadow-[0_2px_10px_rgba(6,182,212,0.02)] hover:bg-cyan-950/10 transition"
        >
          <Sparkles className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5 animate-pulse" />
          <p className="text-xs md:text-sm text-neutral-300 leading-relaxed font-sans">{t(ins, lang)}</p>
        </div>
      ))}
    </div>
  );
}

const FIRLookupDossier = memo(FIRLookupDossierRaw);

// ---------------------------------------------------------------------------
// Main IntentResponseBlock Orchestrator
// ---------------------------------------------------------------------------
// Custom Lightweight Components
// ---------------------------------------------------------------------------
function VictimCard({ payload }: { payload: BackendResponse }) {
  const summary = payload.summary || "No victim information available.";
  return (
    <div className="p-4 rounded-xl border border-cyan-500/20 bg-cyan-950/10 shadow-sm mt-2">
       <div className="flex items-center space-x-2 text-cyan-400 mb-2">
         <Users className="w-4 h-4" />
         <span className="text-xs font-mono uppercase font-bold tracking-wider">Victim Profile</span>
       </div>
       <div className="text-sm text-neutral-300 font-sans leading-relaxed whitespace-pre-wrap">
         {summary}
       </div>
    </div>
  );
}

function StatusBadge({ payload }: { payload: BackendResponse }) {
  const summary = payload.summary || "No status available.";
  return (
    <div className="mt-2 inline-flex items-center space-x-2 px-4 py-2 rounded-lg border border-purple-500/30 bg-purple-950/20 shadow-sm">
       <Activity className="w-4 h-4 text-purple-400" />
       <span className="text-sm font-semibold text-purple-200">{summary}</span>
    </div>
  );
}

function LocationBadge({ payload, icon: Icon, title }: { payload: BackendResponse, icon: any, title?: string }) {
  const summary = payload.summary || "Information unavailable.";
  return (
    <div className="p-4 rounded-xl border border-emerald-500/20 bg-emerald-950/10 shadow-sm mt-2">
       {title && (
         <div className="flex items-center space-x-2 text-emerald-400 mb-2">
           <Icon className="w-4 h-4" />
           <span className="text-xs font-mono uppercase font-bold tracking-wider">{title}</span>
         </div>
       )}
       {!title && (
         <Icon className="w-4 h-4 text-emerald-400 inline-block mr-2" />
       )}
       <span className="text-sm text-neutral-300 font-sans leading-relaxed whitespace-pre-wrap">{summary}</span>
    </div>
  );
}

function NetworkSummaryCard({ payload }: { payload: BackendResponse }) {
  const summary = payload.summary || "No network information available.";
  return (
    <div className="mt-3 p-5 rounded-2xl border border-blue-500/20 bg-blue-950/10 shadow-md">
       <div className="flex items-center space-x-2 text-blue-400 mb-3 border-b border-blue-500/10 pb-2">
         <Activity className="w-5 h-5" />
         <span className="text-xs font-mono uppercase font-bold tracking-wider">Investigation Network Analysis</span>
       </div>
       <div className="text-sm text-neutral-300 font-sans leading-relaxed whitespace-pre-wrap">
         {summary}
       </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
function IntentResponseBlock({ payload, onQueryAction }: { payload: BackendResponse; onQueryAction?: (q: string) => void }) {
  const { intent, count, results, prediction, summary, insights } = payload;
  const rawCount = count ?? (results ? results.length : 0);

  return (
    <ErrorBoundary>
      <div className="space-y-4">
        {/* Context specific UI for active FIR follow-ups */}
        {intent === 'SEARCH_VICTIMS' && payload.summary && payload.summary.includes("victims") && (
          <VictimCard payload={payload} />
        )}
        
        {intent === 'SEARCH_POLICE_STATION' && (
          <LocationBadge payload={payload} icon={Shield} title="Police Station Jurisdiction" />
        )}
        
        {intent === 'SEARCH_LOCATION' && (
          <LocationBadge payload={payload} icon={MapPin} title="Incident District" />
        )}
        
        {intent === 'SEARCH_OFFICER' && (
          <LocationBadge payload={payload} icon={User} title="Investigating Officer" />
        )}
        
        {intent === 'NETWORK_ANALYSIS' && (
          <NetworkSummaryCard payload={payload} />
        )}

        {/* 1. SEARCH_CASES or SEARCH_VICTIMS */}
        {(intent === 'SEARCH_CASES' || intent === 'SEARCH_VICTIMS') && Array.isArray(results) && !(intent === 'SEARCH_VICTIMS' && payload.summary && payload.summary.includes("victims")) && (
          <CasesTable records={results} />
        )}

        {/* FIR_LOOKUP */ }
        {intent === 'FIR_LOOKUP' && Array.isArray(results) && (
          <FIRLookupDossier records={results} onQueryAction={onQueryAction} />
        )}

        {/* 2. SEARCH_ACCUSED, MOST_WANTED, REPEAT_OFFENDERS */}
        {(intent === 'SEARCH_ACCUSED' || intent === 'MOST_WANTED' || intent === 'REPEAT_OFFENDERS') && Array.isArray(results) && (
          <AccusedCardGrid records={results} />
        )}

      {/* 3. AGGREGATE_COUNT */}
      {intent === 'AGGREGATE_COUNT' && payload.summary && payload.summary.includes("investigation status") ? (
        <StatusBadge payload={payload} />
      ) : (
        intent === 'AGGREGATE_COUNT' && <AggregateCard count={rawCount} entities={payload.entities} />
      )}

      {/* 4. CRIME_TREND */}
      {intent === 'CRIME_TREND' && payload.summary && payload.summary.includes("registered on") ? (
        <LocationBadge payload={payload} icon={Calendar} title="Registration Date" />
      ) : (
        intent === 'CRIME_TREND' && results && (
          <div className="mt-3 rounded-2xl border border-purple-500/20 bg-purple-950/5 p-5 space-y-4 shadow-[0_4px_25px_rgba(168,85,247,0.05)]">
            <div className="flex items-center justify-between border-b border-neutral-800 pb-2.5">
              <div className="flex items-center space-x-2">
                <BarChart3 className="w-5 h-5 text-purple-400" />
                <span className="text-xs font-mono font-bold tracking-wider text-purple-400 uppercase">
                  Crime Trend Analytics
                </span>
              </div>
              <span className="text-[10px] font-mono text-neutral-500 uppercase font-bold">Growth Statistics</span>
            </div>
            <UniversalChartContainer data={results} />
          </div>
        )
      )}

      {/* 5. HOTSPOT */}
      {intent === 'HOTSPOT' && (
        <HotspotCard results={results} summary={summary} />
      )}

      {/* 6. PREDICT_CRIME */}
      {intent === 'PREDICT_CRIME' && prediction && (
        <PredictionCard p={prediction} />
      )}

      {/* 7. Automatic insights panels */}
      {insights && insights.length > 0 && <InsightsBlock insights={insights} />}
    </div>
    </ErrorBoundary>
  );
}

// ---------------------------------------------------------------------------
// Skeletons, Error boundaries & suggestions
// ---------------------------------------------------------------------------
function LoadingSkeleton({ stage = 0 }: { stage?: number }) {
  return <SequencedStatusLoader stage={stage} />;
}

function ErrorAlert({ message, onRetry }: { message: string; onRetry?: () => void }) {
  const lang = useContext(LangContext);
  return (
    <div className="p-4 rounded-xl border border-rose-500/20 bg-rose-950/10 flex items-start space-x-3.5 mt-3 relative overflow-hidden">
      <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <div className="text-xs font-mono font-bold text-rose-400 uppercase mb-0.5">{t('Portal System Error', lang)}</div>
        <p className="text-xs md:text-sm text-rose-300 leading-normal font-sans">{t(message, lang)}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-3 px-3 py-1 border border-rose-500/30 rounded-lg text-xs font-mono hover:bg-rose-950/30 text-rose-300 hover:text-white cursor-pointer animate-pulse"
          >
            {t('Retry Inspection', lang)}
          </button>
        )}
      </div>
    </div>
  );
}

// React memoized containers for eliminating redundant visual redraws
const CasesTable = memo(CasesTableRaw);
const AggregateCard = memo(AggregateCardRaw);
const TimelineLineChart = memo(TimelineLineChartRaw);
const DonutPieChart = memo(DonutPieChartRaw);
const UniversalChartContainer = memo(UniversalChartContainerRaw);
const HotspotCard = memo(HotspotCardRaw);
const PredictionCard = memo(PredictionCardRaw);
const AccusedCardGrid = memo(AccusedCardGridRaw);

// ---------------------------------------------------------------------------
// AIWorkspace Main Component
// ---------------------------------------------------------------------------
interface AIWorkspaceProps {
  initialSearchQuery?: string;
  onSelectEntity?: (name: string) => void;
  className?: string;
  isFullscreen?: boolean;
  onToggleFullscreen?: () => void;
}

export default function AIWorkspace({ 
  initialSearchQuery = '', 
  onSelectEntity, 
  className = 'flex-1',
  isFullscreen = false,
  onToggleFullscreen
}: AIWorkspaceProps) {
  if (onSelectEntity) {
    // no-op to satisfy typescript compiler unused variable rules
  }
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'm-welcome',
      sender: 'assistant',
      text: 'System boot successful. KSP Sentinel AI Core initialized. Access clearance verified. I have indexed 5 active FIR files, 4 high-risk accused profiles, and real-time cellular towers. Ask about any FIR, accused profile, location, or cross-case correlation.',
      timestamp: new Date().toLocaleTimeString(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [selectedModel, setSelectedModel] = useState('KSP-Sentinel-v3.5-Intelligence');
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingStage, setLoadingStage] = useState(0);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [demoActive, setDemoActive] = useState(false);
  const [activeDrawerPayload, setActiveDrawerPayload] = useState<BackendResponse | null>(null);
  const [bootLines, setBootLines] = useState<string[]>([]);
  const [language, setLanguage] = useState<'auto' | 'en' | 'kn'>('auto');
  const [activeUiLang, setActiveUiLang] = useState<'en' | 'kn'>('en');
  
  useEffect(() => {
    if (language !== 'auto') {
      setActiveUiLang(language);
    }
  }, [language]);

  const [micState, setMicState] = useState<'idle' | 'listening' | 'processing' | 'error'>('idle');
  const [micError, setMicError] = useState<string | null>(null);
  const recognitionRef = useRef<any>(null);
  const startInputRef = useRef<string>('');

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isFullscreen && onToggleFullscreen) {
        onToggleFullscreen();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isFullscreen, onToggleFullscreen]);

  const toggleMicrophone = () => {
    if (micState === 'listening' || micState === 'processing') {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setMicState('idle');
      return;
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setMicState('error');
      setMicError('Browser unsupported');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = true;
    recognition.continuous = true;
    recognitionRef.current = recognition;
    startInputRef.current = inputValue;

    recognition.onstart = () => {
      setMicState('listening');
      setMicError(null);
    };

    recognition.onresult = (event: any) => {
      let currentTranscript = '';
      for (let i = 0; i < event.results.length; i++) {
        currentTranscript += event.results[i][0].transcript;
      }
      
      const prefix = startInputRef.current ? startInputRef.current + ' ' : '';
      setInputValue(prefix + currentTranscript);
    };

    recognition.onerror = (event: any) => {
      if (event.error === 'not-allowed') {
        setMicError('Permission denied');
      } else if (event.error === 'no-speech') {
        setMicError('No speech detected');
      } else if (event.error === 'network') {
        setMicError('Network error');
      } else {
        setMicError('Recognition error');
      }
      setMicState('error');
    };

    recognition.onend = () => {
      setMicState((prev) => {
        if (prev !== 'error') return 'idle';
        return prev;
      });
    };

    try {
      recognition.start();
    } catch (err) {
      setMicState('error');
    }
  };

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Terminal boot log animations
  useEffect(() => {
    if (messages.length > 1 || demoActive) return;
    const lines = [
      "➔ Security Enclave deployed.",
      "➔ Portal socket synchronized: 127.0.0.1:8000",
      "➔ Access token assigned: Insp. Vikram Rathore [INSP]",
      "➔ Cache intercept ready. DB integrity: 100% OK.",
      "➔ KSP Sentinel core intelligence engine boot successful."
    ];
    setBootLines([]);
    const timers = lines.map((line, idx) => {
      return setTimeout(() => {
        setBootLines((prev) => [...prev, line]);
      }, (idx + 1) * 350);
    });
    return () => timers.forEach(clearTimeout);
  }, [messages.length, demoActive]);

  const demoMessages: Message[] = [
    {
      id: 'm-welcome',
      sender: 'assistant',
      text: 'System boot successful. KSP Sentinel AI Core initialized. Access clearance verified. I have indexed 5 active FIR files, 4 high-risk accused profiles, and real-time cellular towers. Ask about any FIR, accused profile, location, or cross-case correlation.',
      timestamp: '15:30:00',
    },
    {
      id: 'd-user-1',
      sender: 'user',
      text: 'Show theft in Mysuru',
      timestamp: '15:30:10',
    },
    {
      id: 'd-ast-1',
      sender: 'assistant',
      text: 'Retrieved 3 theft records in Mysuru district matching query.',
      timestamp: '15:30:12',
      backendPayload: {
        success: true,
        query: 'Show theft in Mysuru',
        intent: 'SEARCH_CASES',
        entities: { crime_head: 'theft', district: 'Mysuru' },
        summary: 'Retrieved 3 theft records in Mysuru district.',
        results: [
          { crime_no: 'KA-MY-2026-0091', case_no: 'FIR-091', crime_registered_date: '2026-03-12', status: 1, brief_facts: 'Complainant reported theft of a motor vehicle parked near Devaraja Market, Mysuru.', fir_summary: 'Motor vehicle theft at Devaraja Market' },
          { crime_no: 'KA-MY-2026-0042', case_no: 'FIR-042', crime_registered_date: '2026-02-19', status: 2, brief_facts: 'Break-in reported at a residential building in Gokulam, Mysuru. Gold jewelry and cash stolen.', fir_summary: 'Residential break-in and burglary in Gokulam' },
          { crime_no: 'KA-MY-2026-0015', case_no: 'FIR-015', crime_registered_date: '2026-01-08', status: 3, brief_facts: 'Shoplifting suspect apprehended by security at Mall of Mysore with stolen electronics.', fir_summary: 'Electronics shoplifting suspect apprehended' }
        ],
        explanation: {
          intent: 'SEARCH_CASES',
          entities: { crime_head: 'theft', district: 'Mysuru' },
          reasoning: 'Searching historical crime registers matching keyword parameters. Filters applied for theft cases in Mysuru.',
          filters: ['crime_head=theft', 'district=Mysuru'],
          sql_summary: 'SELECT * FROM case_master WHERE crime_head_id = 4 AND district_id = 12 ORDER BY crime_registered_date DESC LIMIT 5'
        },
        metadata: { query: 'Show theft in Mysuru', query_time_ms: 42.15, cache_hit: false }
      }
    },
    {
      id: 'd-user-2',
      sender: 'user',
      text: 'Crime trend in Bengaluru Urban',
      timestamp: '15:31:05',
    },
    {
      id: 'd-ast-2',
      sender: 'assistant',
      text: 'Monthly crime count trend for Bengaluru Urban.',
      timestamp: '15:31:07',
      backendPayload: {
        success: true,
        query: 'Crime trend in Bengaluru Urban',
        intent: 'CRIME_TREND',
        entities: { district: 'Bengaluru Urban' },
        summary: 'Monthly crime count trend for Bengaluru Urban.',
        results: [
          { period: '2025-09', count: 45 },
          { period: '2025-10', count: 52 },
          { period: '2025-11', count: 48 },
          { period: '2025-12', count: 61 },
          { period: '2026-01', count: 55 },
          { period: '2026-02', count: 72 },
          { period: '2026-03', count: 68 }
        ],
        explanation: {
          intent: 'CRIME_TREND',
          entities: { district: 'Bengaluru Urban' },
          reasoning: 'Aggregating crime cases chronologically and categorical distributions to detect growth curves.',
          filters: ['district=Bengaluru Urban'],
          sql_summary: "SELECT strftime('%Y-%m', crime_registered_date) as period, COUNT(*) as count FROM case_master WHERE district_id = 1 GROUP BY period ORDER BY period ASC"
        },
        metadata: { query: 'Crime trend in Bengaluru Urban', query_time_ms: 38.5, cache_hit: false }
      }
    },
    {
      id: 'd-user-3',
      sender: 'user',
      text: 'Predict theft next month in Mysuru',
      timestamp: '15:32:00',
    },
    {
      id: 'd-ast-3',
      sender: 'assistant',
      text: 'Prediction for 2026-04: 12 cases expected. Risk: MEDIUM. Confidence: 84%.',
      timestamp: '15:32:03',
      backendPayload: {
        success: true,
        query: 'Predict theft next month in Mysuru',
        intent: 'PREDICT_CRIME',
        entities: { crime_head: 'theft', district: 'Mysuru' },
        prediction: {
          predicted_cases: 12,
          risk_level: 'MEDIUM',
          confidence: 84,
          trend: 'Increasing',
          reasoning: 'OLS linear regression projection predicts 12 cases for theft in Mysuru next month.',
          historical_counts: [
            { year: 2025, month: 10, count: 8 },
            { year: 2025, month: 11, count: 9 },
            { year: 2025, month: 12, count: 7 },
            { year: 2026, month: 1, count: 11 },
            { year: 2026, month: 2, count: 10 },
            { year: 2026, month: 3, count: 13 }
          ],
          forecast_month: '2026-04',
          model_used: 'OLS Linear Regressor v1.2',
          data_points_used: 6
        },
        explanation: {
          intent: 'PREDICT_CRIME',
          entities: { crime_head: 'theft', district: 'Mysuru' },
          reasoning: 'Applying Ordinary Least Squares (OLS) regression and rolling moving average to model future caseload.',
          filters: ['crime_head=theft', 'district=Mysuru'],
          sql_summary: 'None (Predictive OLS Model)'
        },
        metadata: { query: 'Predict theft next month in Mysuru', query_time_ms: 112.4, cache_hit: false }
      }
    },
    {
      id: 'd-user-4',
      sender: 'user',
      text: 'Top hotspots',
      timestamp: '15:32:50',
    },
    {
      id: 'd-ast-4',
      sender: 'assistant',
      text: 'Crime hotspot coordinate listing ranked by counts.',
      timestamp: '15:32:52',
      backendPayload: {
        success: true,
        query: 'Top hotspots',
        intent: 'HOTSPOT',
        entities: {},
        summary: 'Crime hotspot coordinate listing ranked by counts.',
        results: [
          { latitude: 12.9716, longitude: 77.5946, location: 'Bengaluru Urban', count: 184, ranking: 1, risk_level: 'CRITICAL', crime_density: 'CRITICAL' },
          { latitude: 12.2958, longitude: 76.6394, location: 'Mysuru', count: 126, ranking: 2, risk_level: 'HIGH', crime_density: 'HIGH' },
          { latitude: 15.3647, longitude: 75.1240, location: 'Hubballi', count: 78, ranking: 3, risk_level: 'MEDIUM', crime_density: 'MEDIUM' }
        ],
        explanation: {
          intent: 'HOTSPOT',
          entities: {},
          reasoning: 'Evaluating geolocation density of police station and district coordinates to locate risk areas.',
          filters: [],
          sql_summary: 'SELECT latitude, longitude, police_station_name, COUNT(*) as count FROM case_master GROUP BY latitude, longitude ORDER BY count DESC LIMIT 3'
        },
        metadata: { query: 'Top hotspots', query_time_ms: 65.2, cache_hit: false }
      }
    }
  ];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  useEffect(() => {
    if (initialSearchQuery) {
      handleSend(initialSearchQuery);
    }
  }, [initialSearchQuery]);

  const handleSend = async (manualQuery?: string) => {
    const query = manualQuery ?? inputValue;
    if (!query.trim()) return;

    setError(null);
    setShowSuggestions(false); // Hide suggested queries once a search triggers

    const isKn = language === 'kn' || (language === 'auto' && detectKannada(query));
    if (language === 'auto') {
      setActiveUiLang(isKn ? 'kn' : 'en');
    }

    const userMsg: Message = {
      id: `usr-${Date.now()}`,
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString(),
      isKannada: isKn,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputValue('');
    setIsTyping(true);
    setLoadingStage(0);

    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setMicState('idle');
    setMicError(null);

    const timer1 = setTimeout(() => setLoadingStage(1), 400);

    try {
      let englishQuery = query;
      if (isKn) {
        englishQuery = await translateToEnglish(query);
      }

      const data = await sendChatMessage(englishQuery);
      clearTimeout(timer1);
      setLoadingStage(2);
      await new Promise(r => setTimeout(r, 200));

      // Build text summary
      const intentLabel = data.intent?.replace(/_/g, ' ') ?? 'Response';
      let safeSummary = data.summary;
      
      if (typeof safeSummary === 'object' && safeSummary !== null) {
        // Strict fallback. NEVER stringify the entire object into the chat.
        safeSummary = (safeSummary as any).summary ?? (safeSummary as any).text ?? null;
      }
      
      let bubbleText = (typeof safeSummary === 'string' && safeSummary.trim() !== '') 
        ? safeSummary 
        : `Intent detected: ${intentLabel}.`;

      if (data.intent === 'PREDICT_CRIME' && data.prediction) {
        const p = data.prediction;
        bubbleText = `Prediction for ${p.forecast_month}: ${p.predicted_cases} cases expected. Risk: ${p.risk_level}. Confidence: ${p.confidence}%.`;
      } else if (data.intent === 'AGGREGATE_COUNT' && data.count !== undefined) {
        bubbleText = (typeof safeSummary === 'string' && safeSummary.trim() !== '') ? safeSummary : `Total aggregate count: ${data.count}`;
      } else if (data.results && data.results.length > 0) {
        bubbleText = (typeof safeSummary === 'string' && safeSummary.trim() !== '') ? safeSummary : `Retrieved ${data.results.length} record(s) matching your request.`;
      }

      if (isKn) {
        try {
          if (bubbleText) bubbleText = await translateToKannada(bubbleText);
          if (data.insights && Array.isArray(data.insights)) {
            data.insights = await Promise.all(data.insights.map((i: string) => translateToKannada(i)));
          }
          if (data.explanation) {
             if (data.explanation.intent) data.explanation.intent = await translateToKannada(data.explanation.intent);
             if (data.explanation.reasoning) data.explanation.reasoning = await translateToKannada(data.explanation.reasoning);
          }
        } catch(e) {
          console.error("Kannada translation failed", e);
        }
      }

      const assistantMsg: Message = {
        id: `ast-${Date.now()}`,
        sender: 'assistant',
        text: bubbleText,
        timestamp: new Date().toLocaleTimeString(),
        backendPayload: data,
        isStreaming: true, // Mark as streaming when first received
        isKannada: isKn,
      };

      setIsTyping(false);
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: unknown) {
      setIsTyping(false);
      let errText = 'Unable to connect to the investigation portal. Ensure backend is running.';
      if (err && typeof err === 'object') {
         if ('message' in err && (err.message as string).includes('translate')) {
           errText = 'Unable to translate the query. Please try again.';
         } else if ('response' in err) {
           const axiosErr = err as { response?: { data?: { detail?: string } } };
           errText = axiosErr.response?.data?.detail ?? errText;
         }
      }
      setError(errText);

      const errMsg: Message = {
        id: `err-${Date.now()}`,
        sender: 'assistant',
        text: errText === 'Unable to translate the query. Please try again.' ? errText : '⚠️ Search portal error. Review failure metrics below.',
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, errMsg]);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const regenerateResponse = () => {
    // Find last user message in the list
    const userMsgs = messages.filter((m) => m.sender === 'user');
    if (userMsgs.length > 0) {
      const lastQuery = userMsgs[userMsgs.length - 1].text;
      handleSend(lastQuery);
    }
  };

  const toggleDemoMode = () => {
    if (demoActive) {
      setMessages([
        {
          id: 'm-welcome',
          sender: 'assistant',
          text: t('System boot successful. KSP Sentinel AI Core initialized. Access clearance verified. I have indexed 5 active FIR files, 4 high-risk accused profiles, and real-time cellular towers. Ask about any FIR, accused profile, location, or cross-case correlation.', activeUiLang),
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
      setDemoActive(false);
      setShowSuggestions(true);
    } else {
      setMessages(demoMessages);
      setDemoActive(true);
      setShowSuggestions(false);
    }
  };

  const exportPDF = async () => {
    try {
      const activePayloads = messages.filter(m => m.backendPayload);
      let reportId = `EXP-${Date.now()}`;
      
      // Extract crime_no or report_id from payload
      if (activePayloads.length > 0) {
        const payload = activePayloads[activePayloads.length - 1].backendPayload;
        if (payload?.results && payload.results.length > 0 && payload.results[0].crime_no) {
          reportId = payload.results[0].crime_no;
        } else if (payload?.report_id) {
          reportId = payload.report_id;
        } else if (activePayloads[0].backendPayload?.results?.[0]?.crime_no) {
          reportId = activePayloads[0].backendPayload.results[0].crime_no;
        }
      }
      console.log("Export button clicked");
      console.log(`Calling POST /reports/${reportId}/export`);
      
      const postResponse = await api.post(`/reports/${reportId}/export`, { messages });
      console.log("POST response received", postResponse.data);
      
      const returnedDownloadUrl = postResponse.data.download_url;
      console.log("download_url received", returnedDownloadUrl);
      
      console.log("Starting download");
      
      // Construct full URL since the download endpoint is not under /api/v1
      const baseUrl = api.defaults.baseURL?.replace('/api/v1', '') || 'http://127.0.0.1:8000';
      const fullDownloadUrl = `${baseUrl}${returnedDownloadUrl}`;
      
      // Fetch the file as a blob to guarantee filename and handle CORS safely
      const fileResponse = await fetch(fullDownloadUrl);
      if (!fileResponse.ok) {
        throw new Error(`Failed to fetch PDF: ${fileResponse.statusText}`);
      }
      const blob = await fileResponse.blob();
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Investigation_Report_${reportId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("PDF export failed:", error);
      setError("Failed to download PDF report. Please try again.");
    }
  };

  return (
    <LangContext.Provider value={activeUiLang}>
    <div className={`premium-card flex flex-col overflow-hidden transition-all duration-300 ease-in-out ${isFullscreen ? 'w-full h-full bg-[#0B0F14] rounded-none border-0' : `relative bg-[#0B0F14] ${className}`}`}>
      {/* Workspace Header Redesign */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 bg-[#0B0F14]">
        {/* Left Side: Title & Subtitle */}
        <div className="flex items-start space-x-3">
          <Sparkles className="w-6 h-6 text-[#18D3C5] mt-1" />
          <div className="flex flex-col">
            <span className="text-sm font-bold text-white tracking-wide">AI INVESTIGATION CO-PILOT</span>
            <span className="text-xs text-neutral-500 mt-0.5 flex items-center">
              Your intelligent partner in crime investigation 
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 ml-2 animate-pulse"></span>
            </span>
          </div>
        </div>

        {/* Center: AI Co-Pilot Tab & Selectors */}
        <div className="hidden lg:flex items-center space-x-6">
          <div className="flex items-center space-x-2 bg-[#18D3C5]/10 border border-[#18D3C5]/20 px-4 py-1.5 rounded-full text-[#18D3C5] text-xs font-semibold cursor-default">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI Co-Pilot</span>
          </div>
          
          <div className="flex items-center space-x-2">
            <span className="text-xs text-neutral-500">Model:</span>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="bg-transparent border border-white/10 text-xs text-neutral-300 rounded-md px-2.5 py-1 focus:outline-none focus:border-white/20 cursor-pointer hover:bg-white/5 transition appearance-none pr-6 relative"
              style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 fill=%22none%22 viewBox=%220 0 24 24%22 stroke=%22%239ca3af%22%3E%3Cpath stroke-linecap=%22round%22 stroke-linejoin=%22round%22 stroke-width=%222%22 d=%22M19 9l-7 7-7-7%22/%3E%3C/svg%3E")', backgroundPosition: 'right 0.5rem center', backgroundRepeat: 'no-repeat', backgroundSize: '1em' }}
            >
              <option value="Llama-3.1-8B">Llama-3.1-8B</option>
              <option value="KSP-Sentinel-v3.5-Intelligence">KSP-Sentinel-v3.5</option>
              <option value="DeepSeek-R1-District">DeepSeek-R1-District</option>
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-xs text-neutral-500">Language:</span>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value as any)}
              className="bg-transparent border border-white/10 text-xs text-neutral-300 rounded-md px-2.5 py-1 focus:outline-none focus:border-white/20 cursor-pointer hover:bg-white/5 transition appearance-none pr-6 relative"
              style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 fill=%22none%22 viewBox=%220 0 24 24%22 stroke=%22%239ca3af%22%3E%3Cpath stroke-linecap=%22round%22 stroke-linejoin=%22round%22 stroke-width=%222%22 d=%22M19 9l-7 7-7-7%22/%3E%3C/svg%3E")', backgroundPosition: 'right 0.5rem center', backgroundRepeat: 'no-repeat', backgroundSize: '1em' }}
            >
              <option value="auto">Auto Detect</option>
              <option value="en">English</option>
              <option value="kn">Kannada</option>
            </select>
          </div>
        </div>

        {/* Right Side: Health, Buttons */}
        <div className="flex items-center space-x-3">
          <div className="hidden sm:flex items-center space-x-1.5 px-2 py-1 border border-white/10 rounded-full">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            <span className="text-[10px] text-neutral-400 font-medium tracking-wide">API Healthy</span>
          </div>
          
          <button
            onClick={() => {
              setMessages([messages[0]]);
              setShowSuggestions(true);
              setDemoActive(false);
            }}
            title={t("New Chat", activeUiLang)}
            className="hidden sm:flex items-center space-x-1.5 text-neutral-400 hover:text-white px-3 py-1.5 border border-white/10 hover:border-white/20 rounded-md transition cursor-pointer text-xs"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>New Chat</span>
          </button>
          
          <button
            onClick={exportPDF}
            title="Export PDF"
            className="p-1.5 text-neutral-400 border border-white/10 rounded-md hover:text-white hover:border-white/20 transition cursor-pointer"
          >
            <Download className="w-4 h-4" />
          </button>

          <button
            onClick={() => onToggleFullscreen && onToggleFullscreen()}
            title="Fullscreen"
            className="p-1.5 text-neutral-400 border border-white/10 rounded-md hover:text-white hover:border-white/20 transition cursor-pointer"
          >
             {isFullscreen ? <Minimize className="w-4 h-4" /> : <Maximize className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Message Output Workspace */}
      <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6">
        
        {/* LANDING EXPERIENCE SCREEN */}
        {messages.length === 1 && !demoActive && (
          <div className={`mx-auto animate-fadeIn ${isFullscreen ? 'space-y-8 max-w-6xl min-h-[calc(100vh-250px)] flex flex-col justify-center py-0' : 'space-y-8 max-w-5xl py-12'}`}>
            {/* Title & Banner */}
            <div className="text-center space-y-4">
              <div className="inline-flex p-4 rounded-full border border-[#18D3C5]/20 bg-[#18D3C5]/10 shadow-[0_0_30px_rgba(24,211,197,0.15)] text-[#18D3C5] mb-2">
                <Shield className="w-10 h-10 animate-pulse" />
              </div>
              <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-white font-sans uppercase">
                AI INVESTIGATION CO-PILOT
              </h1>
              {/* Dynamic Terminal Boot animation logs */}
              <div className="max-w-xl mx-auto text-xs font-mono text-emerald-400 bg-[#141A22] border border-white/10 p-5 rounded-xl text-left leading-relaxed h-[130px] flex flex-col justify-start overflow-hidden shadow-inner">
                {bootLines.map((line, idx) => (
                  <div key={idx} className="animate-fadeIn">{line}</div>
                ))}
                {bootLines.length < 5 && (
                  <div className="animate-pulse text-neutral-500">_ Accessing portal pipeline databases...</div>
                )}
              </div>
            </div>

            {/* AI Capabilities list */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="p-4 border border-neutral-850 bg-neutral-900/15 hover:border-neutral-700 hover:-translate-y-0.5 shadow-md transition duration-200 rounded-2xl space-y-2">
                <div className="flex items-center space-x-2.5 text-cyan-455 font-bold font-mono">
                  <Search className="w-4 h-4" />
                  <span className="text-xs uppercase">Crime Search</span>
                </div>
                <p className="text-xs md:text-sm text-neutral-400 leading-relaxed font-sans">
                  Query crime types, districts, stations, suspect demographics, dates, and record limits in plain English.
                </p>
              </div>

              <div className="p-4 border border-neutral-850 bg-neutral-900/15 hover:border-neutral-700 hover:-translate-y-0.5 shadow-md transition duration-200 rounded-2xl space-y-2">
                <div className="flex items-center space-x-2.5 text-purple-400 font-bold font-mono">
                  <Activity className="w-4 h-4" />
                  <span className="text-xs uppercase">Trend Forecasts</span>
                </div>
                <p className="text-xs md:text-sm text-neutral-400 leading-relaxed font-sans">
                  Inspect chronological timelines with growth curves, moving averages, and OLS regression projections.
                </p>
              </div>

              <div className="p-4 border border-neutral-850 bg-neutral-900/15 hover:border-neutral-700 hover:-translate-y-0.5 shadow-md transition duration-200 rounded-2xl space-y-2">
                <div className="flex items-center space-x-2.5 text-rose-400 font-bold font-mono">
                  <MapPin className="w-4 h-4" />
                  <span className="text-xs uppercase">Coord Hotspots</span>
                </div>
                <p className="text-xs md:text-sm text-neutral-400 leading-relaxed font-sans">
                  Assess density rankings mapping high-risk coordinate clusters directly onto scaled geolocation radars.
                </p>
              </div>

              <div className="p-4 border border-neutral-850 bg-neutral-900/15 hover:border-neutral-700 hover:-translate-y-0.5 shadow-md transition duration-200 rounded-2xl space-y-2">
                <div className="flex items-center space-x-2.5 text-emerald-455 font-bold font-mono">
                  <Database className="w-4 h-4" />
                  <span className="text-xs uppercase">Explainable Logs</span>
                </div>
                <p className="text-xs md:text-sm text-neutral-400 leading-relaxed font-sans">
                  Examine detected parameters, NLP intents, pipeline reasoning, and raw SQL queries generated in real-time.
                </p>
              </div>
            </div>

            {/* Suggested Demo Cards */}
            <div className="space-y-4 pt-3.5">
              <span className="text-xs font-mono font-bold tracking-widest text-neutral-500 uppercase block text-center">
                Choose An Investigation Pipeline
              </span>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-left">
                {/* Card 1: Search Cases */}
                <button
                  onClick={() => handleSend("Show theft in Mysuru")}
                  className="glass-panel-interactive p-4 rounded-2xl border border-neutral-850 bg-neutral-900/10 hover:border-cyan-500/30 hover:-translate-y-1 transition duration-200 cursor-pointer flex flex-col justify-between h-28 text-left group"
                >
                  <div className="flex items-center justify-between w-full">
                    <Search className="w-5 h-5 text-cyan-405 group-hover:scale-110 transition duration-200" />
                    <span className="text-xs font-mono text-neutral-550">Pipeline 01</span>
                  </div>
                  <div>
                    <span className="block text-xs font-bold text-white uppercase tracking-wide font-mono">Case Registry Search</span>
                    <span className="block text-xs font-mono text-neutral-450 mt-1 truncate">Show theft in Mysuru</span>
                  </div>
                </button>

                {/* Card 2: Analytics Trend */}
                <button
                  onClick={() => handleSend("Crime trend in Bengaluru Urban")}
                  className="glass-panel-interactive p-4 rounded-2xl border border-neutral-850 bg-neutral-900/10 hover:border-purple-500/30 hover:-translate-y-1 transition duration-200 cursor-pointer flex flex-col justify-between h-28 text-left group"
                >
                  <div className="flex items-center justify-between w-full">
                    <BarChart3 className="w-5 h-5 text-purple-400 group-hover:scale-110 transition duration-200" />
                    <span className="text-xs font-mono text-neutral-550">Pipeline 02</span>
                  </div>
                  <div>
                    <span className="block text-xs font-bold text-white uppercase tracking-wide font-mono">Caseload Trend</span>
                    <span className="block text-xs font-mono text-neutral-455 mt-1 truncate">Crime trend in Bengaluru</span>
                  </div>
                </button>

                {/* Card 3: Geolocation Hotspots */}
                <button
                  onClick={() => handleSend("Top hotspots")}
                  className="glass-panel-interactive p-4 rounded-2xl border border-neutral-850 bg-neutral-900/10 hover:border-rose-500/30 hover:-translate-y-1 transition duration-200 cursor-pointer flex flex-col justify-between h-28 text-left group"
                >
                  <div className="flex items-center justify-between w-full">
                    <MapPin className="w-5 h-5 text-rose-400 group-hover:scale-110 transition duration-200" />
                    <span className="text-xs font-mono text-neutral-550">Pipeline 03</span>
                  </div>
                  <div>
                    <span className="block text-xs font-bold text-white uppercase tracking-wide font-mono">Radar Hotspots</span>
                    <span className="block text-xs font-mono text-neutral-455 mt-1 truncate">Top hotspots</span>
                  </div>
                </button>

                {/* Card 4: Crime Prediction */}
                <button
                  onClick={() => handleSend("Predict theft next month in Mysuru")}
                  className="glass-panel-interactive p-4 rounded-2xl border border-neutral-850 bg-neutral-900/10 hover:border-emerald-500/30 hover:-translate-y-1 transition duration-200 cursor-pointer flex flex-col justify-between h-28 text-left group"
                >
                  <div className="flex items-center justify-between w-full">
                    <Shield className="w-5 h-5 text-emerald-450 group-hover:scale-110 transition duration-200" />
                    <span className="text-xs font-mono text-neutral-550">Pipeline 04</span>
                  </div>
                  <div>
                    <span className="block text-xs font-bold text-white uppercase tracking-wide font-mono">Caseload Forecast</span>
                    <span className="block text-xs font-mono text-neutral-455 mt-1 truncate">Predict theft next month</span>
                  </div>
                </button>
              </div>
            </div>

            {/* Demo mode quick trigger card */}
            <div className="p-5 border border-rose-500/20 bg-rose-950/5 rounded-2xl flex items-center justify-between shadow-[0_0_15px_rgba(244,63,94,0.02)]">
              <div className="space-y-1.5 pr-4">
                <span className="text-sm font-bold text-white uppercase block font-mono">
                  ⚡ Judge Assistant Mode
                </span>
                <p className="text-xs md:text-sm text-neutral-400 leading-relaxed font-sans max-w-xl">
                  Click to pre-populate the screen with ready-to-present maps, trends, predictions, and query explainers.
                </p>
              </div>
              <button
                onClick={toggleDemoMode}
                className="px-5 py-2.5 border border-rose-500/35 bg-rose-950/20 text-rose-400 hover:bg-rose-950 hover:text-white transition rounded-xl font-mono text-xs font-bold shadow-[0_0_10px_rgba(244,63,94,0.15)] cursor-pointer"
              >
                Start Demo Session
              </button>
            </div>
          </div>
        )}

        {/* MESSAGES LISTING */}
        <ErrorBoundary>
        {(messages.length > 1 || demoActive) && messages.map((msg) => {
          const isUser = msg.sender === 'user';
          // Mock time format for redesign
          const timeString = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

          return (
            <div
              key={msg.id}
              className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'} animate-fadeIn mb-6`}
            >
              <div className={`flex items-start max-w-[85%] md:max-w-[75%] ${isUser ? 'flex-row-reverse' : 'flex-row'} space-x-4`}>
                
                {/* Avatar Icon */}
                {!isUser && (
                  <div className="w-9 h-9 rounded-full border border-[#18D3C5]/30 bg-[#18D3C5]/10 flex items-center justify-center text-[#18D3C5] flex-shrink-0 mt-1 mr-4">
                    <Sparkles className="w-4 h-4" />
                  </div>
                )}

                {/* Message Bubble/Card */}
                <div
                  className={`p-5 rounded-2xl flex flex-col space-y-3 shadow-md ${
                    isUser
                      ? 'bg-[#152C2D] text-white rounded-tr-sm border border-[#18D3C5]/10 ml-4'
                      : 'bg-[#141A22] text-neutral-200 rounded-tl-sm border border-white/5'
                  }`}
                >
                  <div className="font-sans leading-relaxed text-[15px] whitespace-pre-wrap">
                    {!isUser && msg.isStreaming ? (
                      <StreamedText
                        text={msg.id === 'm-welcome' ? t(msg.text, activeUiLang) : msg.text}
                        onUpdate={() => messagesEndRef.current?.scrollIntoView({ behavior: 'auto' })}
                        onComplete={() => { msg.isStreaming = false; }}
                      />
                    ) : (
                      <span>{msg.id === 'm-welcome' ? t(msg.text, activeUiLang) : msg.text}</span>
                    )}
                  </div>

                  {/* Backend Cards (AI Only) */}
                  {msg.backendPayload && (
                    <div className="mt-4">
                      <IntentResponseBlock payload={msg.backendPayload} onQueryAction={handleSend} />
                    </div>
                  )}

                  {/* Metadata Footer */}
                  <div className={`flex items-center space-x-2 text-[11px] font-medium text-neutral-500 pt-2 ${isUser ? 'justify-end' : 'justify-between'}`}>
                    {!isUser && msg.backendPayload && (
                      <button
                        onClick={() => setActiveDrawerPayload(msg.backendPayload || null)}
                        className="flex items-center space-x-1 hover:text-[#18D3C5] transition cursor-pointer px-2 py-1 rounded-md hover:bg-[#18D3C5]/10 border border-transparent hover:border-[#18D3C5]/20"
                        title="View Developer Info"
                      >
                        <Info className="w-3.5 h-3.5" />
                        <span>Info</span>
                      </button>
                    )}
                    <div className="flex items-center space-x-2">
                      <span>{timeString}</span>
                      {isUser && <CheckCheck className="w-3.5 h-3.5 text-[#18D3C5]" />}
                    </div>
                  </div>
                </div>

              </div>
            </div>
          );
        })}
        </ErrorBoundary>

        {/* AI Typing Indicator */}
        {isTyping && <LoadingSkeleton stage={loadingStage} />}

        {/* Global error banner */}
        {error && <ErrorAlert message={error} onRetry={() => regenerateResponse()} />}

        <div ref={messagesEndRef} />
      </div>

      {/* Developer Mode Drawer */}
      {activeDrawerPayload && (
        <>
          <div 
            className="absolute inset-0 bg-black/50 z-40 animate-in fade-in duration-300"
            onClick={() => setActiveDrawerPayload(null)}
          />
          <div className="absolute top-0 right-0 bottom-0 w-full max-w-md bg-[#0B0F14] border-l border-white/10 shadow-2xl z-50 flex flex-col animate-in slide-in-from-right duration-300">
            <div className="flex items-center justify-between p-5 border-b border-white/10 bg-[#141A22]">
              <div className="flex items-center space-x-2">
                <Database className="w-5 h-5 text-[#18D3C5]" />
                <h3 className="text-white font-semibold tracking-wide font-sans">Developer Inspector</h3>
              </div>
              <button 
                onClick={() => setActiveDrawerPayload(null)}
                className="text-neutral-400 hover:text-white transition p-1 rounded-md hover:bg-white/10"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-5 space-y-6">
              {/* Metadata Overview */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-[#141A22] border border-white/5 p-3 rounded-xl flex flex-col">
                  <span className="text-[10px] text-neutral-500 uppercase tracking-wider font-bold mb-1">Intent</span>
                  <span className="text-xs text-white font-mono">{activeDrawerPayload.intent || (activeDrawerPayload.explanation?.intent)}</span>
                </div>
                <div className="bg-[#141A22] border border-white/5 p-3 rounded-xl flex flex-col">
                  <span className="text-[10px] text-neutral-500 uppercase tracking-wider font-bold mb-1">Confidence</span>
                  <span className="text-xs text-[#18D3C5] font-mono">{activeDrawerPayload.explanation?.confidence ? (activeDrawerPayload.explanation.confidence * 100).toFixed(1) : '100.0'}%</span>
                </div>
                <div className="bg-[#141A22] border border-white/5 p-3 rounded-xl flex flex-col col-span-2">
                  <span className="text-[10px] text-neutral-500 uppercase tracking-wider font-bold mb-1">Execution Time</span>
                  <span className="text-xs text-emerald-400 font-mono">{activeDrawerPayload.metadata?.query_time_ms || 0}ms</span>
                </div>
              </div>

              {/* Filters */}
              {activeDrawerPayload.explanation?.filters && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-neutral-400 uppercase tracking-wider">Applied Filters</h4>
                  <div className="flex flex-wrap gap-2">
                    {(Array.isArray(activeDrawerPayload.explanation.filters) 
                      ? activeDrawerPayload.explanation.filters 
                      : [String(activeDrawerPayload.explanation.filters)]
                    ).map((f: string, i: number) => (
                      <span key={i} className="px-2 py-1 rounded border border-cyan-500/30 bg-cyan-950/40 text-cyan-400 text-[10px] font-mono shadow-[0_0_8px_rgba(6,182,212,0.1)]">
                        {f}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* SQL Query */}
              {activeDrawerPayload.explanation?.sql_summary && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-neutral-400 uppercase tracking-wider">Executed SQL</h4>
                  <div className="bg-neutral-950 border border-white/5 p-4 rounded-xl relative group">
                    <pre className="text-xs font-mono text-cyan-400 overflow-x-auto whitespace-pre-wrap">{activeDrawerPayload.explanation.sql_summary}</pre>
                  </div>
                </div>
              )}

              {/* Raw JSON */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-neutral-400 uppercase tracking-wider">Raw JSON Payload</h4>
                <div className="bg-neutral-950 border border-white/5 p-4 rounded-xl relative group">
                  <pre className="text-[10px] font-mono text-neutral-400 overflow-x-auto whitespace-pre-wrap">
                    {JSON.stringify(activeDrawerPayload, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Suggestions and Input bar */}
      <div className="relative pt-2 pb-6 px-4 md:px-8 bg-transparent">
        {/* Suggestion Chips */}
        {showSuggestions && messages.length === 1 && !demoActive && (
          <div className="mb-4 flex flex-wrap gap-2 justify-center">
            {suggestedQueries.crimeSearch.slice(0, 1).concat(suggestedQueries.analytics.slice(0, 1)).concat(suggestedQueries.prediction).concat(suggestedQueries.hotspots).map((pill: string, idx: number) => (
              <button
                key={idx}
                onClick={() => handleSend(pill)}
                className={`rounded-full border border-white/10 bg-white/5 text-neutral-300 hover:text-[#18D3C5] hover:border-[#18D3C5]/30 transition cursor-pointer font-sans text-xs px-4 py-2 hover:bg-white/10`}
              >
                {pill}
              </button>
            ))}
          </div>
        )}

        {/* Input Box Redesign */}
        <div className="max-w-4xl mx-auto">
          <div className="relative rounded-2xl border border-white/10 bg-[#0B0F14] focus-within:border-[#18D3C5]/40 focus-within:shadow-[0_0_15px_rgba(24,211,197,0.15)] transition duration-300">
            <textarea
              rows={1}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={t("Ask about any FIR, accused, location, or crime pattern...", activeUiLang)}
              className="w-full pl-5 pr-36 bg-transparent text-neutral-200 focus:outline-none resize-none placeholder:text-neutral-500 font-sans leading-relaxed py-4 text-sm md:text-base pt-5"
            />
            
            {/* Input Footer Icons */}
            <div className="flex items-center justify-between px-4 pb-3">
              {/* Left Icons */}
              <div className="flex items-center space-x-3 text-neutral-500">
                <button className="hover:text-white transition cursor-pointer p-1"><Paperclip className="w-4 h-4" /></button>
                <button className="flex items-center space-x-1 hover:text-white transition cursor-pointer p-1"><Calendar className="w-4 h-4" /><span className="text-[10px] uppercase font-bold tracking-wider hidden sm:block">Date</span></button>
                <button className="flex items-center space-x-1 hover:text-white transition cursor-pointer p-1"><MapPin className="w-4 h-4" /><span className="text-[10px] uppercase font-bold tracking-wider hidden sm:block">Location</span></button>
                <button className="flex items-center space-x-1 hover:text-white transition cursor-pointer p-1"><Filter className="w-4 h-4" /><span className="text-[10px] uppercase font-bold tracking-wider hidden sm:block">Filters</span></button>
              </div>

              {/* Right Icons */}
              <div className="flex items-center space-x-2 relative">
                {micError && (
                  <span className="absolute -top-8 right-0 text-[10px] text-rose-500 font-mono tracking-wide px-2 bg-rose-500/10 rounded border border-rose-500/20 whitespace-nowrap">
                    {micError}
                  </span>
                )}
                <button
                  onClick={toggleMicrophone}
                  title={micState === 'listening' ? t('Stop Listening', activeUiLang) : t('Voice Query', activeUiLang)}
                  className={`p-2 rounded-full transition cursor-pointer ${
                    micState === 'listening' 
                      ? 'text-rose-400 bg-rose-500/10 animate-pulse'
                      : micState === 'error'
                      ? 'text-rose-500 hover:text-rose-400'
                      : 'text-neutral-400 hover:text-white hover:bg-white/5'
                  }`}
                >
                  {micState === 'listening' ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                </button>
                <button
                  onClick={() => handleSend()}
                  disabled={!inputValue.trim() || isTyping}
                  className="p-2 rounded-lg bg-[#18D3C5] hover:bg-[#15B0A4] text-[#0B0F14] disabled:opacity-50 disabled:cursor-not-allowed transition shadow-[0_0_10px_rgba(24,211,197,0.2)]"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
          
          {/* Subtext */}
          <div className="flex items-center justify-between mt-3 px-2 text-[10px] text-neutral-500 font-medium">
            <span>Examples: Show theft in Mysuru • Open FIR KSP-000347 • Show murder cases last month</span>
            <span>Press / for shortcuts</span>
          </div>
        </div>
      </div>
    </div>
    </LangContext.Provider>
  );
}
