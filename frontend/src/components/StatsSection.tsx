import { FileText, ShieldAlert, Users, Radio } from 'lucide-react';
import { useState, useEffect, memo } from 'react';

function AnimatedCounter({ targetValue }: { targetValue: string }) {
  const [count, setCount] = useState(0);
  
  useEffect(() => {
    const target = parseInt(targetValue.replace(/,/g, ''), 10);
    if (isNaN(target)) {
      return;
    }
    
    let start = 0;
    const duration = 1200; // 1.2s animation
    const increment = target / (duration / 16);
    
    const timer = setInterval(() => {
      start += increment;
      if (start >= target) {
        setCount(target);
        clearInterval(timer);
      } else {
        setCount(Math.ceil(start));
      }
    }, 16);
    
    return () => clearInterval(timer);
  }, [targetValue]);
  
  if (isNaN(parseInt(targetValue.replace(/,/g, ''), 10))) return <>{targetValue}</>;
  return <>{count.toLocaleString()}</>;
}

const StatsSection = memo(function StatsSection() {
  const stats = [
    {
      title: 'Total Registered FIRs',
      value: '2,842',
      change: '+14 this week',
      trend: 'up',
      icon: FileText,
      color: 'text-cyan-400 border-cyan-500/10',
      bgColor: 'bg-cyan-500/5',
      glow: 'shadow-[0_0_15px_rgba(6,182,212,0.03)]'
    },
    {
      title: 'Active Cases',
      value: '142',
      change: '48 under forensic audit',
      trend: 'stable',
      icon: Radio,
      color: 'text-emerald-400 border-emerald-500/10',
      bgColor: 'bg-emerald-500/5',
      glow: 'shadow-[0_0_15px_rgba(16,185,129,0.03)]'
    },
    {
      title: 'Arrests Registered Today',
      value: '8',
      change: '80% target execution rate',
      trend: 'up',
      icon: Users,
      color: 'text-indigo-400 border-indigo-500/10',
      bgColor: 'bg-indigo-500/5',
      glow: 'shadow-[0_0_15px_rgba(99,102,241,0.03)]'
    },
    {
      title: 'Critical High-Risk Targets',
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
          <h1 className="text-3xl font-bold tracking-tight text-white m-0 flex items-center gap-3">
            Welcome Officer,
            <span className="text-cyan-400 font-mono text-lg font-medium bg-cyan-950/20 border border-cyan-500/10 px-2 py-0.5 rounded">
              INSP. VIKRAM RATHORE
            </span>
          </h1>
          <p className="text-sm font-mono text-neutral-500 mt-1.5 uppercase tracking-wider">
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
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => {
          const isHighThreat = stat.trend === 'high-threat';

          return (
            <div 
              key={stat.title}
              className={`glass-panel-interactive rounded-2xl p-6 border ${stat.color} ${stat.bgColor} ${stat.glow} animate-slide-up flex flex-col justify-between relative overflow-hidden`}
              style={{ animationDelay: `${i * 100}ms` }}
            >
              {/* Card Scanline Effect for high threat */}
              {isHighThreat && (
                <div className="absolute inset-0 pointer-events-none opacity-5">
                  <div className="w-full h-0.5 bg-rose-500 animate-scanline" />
                </div>
              )}

              <div className="flex justify-between items-start mb-4">
                <span className="text-[11px] font-mono text-neutral-400 uppercase tracking-widest">{stat.title}</span>
                <div className="p-2 rounded-lg bg-neutral-900/60 border border-neutral-800">
                  <stat.icon className={`w-4 h-4 ${stat.color.split(' ')[0]}`} />
                </div>
              </div>
              
              <div>
                <div className="flex items-center space-x-1.5 mb-1">
                  <span className="text-3xl font-bold tracking-tight text-white block">
                    <AnimatedCounter targetValue={stat.value} />
                  </span>
                  {isHighThreat && (
                    <span className="flex h-2.5 w-2.5 relative">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-500"></span>
                    </span>
                  )}
                </div>
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
});

export default StatsSection;
