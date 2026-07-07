import { Shield, Activity, Cpu, Sparkles, Target, Zap, Clock } from 'lucide-react';
import { memo } from 'react';

const MissionIntelligencePanel = memo(function MissionIntelligencePanel({ onQuerySelect }: { onQuerySelect: (query: string) => void }) {
  const alerts = [
    { text: "Suspicious fund transfer detected (Account ending 8992)", time: "Just now", level: "critical" },
    { text: "New FIR matches known syndicate signature", time: "12m ago", level: "high" },
    { text: "CCTV anomaly identified near MG Road", time: "1h ago", level: "critical" },
    { text: "Social media sentiment spike in Zone 4", time: "2h ago", level: "medium" },
    { text: "Repeat offender spotted in Koramangala", time: "3h ago", level: "high" },
  ];

  return (
    <aside className="h-full flex flex-col justify-between break-inside-avoid mb-6">
      <div className="premium-card p-5 flex-1 overflow-y-auto space-y-6">
        
        {/* Header */}
        <div className="flex items-center space-x-3 pb-3 border-b border-neutral-800/80 sticky top-0 bg-[#0c0c0e]/95 backdrop-blur z-20 pt-1 -mt-1">
          <Cpu className="w-[18px] h-[18px] text-cyan-400" />
          <span className="text-[13px] font-sans font-semibold tracking-wide text-white">
            Mission Control
          </span>
        </div>

        {/* Mission Brief */}
        <div className="p-4 rounded-xl border border-neutral-800/60 bg-gradient-to-br from-neutral-900/40 to-[#0c0c0e]">
          <span className="flex items-center text-[10px] font-mono text-cyan-500 uppercase tracking-widest mb-2.5">
            <Clock className="w-3 h-3 mr-1.5" /> Today's Mission Brief
          </span>
          <p className="text-[13px] text-neutral-300 leading-relaxed font-sans mb-3">
            System has flagged unusual volume of cyber extortion FIRs across East Zone. 
            Pattern strongly correlates with <span className="text-white font-medium">Rajesh Gowda Syndicate</span>.
          </p>
          <div className="flex items-center space-x-2">
            <span className="px-2 py-0.5 rounded border border-rose-500/20 bg-rose-500/10 text-rose-400 text-[10px] font-mono font-medium">CRITICAL ALERT</span>
            <span className="px-2 py-0.5 rounded border border-emerald-500/20 bg-emerald-500/10 text-emerald-400 text-[10px] font-mono font-medium">ACTION REQUIRED</span>
          </div>
        </div>

        {/* AI Recommendations */}
        <div className="space-y-2">
          <span className="block text-[10px] font-mono text-neutral-500 uppercase tracking-widest mb-3 flex items-center">
            <Target className="w-[14px] h-[14px] mr-1.5 opacity-70" /> AI Recommendations
          </span>
          <div className="p-3.5 rounded-xl border border-cyan-500/20 bg-cyan-950/10 hover:border-cyan-500/40 transition-colors cursor-pointer" onClick={() => onQuerySelect("Deploy Cyber Task Force to East Zone")}>
            <div className="flex items-start space-x-3">
              <Zap className="w-4 h-4 text-cyan-400 mt-0.5" />
              <div>
                <span className="block text-[13px] font-medium text-white mb-1">Deploy Task Force</span>
                <span className="block text-[11px] text-neutral-400 font-sans leading-snug">
                  Immediate deployment to East Zone recommended to intercept ongoing syndicate operation.
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Threat Level & AI Confidence Grid */}
        <div className="grid grid-cols-2 gap-4">
          <div className="p-3.5 rounded-xl border border-rose-500/10 bg-rose-500/5">
            <span className="block text-[10px] font-sans font-medium text-neutral-400 uppercase tracking-widest mb-1.5 flex items-center">
              <Shield className="w-[14px] h-[14px] mr-1.5 text-rose-400 opacity-80" /> Threat Level
            </span>
            <span className="block text-xl font-bold text-rose-400 tracking-tight">ELEVATED</span>
          </div>
          <div className="p-3.5 rounded-xl border border-cyan-500/10 bg-cyan-500/5">
            <span className="block text-[10px] font-sans font-medium text-neutral-400 uppercase tracking-widest mb-1.5 flex items-center">
              <Sparkles className="w-[14px] h-[14px] mr-1.5 text-cyan-400 opacity-80" /> AI Confidence
            </span>
            <span className="block text-xl font-bold text-cyan-400 tracking-tight">92.4%</span>
          </div>
        </div>

        {/* Live Intelligence Feed */}
        <div className="flex-1 min-h-0 flex flex-col">
          <div className="sticky top-[48px] bg-[#0c0c0e]/95 backdrop-blur z-10 pb-2 mb-2 border-b border-neutral-800/40">
            <span className="flex items-center text-[10px] font-mono text-neutral-500 uppercase tracking-widest pt-2">
              <Activity className="w-[14px] h-[14px] mr-1.5 opacity-70" /> Live Intelligence Feed
            </span>
          </div>
          <div className="space-y-2 overflow-y-auto pr-2 pb-4 flex-1 custom-scrollbar">
            {alerts.map((alert, idx) => (
              <div key={idx} className="flex items-start space-x-3 p-3.5 rounded-xl border border-neutral-800/40 bg-neutral-900/20 hover:bg-neutral-800/30 transition-colors group">
                <div className={`mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                  alert.level === 'critical' ? 'bg-rose-500 animate-pulse' : 
                  alert.level === 'high' ? 'bg-amber-500' : 'bg-cyan-500'
                }`} />
                <div className="flex-1 min-w-0">
                  <p className="text-[12.5px] text-neutral-300 font-medium leading-snug group-hover:text-white transition-colors">{alert.text}</p>
                  <span className="text-[10px] font-mono text-neutral-500 block mt-1.5 opacity-70">{alert.time}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </aside>
  );
});

export default MissionIntelligencePanel;
