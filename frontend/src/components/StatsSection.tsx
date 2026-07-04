import { FileText, ShieldAlert, Users, TrendingUp, Radio } from 'lucide-react';

export default function StatsSection() {
  const stats = [
    {
      title: 'TOTAL REGISTERED FIRS',
      value: '2,842',
      change: '+14 this week',
      trend: 'up',
      icon: FileText,
      color: 'text-cyan-400 border-cyan-500/10',
      bgColor: 'bg-cyan-500/5',
      glow: 'shadow-[0_0_15px_rgba(6,182,212,0.03)]'
    },
    {
      title: 'ACTIVE CASES',
      value: '142',
      change: '48 under forensic audit',
      trend: 'stable',
      icon: Radio,
      color: 'text-emerald-400 border-emerald-500/10',
      bgColor: 'bg-emerald-500/5',
      glow: 'shadow-[0_0_15px_rgba(16,185,129,0.03)]'
    },
    {
      title: 'ARRESTS REGISTERED TODAY',
      value: '8',
      change: '80% target execution rate',
      trend: 'up',
      icon: Users,
      color: 'text-indigo-400 border-indigo-500/10',
      bgColor: 'bg-indigo-500/5',
      glow: 'shadow-[0_0_15px_rgba(99,102,241,0.03)]'
    },
    {
      title: 'CRITICAL HIGH-RISK TARGETS',
      value: '24',
      change: 'Requires immediate action',
      trend: 'high-threat',
      icon: ShieldAlert,
      color: 'text-rose-400 border-rose-500/10',
      bgColor: 'bg-rose-500/5',
      glow: 'shadow-[0_0_15px_rgba(244,63,94,0.03)]'
    }
  ];

  return (
    <div className="space-y-4">
      {/* Officer Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-3 border-b border-neutral-800/40">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white m-0 flex items-center gap-2">
            WELCOME OFFICER,
            <span className="text-cyan-400 font-mono text-base font-medium bg-cyan-950/20 border border-cyan-500/10 px-2 py-0.5 rounded">
              INSP. VIKRAM RATHORE
            </span>
          </h1>
          <p className="text-xs font-mono text-neutral-500 mt-1 uppercase tracking-wider">
            CRIME OPERATIONS PORTAL • DISTRICT: BENGALURU METROPOLITAN
          </p>
        </div>
        <div className="flex items-center space-x-2 mt-3 md:mt-0 text-xs font-mono text-neutral-400 border border-neutral-800 bg-neutral-950/30 px-3 py-1.5 rounded-lg">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-neutral-500">CORRELATION RATIO:</span>
          <span className="text-white font-bold">98.4% STABLE</span>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, i) => {
          const Icon = stat.icon;
          const isHighThreat = stat.trend === 'high-threat';

          return (
            <div
              key={i}
              className={`glass-panel p-4 rounded-xl flex flex-col justify-between border border-neutral-800 bg-neutral-900/15 ${stat.glow} relative overflow-hidden`}
            >
              {/* Card Scanline Effect for high threat */}
              {isHighThreat && (
                <div className="absolute inset-0 pointer-events-none opacity-5">
                  <div className="w-full h-0.5 bg-rose-500 animate-scanline" />
                </div>
              )}

              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold tracking-wider text-neutral-500 uppercase">
                  {stat.title}
                </span>
                <div className={`p-1.5 rounded-lg border ${stat.color} ${stat.bgColor}`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>

              <div className="mt-3.5 flex items-baseline justify-between">
                <div className="flex items-center space-x-1.5">
                  <span className="text-2xl font-bold tracking-tight text-white font-mono">
                    {stat.value}
                  </span>
                  {isHighThreat && (
                    <span className="flex h-2.5 w-2.5 relative">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-500"></span>
                    </span>
                  )}
                </div>
                {stat.trend === 'up' && (
                  <span className="text-[10px] font-mono text-cyan-400 flex items-center">
                    <TrendingUp className="w-3 h-3 mr-0.5" />
                    +1.2%
                  </span>
                )}
              </div>

              <div className="mt-2.5 pt-2 border-t border-neutral-850 flex items-center justify-between text-[11px] font-sans text-neutral-400">
                <span className="truncate">{stat.change}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
