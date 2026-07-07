import { useState, memo } from 'react';
import { MapPin, Search, UserX, Phone, EyeOff, Eye } from 'lucide-react';
import { mockAccused } from '../mockData';
import type { Accused } from '../types';

interface DossierViewProps {
  searchFilter?: string;
}

const DossierView = memo(function DossierView({ searchFilter = '' }: DossierViewProps) {
  const [searchQuery, setSearchQuery] = useState(searchFilter);
  const [selectedAccused, setSelectedAccused] = useState<Accused | null>(null);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'In Custody':
        return 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
      case 'Under Trial':
        return 'bg-blue-500/10 text-blue-400 border border-blue-500/20';
      case 'Released':
        return 'bg-neutral-500/10 text-neutral-400 border border-neutral-500/20';
      default: // At Large
        return 'bg-rose-500/10 text-rose-400 border border-rose-500/20 status-indicator';
    }
  };

  const getRiskColor = (score: number) => {
    if (score >= 85) return 'bg-rose-500 text-rose-500';
    if (score >= 70) return 'bg-amber-500 text-amber-500';
    return 'bg-cyan-500 text-cyan-500';
  };

  const filteredAccused = mockAccused.filter(acc => 
    acc.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
    acc.primaryOffense.toLowerCase().includes(searchQuery.toLowerCase()) || 
    acc.lastKnownLocation.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Search Header */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pb-4 border-b border-neutral-900">
        <div>
          <span className="block text-xs font-mono text-neutral-500 uppercase tracking-widest">
            KSP Biometric Operations
          </span>
          <h2 className="text-2xl font-bold text-white m-0">Accused Dossiers Database</h2>
        </div>

        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3.5 top-3 w-4 h-4 text-neutral-500" />
          <input
            type="text"
            placeholder="Search dossiers by name, offence..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-neutral-900 border border-neutral-850 text-sm rounded-lg text-neutral-200 focus:outline-none focus:border-cyan-500/50 focus:shadow-[0_0_12px_rgba(6,182,212,0.08)]"
          />
        </div>
      </div>

      {/* Dossier Analytics KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel p-4 rounded-xl border border-neutral-800 bg-neutral-950/60">
          <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider block mb-1">Most Wanted Targets</span>
          <span className="text-2xl font-bold text-rose-500 block">24</span>
          <span className="text-[10px] text-rose-400 mt-1 block">High-priority intercepts</span>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-neutral-800 bg-neutral-950/60">
          <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider block mb-1">Arrest Status</span>
          <span className="text-2xl font-bold text-cyan-400 block">45%</span>
          <span className="text-[10px] text-neutral-400 mt-1 block">In Custody / Under Trial</span>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-neutral-800 bg-neutral-950/60">
          <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider block mb-1">Risk Distribution</span>
          <span className="text-2xl font-bold text-amber-500 block">68</span>
          <span className="text-[10px] text-amber-400 mt-1 block">Avg threat score index</span>
        </div>
        <div className="glass-panel p-4 rounded-xl border border-neutral-800 bg-neutral-950/60">
          <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider block mb-1">Threat Summary</span>
          <span className="text-2xl font-bold text-emerald-400 block">Stable</span>
          <span className="text-[10px] text-emerald-400/80 mt-1 block">No new syndicated activity</span>
        </div>
      </div>

      {/* Main Grid View */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredAccused.map((acc, index) => {
          const isSelected = selectedAccused?.id === acc.id;
          return (
            <div
              key={acc.id}
              className={`glass-panel-interactive rounded-2xl border transition-all duration-300 overflow-hidden flex flex-col justify-between animate-slide-up ${
                isSelected ? 'border-cyan-500/50 ring-1 ring-cyan-500/20 bg-neutral-900/60 shadow-[0_0_15px_rgba(6,182,212,0.15)]' : 'border-neutral-800 bg-neutral-950/40 hover:-translate-y-1 hover:border-neutral-700'
              }`}
              style={{ animationDelay: `${index * 50}ms` }}
            >
              {/* Card Header Profile Banner */}
              <div className="p-5 border-b border-neutral-900 bg-neutral-900/10 flex items-start space-x-4">
                {/* Visual Avatar Placeholder with matching color depending on risk */}
                <div className={`w-16 h-16 rounded-lg bg-neutral-900 border flex flex-col items-center justify-center relative overflow-hidden flex-shrink-0 ${
                  acc.status === 'At Large' ? 'border-rose-500/20' : 'border-neutral-800'
                }`}>
                  <UserX className={`w-8 h-8 ${acc.status === 'At Large' ? 'text-rose-500' : 'text-neutral-500'}`} />
                  {/* Fingerprint match indicator overlay */}
                  <div className="absolute bottom-0 left-0 right-0 bg-neutral-950/80 border-t border-neutral-900 text-[9px] font-mono text-center text-cyan-400 py-0.5">
                    BIOMETRIC: {acc.biometricsMatch}%
                  </div>
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="text-base font-bold text-white truncate block max-w-[70%]">
                      {acc.name}
                    </span>
                    <span className="text-xs font-mono text-neutral-500">AGE: {acc.age}</span>
                  </div>
                  <span className="block text-sm text-neutral-450 truncate mt-1">
                    {acc.primaryOffense}
                  </span>
                  <div className="mt-2.5 flex items-center">
                    <span className={`text-xs font-mono font-semibold px-2.5 py-1 rounded-full ${getStatusBadge(acc.status)}`}>
                      {acc.status}
                    </span>
                  </div>
                </div>
              </div>

              {/* Card stats */}
              <div className="p-5 space-y-4 flex-1">
                {/* Threat Index Level */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-neutral-500">SENTINEL RISK ANALYSIS:</span>
                    <span className="font-bold text-white">{acc.riskScore}% THREAT</span>
                  </div>
                  {/* Progress bar */}
                  <div className="w-full bg-neutral-900 h-1.5 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${getRiskColor(acc.riskScore)}`}
                      style={{ width: `${acc.riskScore}%` }}
                    />
                  </div>
                </div>

                <div className="space-y-1.5 text-sm font-sans text-neutral-350">
                  <div className="flex items-center text-neutral-400">
                    <MapPin className="w-4 h-4 text-neutral-500 mr-2 flex-shrink-0" />
                    <span className="truncate">Last Geo: {acc.lastKnownLocation}</span>
                  </div>
                  <div className="flex items-center text-neutral-400">
                    <Phone className="w-4 h-4 text-neutral-500 mr-2 flex-shrink-0" />
                    <span className="truncate">{acc.phoneNumbers.join(', ')}</span>
                  </div>
                </div>
              </div>

              {/* Card Actions */}
              <div className="p-4 border-t border-neutral-900 bg-neutral-950/40 flex items-center justify-between">
                <span className="text-xs font-mono text-neutral-500">SYS_ID: {acc.id.toUpperCase()}</span>
                <button
                  onClick={() => setSelectedAccused(isSelected ? null : acc)}
                  className="inline-flex items-center space-x-1.5 px-4 py-2 border border-neutral-800 hover:border-cyan-500/50 hover:bg-neutral-900 hover:shadow-[0_0_8px_rgba(6,182,212,0.15)] bg-neutral-900 rounded-lg text-sm font-mono text-neutral-400 hover:text-cyan-400 transition cursor-pointer"
                >
                  {isSelected ? (
                    <>
                      <EyeOff className="w-4 h-4" />
                      <span>HIDE INSIGHT</span>
                    </>
                  ) : (
                    <>
                      <Eye className="w-4 h-4" />
                      <span>INSPECT DOSSIER</span>
                    </>
                  )}
                </button>
              </div>

              {/* Detailed dossier summary overlay inside card container */}
              {isSelected && (
                <div className="p-5 bg-black/60 border-t border-cyan-500/20 text-sm font-sans text-neutral-300 space-y-4">
                  <div>
                    <span className="block text-[11px] font-mono text-cyan-400 uppercase font-bold tracking-wider mb-1">
                      Intelligence Brief Logs
                    </span>
                    <p className="leading-relaxed text-sm text-neutral-400">{acc.notes}</p>
                  </div>

                  <div>
                    <span className="block text-[11px] font-mono text-cyan-400 uppercase font-bold tracking-wider mb-2">
                      Known Associates
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {acc.associates.map((assoc, idx) => (
                        <span
                          key={idx}
                          className="px-2.5 py-1 rounded bg-neutral-900 border border-neutral-850 text-xs text-neutral-350"
                        >
                          {assoc}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div>
                    <span className="block text-[11px] font-mono text-cyan-400 uppercase font-bold tracking-wider mb-2">
                      Active Database Linkages
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {acc.networkConnections.map((link, idx) => (
                        <span
                          key={idx}
                          className="px-2.5 py-1 rounded bg-cyan-950/20 border border-cyan-500/10 text-xs font-mono text-cyan-400"
                        >
                          {link}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
});

export default DossierView;
