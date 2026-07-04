import { FileText, Calendar, Eye, Activity, Bell } from 'lucide-react';
import { mockFIRs, mockAlerts, mockCourtHearings } from '../mockData';
import type { FIR } from '../types';

interface BottomSectionProps {
  onSelectFIR: (fir: FIR) => void;
  onSelectSearch: (query: string) => void;
}

export default function BottomSection({ onSelectFIR, onSelectSearch }: BottomSectionProps) {
  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'Critical':
        return 'text-rose-400 bg-rose-500/10 border border-rose-500/20';
      case 'High':
        return 'text-amber-400 bg-amber-500/10 border border-amber-500/20';
      case 'Medium':
        return 'text-blue-400 bg-blue-500/10 border border-blue-500/20';
      default:
        return 'text-neutral-400 bg-neutral-500/10 border border-neutral-500/20';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Closed':
        return 'text-emerald-400 bg-emerald-500/10 border border-emerald-500/25';
      case 'Open':
        return 'text-indigo-400 bg-indigo-500/10 border border-indigo-500/25';
      default: // Investigation / Under Review
        return 'text-cyan-400 bg-cyan-500/10 border border-cyan-500/25';
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Recent FIR Table - Span 2 */}
      <div className="glass-panel rounded-2xl border border-neutral-800 bg-neutral-950/60 p-4 lg:col-span-2 overflow-hidden flex flex-col justify-between">
        <div className="flex items-center justify-between pb-3 border-b border-neutral-900">
          <div className="flex items-center space-x-2">
            <FileText className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-mono font-bold tracking-wider text-white uppercase">
              Recent First Information Reports (FIR)
            </span>
          </div>
          <span className="text-[10px] font-mono text-neutral-500 uppercase">
            LIVE SYNC • ACTIVE DISTRICT
          </span>
        </div>

        {/* Scrollable table container */}
        <div className="overflow-x-auto mt-4">
          <table className="w-full text-left text-xs font-sans">
            <thead>
              <tr className="border-b border-neutral-900 text-neutral-500 font-mono uppercase text-[10px] tracking-wider">
                <th className="py-2.5 px-3">FIR ID</th>
                <th className="py-2.5 px-3">Classification</th>
                <th className="py-2.5 px-3">Location</th>
                <th className="py-2.5 px-3">Severity</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-900">
              {mockFIRs.map((fir) => (
                <tr
                  key={fir.id}
                  className="hover:bg-neutral-900/40 transition group"
                >
                  <td className="py-3 px-3 font-mono font-bold text-neutral-300 group-hover:text-cyan-400 transition-colors">
                    {fir.caseNumber}
                  </td>
                  <td className="py-3 px-3">
                    <div className="flex flex-col">
                      <span className="font-semibold text-neutral-200">{fir.title}</span>
                      <span className="text-[10px] font-mono text-neutral-500 mt-0.5">{fir.underSection}</span>
                    </div>
                  </td>
                  <td className="py-3 px-3 text-neutral-450 text-[11px]">
                    {fir.location}
                  </td>
                  <td className="py-3 px-3">
                    <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded-full ${getSeverityBadge(fir.severity)}`}>
                      {fir.severity}
                    </span>
                  </td>
                  <td className="py-3 px-3">
                    <span className={`text-[9px] font-mono px-2 py-0.5 rounded-full ${getStatusBadge(fir.status)}`}>
                      {fir.status}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-right">
                    <button
                      onClick={() => onSelectFIR(fir)}
                      className="inline-flex items-center space-x-1 px-2.5 py-1 border border-neutral-800 bg-neutral-900 text-[10px] font-mono text-neutral-400 hover:text-cyan-400 hover:border-cyan-500/30 rounded transition cursor-pointer"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>DOSSIER</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Right Column containing both Latest Alerts and Upcoming Court Hearings */}
      <div className="space-y-6 lg:col-span-1 flex flex-col">
        {/* Latest Alerts */}
        <div className="glass-panel rounded-2xl border border-neutral-800 bg-neutral-950/60 p-4 flex-1 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-neutral-900">
            <div className="flex items-center space-x-2">
              <Bell className="w-4 h-4 text-cyan-400 animate-pulse" />
              <span className="text-xs font-mono font-bold tracking-wider text-white uppercase">
                Active Tactical Alerts
              </span>
            </div>
            <Activity className="w-3.5 h-3.5 text-neutral-600" />
          </div>

          <div className="space-y-2.5">
            {mockAlerts.map((alert) => (
              <div
                key={alert.id}
                onClick={() => onSelectSearch(alert.text)}
                className="flex items-start p-2.5 rounded-lg border border-neutral-900 bg-neutral-950/40 hover:bg-neutral-900/60 transition cursor-pointer"
              >
                <span className={`flex h-2 w-2 relative mt-1.5 mr-2.5 flex-shrink-0`}>
                  <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                    alert.type === 'CRITICAL' ? 'bg-rose-400' :
                    alert.type === 'WARNING' ? 'bg-amber-400' :
                    'bg-cyan-400'
                  }`}></span>
                  <span className={`relative inline-flex rounded-full h-2 w-2 ${
                    alert.type === 'CRITICAL' ? 'bg-rose-500' :
                    alert.type === 'WARNING' ? 'bg-amber-500' :
                    'bg-cyan-500'
                  }`}></span>
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-neutral-300 leading-normal font-sans">
                    {alert.text}
                  </p>
                  <div className="flex items-center justify-between mt-1 text-[9px] font-mono text-neutral-500">
                    <span>{alert.timestamp}</span>
                    {alert.location && <span>TARGET APEX: {alert.location}</span>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Upcoming Court Hearings */}
        <div className="glass-panel rounded-2xl border border-neutral-800 bg-neutral-950/60 p-4 space-y-3">
          <div className="flex items-center space-x-2 pb-2 border-b border-neutral-900">
            <Calendar className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-mono font-bold tracking-wider text-white uppercase">
              UPCOMING DOCKETS
            </span>
          </div>

          <div className="space-y-2">
            {mockCourtHearings.map((hearing) => (
              <div
                key={hearing.id}
                onClick={() => onSelectSearch(hearing.accusedName)}
                className="p-2.5 rounded-lg border border-neutral-900 bg-neutral-950/40 hover:bg-neutral-900/60 transition cursor-pointer"
              >
                <div className="flex items-center justify-between text-[10px] font-mono mb-1">
                  <span className="text-cyan-400 font-bold">{hearing.caseNumber}</span>
                  <span className={`px-1.5 py-0.5 rounded text-[8px] ${
                    hearing.status === 'Scheduled' ? 'bg-indigo-950 text-indigo-400 border border-indigo-900' :
                    hearing.status === 'Completed' ? 'bg-emerald-950/30 text-emerald-400 border border-emerald-900/30' :
                    'bg-neutral-900 text-neutral-400'
                  }`}>
                    {hearing.status}
                  </span>
                </div>
                <div className="text-xs font-bold text-neutral-200">
                  {hearing.accusedName}
                </div>
                <div className="text-[10px] text-neutral-450 mt-1 font-sans">
                  {hearing.courtName}
                </div>
                <div className="text-[9px] font-mono text-neutral-500 mt-0.5">
                  {hearing.hearingDate}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
