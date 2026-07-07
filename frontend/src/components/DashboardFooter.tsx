import { memo } from 'react';
import { Search, Map, Shield, Folder, Users, FileSearch, ArrowRight, History } from 'lucide-react';
import { mockRecentSearches } from '../mockData';

const DashboardFooter = memo(function DashboardFooter({ onQuerySelect }: { onQuerySelect: (query: string) => void }) {
  const recentInvestigations = [
    { title: 'Rajesh Gowda Syndicate', date: 'Started: Aug 12', status: 'Active', progress: 75, phase: 'Evidence Gathering' },
    { title: 'Operation Nightfall', date: 'Started: Aug 10', status: 'Monitoring', progress: 40, phase: 'Surveillance' },
    { title: 'Cyber Extortion Ring', date: 'Started: Aug 05', status: 'Closed', progress: 100, phase: 'Resolved' },
  ];

  const quickLinks = [
    { label: 'Crime Map', icon: Map, color: 'text-cyan-400', bg: 'bg-cyan-500/10 border-cyan-500/20' },
    { label: 'Suspect Database', icon: Users, color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20' },
    { label: 'Threat Intel', icon: Shield, color: 'text-rose-400', bg: 'bg-rose-500/10 border-rose-500/20' },
    { label: 'Case Files', icon: Folder, color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/20' }
  ];

  return (
    <>
      
      {/* Active Investigations - span 5 */}
      <div className="premium-card p-4 h-full flex flex-col break-inside-avoid mb-6">
        <div className="flex items-center space-x-3 pb-3 border-b border-neutral-800/80 mb-4">
          <FileSearch className="w-[18px] h-[18px] text-indigo-400" />
          <span className="text-[13px] font-sans font-semibold tracking-wide text-white">
            Recent Investigations
          </span>
        </div>
        <div className="space-y-3">
          {recentInvestigations.map((inv, idx) => (
            <div key={idx} className="flex flex-col justify-between p-3.5 rounded-xl border border-neutral-800/40 bg-neutral-900/20 hover:bg-neutral-800/60 transition-colors duration-300 cursor-pointer group">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <span className="block text-[13px] font-medium text-neutral-200 group-hover:text-cyan-400 transition-colors">{inv.title}</span>
                  <span className="text-[11px] font-mono text-neutral-500 block mt-1">{inv.date}</span>
                </div>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                  inv.status === 'Active' ? 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10' :
                  inv.status === 'Monitoring' ? 'text-amber-400 border-amber-500/30 bg-amber-500/10' :
                  'text-neutral-400 border-neutral-700 bg-neutral-800'
                }`}>
                  {inv.status}
                </span>
              </div>
              
              {/* Progress Bar */}
              <div className="mt-2">
                <div className="flex justify-between items-end mb-1.5">
                  <span className="text-[10px] font-mono text-cyan-500 uppercase tracking-widest">{inv.phase}</span>
                  <span className="text-[10px] font-mono text-neutral-400">{inv.progress}%</span>
                </div>
                <div className="h-1.5 w-full bg-neutral-800/80 rounded-full overflow-hidden">
                  <div 
                    className={`h-full rounded-full ${
                      inv.status === 'Active' ? 'bg-emerald-500' :
                      inv.status === 'Monitoring' ? 'bg-amber-500' : 'bg-neutral-500'
                    }`}
                    style={{ width: `${inv.progress}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Access - span 4 */}
      <div className="premium-card p-4 h-full flex flex-col break-inside-avoid mb-6">
        <div className="flex items-center space-x-3 pb-3 border-b border-neutral-800/80 mb-4">
          <ArrowRight className="w-[18px] h-[18px] text-emerald-400" />
          <span className="text-[13px] font-sans font-semibold tracking-wide text-white">
            Quick Access
          </span>
        </div>
        <div className="grid grid-cols-2 gap-3">
          {quickLinks.map((link, idx) => (
            <button key={idx} className={`premium-button group flex-col ${link.bg.replace('bg-', 'hover:bg-').replace('border-', 'hover:border-')}`}>
              <link.icon className={`w-[22px] h-[22px] mb-2.5 ${link.color} group-hover:scale-110 transition-transform duration-300`} />
              <span className="text-[12px] font-medium text-neutral-300 tracking-tight">{link.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Recent Intelligence Searches - span 3 */}
      <div className="premium-card p-4 h-full flex flex-col break-inside-avoid mb-6">
        <div className="flex items-center space-x-3 pb-3 border-b border-neutral-800/80 mb-4">
          <History className="w-[18px] h-[18px] text-neutral-500" />
          <span className="text-[13px] font-sans font-semibold tracking-wide text-white">
            Recent Intelligence Searches
          </span>
        </div>
        <div className="flex flex-wrap gap-2.5">
          {mockRecentSearches.map((search, idx) => (
            <button
              key={idx}
              onClick={() => onQuerySelect(search)}
              className="flex items-center space-x-2 px-3 py-1.5 rounded-full border border-neutral-800/60 bg-neutral-900/30 text-[12px] text-neutral-400 hover:text-cyan-400 hover:border-cyan-500/40 hover:bg-neutral-800 transition-all duration-300 cursor-pointer shadow-sm hover:shadow-[0_2px_8px_rgba(6,182,212,0.15)]"
            >
              <Search className="w-3.5 h-3.5 text-neutral-500 group-hover:text-cyan-500" />
              <span className="tracking-tight">{search}</span>
            </button>
          ))}
        </div>
      </div>

    </>
  );
});

export default DashboardFooter;
