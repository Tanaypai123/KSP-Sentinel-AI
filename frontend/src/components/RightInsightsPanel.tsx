import { AlertTriangle, ChevronRight, Activity, Zap, Sparkles, Search, History, HelpCircle } from 'lucide-react';
import { memo } from 'react';
import { mockAIInsights, mockRecentSearches } from '../mockData';

const RightInsightsPanel = memo(function RightInsightsPanel({ onQuerySelect }: { onQuerySelect: (query: string) => void }) {
  const suggestions = [
    { text: "Show critical alerts in Bengaluru", icon: AlertTriangle, color: "text-rose-400", bgColor: "bg-rose-500/10", borderColor: "border-rose-500/20", glow: "hover:shadow-[0_0_15px_rgba(244,63,94,0.15)] hover:border-rose-500/50" },
    { text: "List recent cyber extortion cases", icon: Activity, color: "text-cyan-400", bgColor: "bg-cyan-500/10", borderColor: "border-cyan-500/20", glow: "hover:shadow-[0_0_15px_rgba(6,182,212,0.15)] hover:border-cyan-500/50" },
    { text: "Who is Rajesh Gowda?", icon: Zap, color: "text-amber-400", bgColor: "bg-amber-500/10", borderColor: "border-amber-500/20", glow: "hover:shadow-[0_0_15px_rgba(245,158,11,0.15)] hover:border-amber-500/50" }
  ];

  const getConfidenceColor = (score: number) => {
    if (score >= 90) return 'text-emerald-400 border-emerald-500/20 bg-emerald-500/5';
    if (score >= 80) return 'text-cyan-400 border-cyan-500/20 bg-cyan-500/5';
    return 'text-amber-400 border-amber-500/20 bg-amber-500/5';
  };

  return (
    <aside className="space-y-4 h-full flex flex-col justify-between">
      {/* AI Insights Card Block */}
      <div className="glass-panel rounded-2xl border border-neutral-800 bg-neutral-950/60 p-5 flex-1 overflow-y-auto space-y-4">
        <div className="flex items-center space-x-3 pb-3 border-b border-neutral-900">
          <Sparkles className="w-5 h-5 text-cyan-400 animate-pulse" />
          <span className="text-sm font-sans font-semibold tracking-wide text-white">
            AI Anomalies & Insights
          </span>
        </div>

        <div className="space-y-3">
          {mockAIInsights.map((insight) => (
            <div
              key={insight.id}
              onClick={() => onQuerySelect(`Correlation regarding: ${insight.title}`)}
              className="p-4 rounded-lg border border-neutral-900 bg-neutral-950/40 hover:bg-neutral-900/60 hover:border-neutral-800 transition cursor-pointer group"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-bold text-neutral-200 truncate block max-w-[70%] group-hover:text-cyan-300 transition-colors">
                  {insight.title}
                </span>
                <span className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded border ${getConfidenceColor(insight.confidence)}`}>
                  {insight.confidence}% CONF
                </span>
              </div>
              <p className="text-xs text-neutral-400 leading-relaxed font-sans mb-3">
                {insight.description}
              </p>
              <div className="flex flex-wrap gap-1.5">
                {insight.tags.map((tag, idx) => (
                  <span
                    key={idx}
                    className="text-[10px] font-mono px-2 py-0.5 rounded bg-neutral-900 border border-neutral-850 text-neutral-500"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Suggested Queries Card Block */}
      <div className="glass-panel rounded-2xl border border-neutral-800 bg-neutral-950/60 p-5 space-y-4">
        <div className="flex items-center space-x-3 pb-3 border-b border-neutral-900">
          <HelpCircle className="w-5 h-5 text-cyan-400" />
          <span className="text-sm font-sans font-semibold tracking-wide text-white">
            Suggested Queries
          </span>
        </div>

        <div className="space-y-3">
          {suggestions.map((s, idx) => (
            <button
              key={idx}
              onClick={() => onQuerySelect(s.text)}
              className={`w-full group glass-panel flex items-center justify-between p-3 rounded-xl border ${s.borderColor} bg-neutral-900/40 hover:bg-neutral-900/80 transition-all duration-300 ${s.glow} hover:-translate-y-0.5 cursor-pointer`}
            >
              <div className="flex items-center space-x-3 text-left">
                <div className={`p-2 rounded-lg ${s.bgColor} ${s.color}`}>
                  <s.icon className="w-4 h-4" />
                </div>
                <span className="text-sm font-medium text-neutral-300 group-hover:text-white transition-colors">
                  {s.text}
                </span>
              </div>
              <ChevronRight className="w-4 h-4 text-neutral-600 group-hover:text-cyan-400 transition-colors transform group-hover:translate-x-1" />
            </button>
          ))}
        </div>
      </div>

      {/* Recent Searches */}
      <div className="glass-panel rounded-2xl border border-neutral-800 bg-neutral-950/60 p-5 space-y-4">
        <div className="flex items-center space-x-3 pb-3 border-b border-neutral-900">
          <History className="w-5 h-5 text-neutral-500" />
          <span className="text-sm font-sans font-semibold tracking-wide text-white">
            Recent Inspections
          </span>
        </div>

        <div className="flex flex-wrap gap-1.5">
          {mockRecentSearches.map((search, idx) => (
            <button
              key={idx}
              onClick={() => onQuerySelect(search)}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full border border-neutral-850 bg-neutral-900/50 text-xs text-neutral-400 hover:text-cyan-400 hover:border-cyan-500/25 transition cursor-pointer"
            >
              <Search className="w-3 h-3 text-neutral-600" />
              <span>{search}</span>
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
});

export default RightInsightsPanel;
