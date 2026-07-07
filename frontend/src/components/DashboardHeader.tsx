import { memo, useState, useEffect } from 'react';

const DashboardHeader = memo(function DashboardHeader() {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-IN', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  const getShift = (date: Date) => {
    const hour = date.getHours();
    if (hour >= 6 && hour < 14) return 'MORNING SHIFT (ALPHA)';
    if (hour >= 14 && hour < 22) return 'EVENING SHIFT (BRAVO)';
    return 'NIGHT SHIFT (CHARLIE)';
  };

  return (
    <div className="sticky top-0 z-30 bg-[#0c0c0e]/95 backdrop-blur-md pb-4 border-b border-neutral-800/40 mb-2 flex flex-col md:flex-row md:items-center justify-between gap-4 pt-1">
      <div>
        <h1 className="text-[28px] font-bold tracking-tight text-white m-0 flex items-center gap-3">
          Welcome Officer,
          <span className="text-cyan-400 font-mono text-[17px] font-semibold px-2.5 py-0.5 rounded-lg bg-cyan-950/20 border border-cyan-500/20 shadow-[0_0_10px_rgba(6,182,212,0.05)]">
            INSP. VIKRAM RATHORE
          </span>
        </h1>
        <p className="flex items-center text-[13px] font-sans font-medium text-neutral-400 mt-2 tracking-wide">
          <span>District: Bengaluru Metropolitan</span>
          <span className="flex items-center mx-3 px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/20 text-rose-400 text-[10px] font-mono tracking-widest uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse mr-1.5"></span>
            Hottest Zone: East
          </span>
          <span>• {getShift(currentTime)}</span>
        </p>
      </div>
      <div className="flex items-center gap-4">
        <div className="text-right">
          <span className="block text-2xl font-mono font-bold text-white tracking-tight leading-none">{formatTime(currentTime)}</span>
          <span className="block text-[10px] font-mono text-neutral-500 uppercase tracking-widest mt-1">Local Time IST</span>
        </div>
        <div className="h-10 w-px bg-neutral-800/80 hidden sm:block" />
        <div className="group relative">
          <div className="flex items-center space-x-2.5 text-xs font-mono font-medium text-neutral-300 border border-neutral-800/60 bg-neutral-900/40 px-4 py-2 rounded-xl cursor-help transition-all hover:border-neutral-600 hover:bg-neutral-800">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
            <span className="text-neutral-400">System Health:</span>
            <span className="text-emerald-400 font-semibold">100% Operational</span>
          </div>
          
          {/* System Health Hover Widget */}
          <div className="absolute right-0 top-full mt-2 w-64 p-4 premium-card opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 translate-y-2 group-hover:translate-y-0">
            <span className="block text-[10px] font-mono text-neutral-500 uppercase tracking-widest mb-3 border-b border-neutral-800/60 pb-2">Diagnostic Overview</span>
            <div className="space-y-3">
              <div className="flex justify-between items-center text-xs">
                <span className="text-neutral-400">Core NLP Engine</span>
                <span className="text-emerald-400 font-mono">14ms ping</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-neutral-400">Crime DB Sync</span>
                <span className="text-emerald-400 font-mono">Synced</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-neutral-400">Video Analytics</span>
                <span className="text-amber-400 font-mono">Standby</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
});

export default DashboardHeader;
