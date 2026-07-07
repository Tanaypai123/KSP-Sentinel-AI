import { FileText, ShieldAlert, Users, Target } from 'lucide-react';
import { useState, useEffect, memo } from 'react';

function AnimatedCounter({ targetValue }: { targetValue: string }) {
  const [count, setCount] = useState(0);
  
  useEffect(() => {
    const target = parseInt(targetValue.replace(/,/g, ''), 10);
    if (isNaN(target)) return;
    
    let start = 0;
    const duration = 1200;
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

// Simple SVG sparkline component
const Sparkline = ({ colorClass, points }: { colorClass: string, points: string }) => (
  <svg width="60" height="20" viewBox="0 0 60 20" className={`overflow-visible ${colorClass}`}>
    <path
      d={points}
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="drop-shadow-md"
    />
  </svg>
);

const DashboardKPIs = memo(function DashboardKPIs() {
  const stats = [
    {
      title: 'Total FIR',
      value: '2,842',
      trend: '+12.4%',
      isPositive: true,
      icon: FileText,
      color: 'text-cyan-400',
      bgColor: 'bg-cyan-500/10',
      borderColor: 'border-cyan-500/20',
      glow: 'shadow-[0_0_15px_rgba(6,182,212,0.05)]',
      sparkline: 'M0,15 Q10,12 20,8 T40,10 T60,2'
    },
    {
      title: 'Active Cases',
      value: '142',
      trend: '-4.2%',
      isPositive: true,
      icon: Target,
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-500/10',
      borderColor: 'border-emerald-500/20',
      glow: 'shadow-[0_0_15px_rgba(16,185,129,0.05)]',
      sparkline: 'M0,5 Q10,8 20,12 T40,15 T60,18' // going down (good for cases)
    },
    {
      title: 'High Risk Targets',
      value: '68',
      trend: '+18.1%',
      isPositive: false,
      icon: ShieldAlert,
      color: 'text-rose-400',
      bgColor: 'bg-rose-500/10',
      borderColor: 'border-rose-500/20',
      glow: 'shadow-[0_0_15px_rgba(244,63,94,0.05)]',
      sparkline: 'M0,18 Q10,15 20,8 T40,12 T60,2' // spiking up (bad)
    },
    {
      title: "Today's Arrests",
      value: '8',
      trend: '+2.0%',
      isPositive: true,
      icon: Users,
      color: 'text-amber-400',
      bgColor: 'bg-amber-500/10',
      borderColor: 'border-amber-500/20',
      glow: 'shadow-[0_0_15px_rgba(245,158,11,0.05)]',
      sparkline: 'M0,15 Q10,15 20,10 T40,8 T60,5'
    }
  ];

  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 800);
    return () => clearTimeout(timer);
  }, []);

  if (isLoading) {
    return (
      <>
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="premium-card p-4 h-[110px] flex flex-col justify-between break-inside-avoid mb-6">
            <div className="flex justify-between w-full mb-3">
              <div className="w-10 h-10 rounded-[10px] skeleton-shimmer" />
              <div className="w-16 h-6 rounded-md skeleton-shimmer" />
            </div>
            <div>
              <div className="w-24 h-8 rounded skeleton-shimmer mb-2" />
              <div className="w-32 h-4 rounded skeleton-shimmer" />
            </div>
          </div>
        ))}
      </>
    );
  }

  return (
    <>
      {stats.map((stat, idx) => (
        <div
          key={idx}
          className={`premium-card-interactive p-4 flex flex-col justify-between animate-slide-up break-inside-avoid mb-6`}
          style={{ animationDelay: `${idx * 100}ms` }}
        >
          <div className="flex items-start justify-between mb-4">
            <div className={`p-2.5 rounded-[10px] ${stat.bgColor} ${stat.color} border ${stat.borderColor} shadow-sm`}>
              <stat.icon className="w-[18px] h-[18px]" />
            </div>
            <div className={`flex items-center space-x-1 px-2.5 py-1 rounded-md text-[11px] font-mono font-bold border ${
              stat.isPositive ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' : 'text-rose-400 bg-rose-500/10 border-rose-500/20'
            }`}>
              <span>{stat.trend}</span>
            </div>
          </div>
          
          <div className="flex items-end justify-between relative">
            <div className="z-10">
              <span className="block text-[32px] font-semibold text-white tracking-tighter leading-none mb-1.5 drop-shadow-sm">
                <AnimatedCounter targetValue={stat.value} />
              </span>
              <span className="block text-xs font-sans font-medium text-neutral-400 tracking-wide mt-1">
                {stat.title}
              </span>
            </div>
            <div className="pb-1 opacity-50 absolute right-0 bottom-0 pointer-events-none">
              <Sparkline colorClass={stat.color} points={stat.sparkline} />
            </div>
          </div>
        </div>
      ))}
    </>
  );
});

export default DashboardKPIs;
