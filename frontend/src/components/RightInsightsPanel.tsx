import { Sparkles, Search, History, HelpCircle, ChevronRight } from 'lucide-react';
import { mockAIInsights, mockRecentSearches, mockSuggestedQueries } from '../mockData';

interface RightInsightsPanelProps {
  onQueryClick: (query: string) => void;
}

export default function RightInsightsPanel({ onQueryClick }: RightInsightsPanelProps) {
  const getConfidenceColor = (score: number) => {
    if (score >= 90) return 'text-emerald-400 border-emerald-500/20 bg-emerald-500/5';
    if (score >= 80) return 'text-cyan-400 border-cyan-500/20 bg-cyan-500/5';
    return 'text-amber-400 border-amber-500/20 bg-amber-500/5';
  };

  return (
    <div className="space-y-4 h-full flex flex-col justify-between">
      {/* AI Insights Card Block */}
      <div className="glass-panel rounded-2xl border border-neutral-800 bg-neutral-950/60 p-4 flex-1 overflow-y-auto space-y-4">
        <div className="flex items-center space-x-2 pb-2.5 border-b border-neutral-900">
          <Sparkles className="w-4 h-4 text-cyan-400 animate-pulse" />
          <span className="text-xs font-mono font-bold tracking-wider text-white uppercase">
            AI Anomalies & Insights
          </span>
        </div>

        <div className="space-y-3">
          {mockAIInsights.map((insight) => (
            <div
              key={insight.id}
              onClick={() => onQueryClick(`Correlation regarding: ${insight.title}`)}
              className="p-3 rounded-lg border border-neutral-900 bg-neutral-950/40 hover:bg-neutral-900/60 hover:border-neutral-800 transition cursor-pointer group"
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-bold text-neutral-250 truncate block max-w-[70%] group-hover:text-cyan-300 transition-colors">
                  {insight.title}
                </span>
                <span className={`text-[9px] font-mono font-semibold px-1.5 py-0.5 rounded border ${getConfidenceColor(insight.confidence)}`}>
                  {insight.confidence}% CONF
                </span>
              </div>
              <p className="text-[11px] text-neutral-450 leading-relaxed font-sans mb-2">
                {insight.description}
              </p>
              <div className="flex flex-wrap gap-1">
                {insight.tags.map((tag, idx) => (
                  <span
                    key={idx}
                    className="text-[8px] font-mono px-1.5 py-0.5 rounded bg-neutral-900 border border-neutral-850 text-neutral-500"
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
      <div className="glass-panel rounded-2xl border border-neutral-800 bg-neutral-950/60 p-4 space-y-3">
        <div className="flex items-center space-x-2 pb-2 border-b border-neutral-900">
          <HelpCircle className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-mono font-bold tracking-wider text-white uppercase">
            Suggested Queries
          </span>
        </div>

        <div className="space-y-1.5">
          {mockSuggestedQueries.map((query, idx) => (
            <button
              key={idx}
              onClick={() => onQueryClick(query)}
              className="w-full text-left p-2 rounded-lg border border-neutral-900 bg-neutral-950/20 hover:bg-neutral-900/50 hover:border-neutral-800 transition text-xs text-neutral-400 hover:text-white flex items-center justify-between group cursor-pointer"
            >
              <span className="truncate pr-2">{query}</span>
              <ChevronRight className="w-3.5 h-3.5 text-neutral-600 group-hover:text-cyan-400 group-hover:translate-x-0.5 transition" />
            </button>
          ))}
        </div>
      </div>

      {/* Recent Searches */}
      <div className="glass-panel rounded-2xl border border-neutral-800 bg-neutral-950/60 p-4 space-y-3">
        <div className="flex items-center space-x-2 pb-2 border-b border-neutral-900">
          <History className="w-4 h-4 text-neutral-500" />
          <span className="text-xs font-mono font-bold tracking-wider text-white uppercase">
            Recent Inspections
          </span>
        </div>

        <div className="flex flex-wrap gap-1.5">
          {mockRecentSearches.map((search, idx) => (
            <button
              key={idx}
              onClick={() => onQueryClick(search)}
              className="flex items-center space-x-1 px-2.5 py-1 rounded-full border border-neutral-850 bg-neutral-900/50 text-[10px] text-neutral-450 hover:text-cyan-400 hover:border-cyan-500/25 transition cursor-pointer"
            >
              <Search className="w-2.5 h-2.5 text-neutral-600" />
              <span>{search}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
