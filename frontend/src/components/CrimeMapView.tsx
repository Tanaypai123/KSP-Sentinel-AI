import { useState, memo } from 'react';
import { MapPin, Layers, Compass, X } from 'lucide-react';

interface Hotspot {
  id: string;
  name: string;
  category: 'cyber' | 'theft' | 'ndps';
  firCount: number;
  riskIndex: number; // 0-100
  coordinates: { x: number; y: number };
  activeSuspects: string[];
}

const CrimeMapView = memo(function CrimeMapView() {
  const [selectedHotspot, setSelectedHotspot] = useState<Hotspot | null>(null);
  const [activeCategory, setActiveCategory] = useState<string>('all');

  const hotspots: Hotspot[] = [
    {
      id: 'hs-1',
      name: 'Electronic City Zone II',
      category: 'ndps',
      firCount: 14,
      riskIndex: 82,
      coordinates: { x: 450, y: 310 },
      activeSuspects: ['Elena Rostova', 'Aditya Sen']
    },
    {
      id: 'hs-2',
      name: 'Jayanagar Central Sector',
      category: 'theft',
      firCount: 9,
      riskIndex: 74,
      coordinates: { x: 220, y: 210 },
      activeSuspects: ['Munna Qureshi']
    },
    {
      id: 'hs-3',
      name: 'Koramangala IT Corridor',
      category: 'cyber',
      firCount: 22,
      riskIndex: 88,
      coordinates: { x: 380, y: 150 },
      activeSuspects: ['Rajesh Gowda', 'Vikram "Techie" Rao']
    },
    {
      id: 'hs-4',
      name: 'Shivaji Nagar Transit Hub',
      category: 'theft',
      firCount: 18,
      riskIndex: 65,
      coordinates: { x: 290, y: 80 },
      activeSuspects: ['Local Factions']
    }
  ];

  const filteredHotspots = hotspots.filter(h => {
    if (activeCategory === 'all') return true;
    return h.category === activeCategory;
  });

  const getCategoryColor = (cat: string) => {
    switch (cat) {
      case 'cyber': return 'bg-cyan-500 fill-cyan-400 stroke-cyan-500';
      case 'ndps': return 'bg-purple-500 fill-purple-400 stroke-purple-500';
      default: return 'bg-amber-500 fill-amber-400 stroke-amber-500';
    }
  };

  return (
    <div className="flex flex-col space-y-6 h-full min-h-[580px]">
      {/* Crime Map Analytics KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="glass-panel p-5 rounded-xl border border-neutral-800 bg-neutral-950/60 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider block mb-1">Active Zones</span>
            <span className="text-2xl font-bold text-white block">14</span>
          </div>
          <div className="w-10 h-10 rounded-full bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
            <Layers className="w-5 h-5 text-cyan-400" />
          </div>
        </div>
        <div className="glass-panel p-5 rounded-xl border border-neutral-800 bg-neutral-950/60 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider block mb-1">Top District</span>
            <span className="text-lg font-bold text-rose-500 block truncate">Koramangala IT</span>
          </div>
          <div className="w-10 h-10 rounded-full bg-rose-500/10 border border-rose-500/20 flex items-center justify-center">
            <MapPin className="w-5 h-5 text-rose-400" />
          </div>
        </div>
        <div className="glass-panel p-5 rounded-xl border border-neutral-800 bg-neutral-950/60 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider block mb-1">Heatmap Peak</span>
            <span className="text-2xl font-bold text-amber-500 block">88%</span>
          </div>
          <div className="w-10 h-10 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
            <Compass className="w-5 h-5 text-amber-400" />
          </div>
        </div>
        <div className="glass-panel p-5 rounded-xl border border-neutral-800 bg-neutral-950/60">
          <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider block mb-1">Category Breakout</span>
          <div className="flex items-center space-x-2 mt-1">
            <span className="text-xs font-mono text-cyan-400 font-bold">22 CYBER</span>
            <span className="text-xs text-neutral-600">|</span>
            <span className="text-xs font-mono text-purple-400 font-bold">14 NDPS</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 flex-1">
      {/* Sidebar controls */}
      <div className="glass-panel rounded-2xl border border-neutral-800 bg-neutral-950/60 p-6 lg:col-span-1 flex flex-col justify-between">
        <div className="space-y-4">
          <div className="flex items-center space-x-3 pb-3 border-b border-neutral-900">
            <Compass className="w-5 h-5 text-cyan-400" />
            <span className="text-sm font-sans font-semibold tracking-wide text-white">
              Geolocation Radar
            </span>
          </div>

          <div className="space-y-3">
            <label className="text-xs font-mono text-neutral-500 uppercase flex items-center">
              <Layers className="w-4 h-4 mr-1.5 text-cyan-500" />
              HEATMAP CATEGORIES
            </label>
            <div className="flex flex-col space-y-1.5">
              {[
                { id: 'all', label: 'All Crime Incidents' },
                { id: 'cyber', label: 'Cyber Intrusion / Fraud' },
                { id: 'theft', label: 'Commercial Burglary' },
                { id: 'ndps', label: 'NDPS Drug Seizures' }
              ].map(cat => (
                <button
                  key={cat.id}
                  onClick={() => setActiveCategory(cat.id)}
                  className={`w-full text-left px-4 py-2 rounded-lg border text-sm font-sans font-medium transition cursor-pointer ${
                    activeCategory === cat.id
                      ? 'bg-cyan-950/20 border-cyan-500/30 text-cyan-400'
                      : 'border-transparent text-neutral-450 hover:bg-neutral-900 hover:text-white'
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Legend stats */}
        <div className="pt-4 border-t border-neutral-900 space-y-3">
          <span className="block text-xs font-mono text-neutral-600 uppercase font-bold tracking-wider">
            District Stats
          </span>
          <div className="space-y-2 text-xs font-mono text-neutral-450">
            <div className="flex justify-between">
              <span>CYBER EXTORTION:</span>
              <span className="text-cyan-400 font-bold">22 CASES</span>
            </div>
            <div className="flex justify-between">
              <span>NDPS ACCRUAL:</span>
              <span className="text-purple-400 font-bold">14 CASES</span>
            </div>
            <div className="flex justify-between">
              <span>THEFT & BREAK-IN:</span>
              <span className="text-amber-400 font-bold">27 CASES</span>
            </div>
          </div>
        </div>
      </div>

      {/* Map display area */}
      <div className="glass-panel rounded-2xl border border-neutral-800 bg-neutral-950/60 p-1 lg:col-span-3 relative overflow-hidden flex flex-col group">
        
        {/* Animated Map Scanning Line */}
        <div className="absolute inset-0 pointer-events-none z-10 overflow-hidden rounded-2xl">
          <div className="w-full h-1 bg-cyan-500/30 animate-scanline shadow-[0_0_15px_rgba(6,182,212,0.5)]" />
        </div>

        <div className="flex-1 w-full bg-[#0a0a0c] rounded-xl relative overflow-hidden intelligence-grid">
          <div className="bg-neutral-950/80 border border-neutral-800 p-3 rounded-lg max-w-xs backdrop-blur absolute top-4 left-4 z-10">
            <span className="block text-[10px] font-mono text-cyan-400 font-bold uppercase tracking-widest">
              BENGALURU DISTRICT SECTORS
            </span>
            <span className="block text-sm font-bold text-neutral-200 mt-1">
              Active Radar Hotspots: {filteredHotspots.length}
            </span>
          </div>

          <svg className="w-full h-full min-h-[460px]" viewBox="0 0 650 420">
            <defs>
              <pattern id="mapGrid" width="40" height="40" patternUnits="userSpaceOnUse">
                <rect width="40" height="40" fill="none" stroke="rgba(255, 255, 255, 0.015)" strokeWidth="0.5" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#mapGrid)" />

            <path
              d="M 50 150 Q 150 120 220 180 T 350 200 T 500 150 T 600 280"
              fill="none"
              stroke="rgba(255, 255, 255, 0.04)"
              strokeWidth="2"
              strokeDasharray="4 8"
            />
            <path
              d="M 120 50 Q 250 90 280 200 T 450 350 T 550 400"
              fill="none"
              stroke="rgba(255, 255, 255, 0.03)"
              strokeWidth="1.5"
              strokeDasharray="2 4"
            />

            {filteredHotspots.map((hs) => (
              <g
                key={hs.id}
                onClick={() => setSelectedHotspot(hs)}
                className="group cursor-pointer animate-pulse-slow"
              >
                <circle
                  cx={hs.coordinates.x}
                  cy={hs.coordinates.y}
                  r="24"
                  className={`${getCategoryColor(hs.category)} opacity-10 group-hover:opacity-20 transition duration-300`}
                />
                
                <circle
                  cx={hs.coordinates.x}
                  cy={hs.coordinates.y}
                  r="7"
                  className={`${getCategoryColor(hs.category)} group-hover:scale-125 transition duration-300`}
                />

                <circle
                  cx={hs.coordinates.x}
                  cy={hs.coordinates.y}
                  r="15"
                  className="fill-transparent stroke-cyan-500/20 stroke-[1.5px] animate-ping"
                  style={{ animationDuration: '3s' }}
                />

                <text
                  x={hs.coordinates.x}
                  y={hs.coordinates.y - 14}
                  className="fill-neutral-400 font-mono text-[10px] font-bold select-none text-center bg-black/80 pointer-events-none"
                  textAnchor="middle"
                >
                  {hs.name}
                </text>
              </g>
            ))}
          </svg>

          {/* Hotspot details panel (Slides in from right) */}
          {selectedHotspot && (
            <div className="absolute top-4 right-4 w-80 glass-panel border border-neutral-800/80 bg-neutral-950/90 rounded-xl shadow-2xl z-20 backdrop-blur-xl animate-fade-in transform transition-transform duration-300 ease-out translate-x-0">
              <div className="p-4 border-b border-neutral-900/50 flex justify-between items-start">
                <span className="text-xs font-mono font-bold tracking-wider text-cyan-400 uppercase flex items-center">
                  <MapPin className="w-4 h-4 mr-1.5" />
                  SECTOR INFORMATION
                </span>
                <button
                  onClick={() => setSelectedHotspot(null)}
                  className="p-0.5 rounded text-neutral-500 hover:text-white hover:bg-neutral-900 cursor-pointer"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="space-y-2">
                <div className="text-base font-bold text-white">{selectedHotspot.name}</div>
                <div className="grid grid-cols-2 gap-3 text-sm font-mono text-neutral-400">
                  <div>
                    <span className="block text-[10px] text-neutral-500 uppercase">ACTIVE INCIDENTS</span>
                    <span className="text-white font-bold">{selectedHotspot.firCount} FIRs</span>
                  </div>
                  <div>
                    <span className="block text-[10px] text-neutral-500 uppercase">DENSITY INDEX</span>
                    <span className="text-rose-400 font-bold">{selectedHotspot.riskIndex}% RISK</span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-neutral-900 space-y-3">
                <span className="block text-[10px] font-mono text-neutral-500 uppercase">Suspects Flagged in Grid</span>
                <div className="flex flex-wrap gap-1.5">
                  {selectedHotspot.activeSuspects.map((susp, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 rounded bg-neutral-900 border border-neutral-850 text-xs font-sans font-medium text-neutral-350"
                    >
                      {susp}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
    </div>
  );
});

export default CrimeMapView;
