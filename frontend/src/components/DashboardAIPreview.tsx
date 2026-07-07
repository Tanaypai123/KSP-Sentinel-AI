import { Brain, ArrowRight, Shield, Target, Zap, Activity, Clock, CheckCircle2 } from 'lucide-react';
import { memo } from 'react';

const DashboardAIPreview = memo(function DashboardAIPreview({ onOpenWorkspace }: { onOpenWorkspace: () => void }) {
  return (
    <div className="premium-card p-4 h-full flex flex-col justify-between scanline-overlay relative overflow-hidden min-h-[260px] break-inside-avoid mb-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 relative z-10">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-purple-500/10 rounded-lg border border-purple-500/20 shadow-[0_0_10px_rgba(168,85,247,0.2)]">
            <Brain className="w-5 h-5 text-purple-400 animate-pulse" />
          </div>
          <div>
            <h2 className="text-[15px] font-sans font-bold text-white tracking-wide leading-tight m-0 uppercase">
              AI Intelligence Summary
            </h2>
            <span className="text-[10px] font-mono text-cyan-500 uppercase tracking-widest mt-0.5 block">
              Live Intelligence Engine
            </span>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex flex-col items-end">
            <span className="text-[9px] font-mono text-neutral-500 uppercase">System Status</span>
            <span className="text-[11px] font-mono font-bold text-emerald-400 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              ONLINE & SYNCED
            </span>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 flex-1 mb-4 relative z-10">
        {/* Latest AI Insight */}
        <div className="bg-neutral-900/40 border border-neutral-800/60 rounded-xl p-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-mono text-neutral-400 uppercase flex items-center gap-1">
                <Brain className="w-3 h-3 text-purple-400" />
                Latest AI Finding
              </span>
              <span className="text-[9px] font-mono text-neutral-500 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Just now
              </span>
            </div>
            <p className="text-[13px] text-white font-medium leading-snug">
              Rajesh Gowda linked to 4 cyber extortion FIRs.
            </p>
          </div>
          <div className="flex gap-2 mt-3">
            <span className="px-2 py-1 rounded bg-rose-500/10 border border-rose-500/20 text-rose-400 text-[10px] font-mono uppercase">
              Risk: High
            </span>
            <span className="px-2 py-1 rounded bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-[10px] font-mono uppercase">
              Confidence: 92%
            </span>
          </div>
        </div>

        {/* Recommendations */}
        <div className="bg-neutral-900/40 border border-neutral-800/60 rounded-xl p-3 flex flex-col justify-between">
          <span className="text-[10px] font-mono text-neutral-400 uppercase mb-2 flex items-center gap-1">
            <Target className="w-3 h-3 text-emerald-400" />
            Recommended Actions
          </span>
          <ul className="space-y-2 flex-1">
            <li className="flex items-start gap-2 text-[12px] text-neutral-300">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
              <span className="leading-tight">Deploy surveillance</span>
            </li>
            <li className="flex items-start gap-2 text-[12px] text-neutral-300">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
              <span className="leading-tight">Freeze accounts</span>
            </li>
            <li className="flex items-start gap-2 text-[12px] text-neutral-300">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
              <span className="leading-tight">Cross match towers</span>
            </li>
          </ul>
        </div>
      </div>

      {/* Bottom Metrics & Actions */}
      <div className="flex flex-col sm:flex-row items-center justify-between border-t border-neutral-800/80 pt-4 mt-auto relative z-10 gap-4">
        {/* Quick Metrics */}
        <div className="flex items-center gap-6">
          <div className="flex flex-col">
            <span className="text-[9px] font-mono text-neutral-500 uppercase flex items-center gap-1"><Zap className="w-3 h-3" /> Accuracy</span>
            <span className="text-[12px] font-bold text-white">98.4%</span>
          </div>
          <div className="flex flex-col">
            <span className="text-[9px] font-mono text-neutral-500 uppercase flex items-center gap-1"><Shield className="w-3 h-3" /> Threat Lvl</span>
            <span className="text-[12px] font-bold text-rose-400">Severe</span>
          </div>
          <div className="flex flex-col hidden md:flex">
            <span className="text-[9px] font-mono text-neutral-500 uppercase flex items-center gap-1"><Activity className="w-3 h-3" /> Cases Today</span>
            <span className="text-[12px] font-bold text-cyan-400">142</span>
          </div>
        </div>

        {/* Buttons */}
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <button 
            className="flex-1 sm:flex-none px-4 py-2 border border-neutral-700 bg-neutral-800/50 hover:bg-neutral-800 text-neutral-300 rounded-lg text-xs font-mono transition-colors cursor-pointer"
          >
            Run Demo
          </button>
          <button 
            onClick={onOpenWorkspace}
            className="flex-1 sm:flex-none px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-mono font-bold transition-colors flex items-center justify-center gap-1.5 shadow-[0_0_15px_rgba(6,182,212,0.4)] cursor-pointer"
          >
            <span>Open AI Workspace</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
});

export default DashboardAIPreview;
