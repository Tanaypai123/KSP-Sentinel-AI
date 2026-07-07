import { useState, memo } from 'react';
import { Network, Search, User, Globe, Layers, X, Shield, Smartphone, Database } from 'lucide-react';

interface Node {
  id: string;
  label: string;
  type: 'suspect' | 'case' | 'phone' | 'financial' | 'location';
  details: string;
  risk: 'High' | 'Medium' | 'Low' | 'None';
  x: number;
  y: number;
}

interface Edge {
  id: string;
  source: string;
  target: string;
  label: string;
}

const NetworkGraphView = memo(function NetworkGraphView() {
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const nodes: Node[] = [
    { id: '1', label: 'Rajesh Gowda', type: 'suspect', details: 'Kingpin, Gowda_Net Syndicate. Risk: 92%', risk: 'High', x: 250, y: 180 },
    { id: '2', label: 'Vikram "Techie" Rao', type: 'suspect', details: 'Access broker. In Custody. Risk: 78%', risk: 'Medium', x: 100, y: 220 },
    { id: '3', label: 'Apex Realty Group', type: 'financial', details: '₹140 Crore fraud entity. Risk: 85%', risk: 'High', x: 400, y: 150 },
    { id: '4', label: 'FIR 402/2026', type: 'case', details: 'Narayana Ransomware Case', risk: 'High', x: 180, y: 100 },
    { id: '5', label: 'Wallet 0x74a...81', type: 'financial', details: 'Destination BTC Tumblr address', risk: 'High', x: 380, y: 270 },
    { id: '6', label: 'Burner SIM +91-98450', type: 'phone', details: 'Registered with fake ID in AP border', risk: 'Medium', x: 200, y: 320 },
    { id: '7', label: 'Madanapalle Tower', type: 'location', details: 'Last cellular ping sector B4', risk: 'Medium', x: 320, y: 340 },
    { id: '8', label: 'Munna Qureshi', type: 'suspect', details: 'Safe-breaker specialist. Risk: 85%', risk: 'High', x: 500, y: 250 },
    { id: '9', label: 'FIR 289/2026', type: 'case', details: 'Jayanagar safe robbery', risk: 'Medium', x: 600, y: 200 }
  ];

  const edges: Edge[] = [
    { id: 'e1', source: '1', target: '4', label: 'Orchestrated' },
    { id: 'e2', source: '2', target: '4', label: 'Access Point' },
    { id: 'e3', source: '2', target: '1', label: 'Supplied credentials' },
    { id: 'e4', source: '1', target: '3', label: 'Laundered booking cash' },
    { id: 'e5', source: '3', target: '5', label: 'Transferred funds' },
    { id: 'e6', source: '1', target: '5', label: 'Controls cashout' },
    { id: 'e7', source: '1', target: '6', label: 'Uses device' },
    { id: 'e8', source: '6', target: '7', label: 'Connected cell tower' },
    { id: 'e9', source: '8', target: '9', label: 'Primary Suspect' },
    { id: 'e10', source: '8', target: '1', label: 'Syndicate affiliate' }
  ];

  const getNodeColor = (node: Node) => {
    if (selectedNode?.id === node.id) return 'fill-cyan-400 stroke-cyan-300';
    switch (node.type) {
      case 'suspect':
        return node.risk === 'High' ? 'fill-rose-500 stroke-rose-400' : 'fill-amber-500 stroke-amber-400';
      case 'case':
        return 'fill-cyan-500 stroke-cyan-400';
      case 'phone':
        return 'fill-purple-500 stroke-purple-400';
      case 'financial':
        return 'fill-emerald-500 stroke-emerald-400';
      default:
        return 'fill-neutral-500 stroke-neutral-400';
    }
  };

  const getNodeIcon = (type: string) => {
    switch (type) {
      case 'suspect': return <User className="w-4 h-4 text-rose-400" />;
      case 'phone': return <Smartphone className="w-4 h-4 text-purple-400" />;
      case 'financial': return <Database className="w-4 h-4 text-emerald-400" />;
      case 'case': return <Shield className="w-4 h-4 text-cyan-400" />;
      default: return <Globe className="w-4 h-4 text-neutral-400" />;
    }
  };

  const filteredNodes = nodes.filter(node => {
    const matchesSearch = node.label.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          node.details.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  const nodeIds = new Set(filteredNodes.map(n => n.id));
  const filteredEdges = edges.filter(edge => nodeIds.has(edge.source) && nodeIds.has(edge.target));

  return (
    <div className="flex flex-col space-y-6 h-full min-h-[580px]">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="glass-panel p-5 rounded-xl border border-neutral-800 bg-neutral-950/60 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider block mb-1">Live Connections</span>
            <span className="text-2xl font-bold text-white block">{filteredEdges.length}</span>
          </div>
          <div className="w-10 h-10 rounded-full bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
            <Network className="w-5 h-5 text-cyan-400" />
          </div>
        </div>
        <div className="glass-panel p-5 rounded-xl border border-neutral-800 bg-neutral-950/60 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider block mb-1">High Risk Entities</span>
            <span className="text-2xl font-bold text-rose-500 block">4</span>
          </div>
          <div className="w-10 h-10 rounded-full bg-rose-500/10 border border-rose-500/20 flex items-center justify-center">
            <User className="w-5 h-5 text-rose-400" />
          </div>
        </div>
        <div className="glass-panel p-5 rounded-xl border border-neutral-800 bg-neutral-950/60 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider block mb-1">Financial Linkages</span>
            <span className="text-2xl font-bold text-emerald-500 block">2</span>
          </div>
          <div className="w-10 h-10 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
            <Database className="w-5 h-5 text-emerald-400" />
          </div>
        </div>
        <div className="glass-panel p-5 rounded-xl border border-neutral-800 bg-neutral-950/60 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider block mb-1">Network Density</span>
            <span className="text-2xl font-bold text-amber-500 block">68%</span>
          </div>
          <div className="w-10 h-10 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
            <Layers className="w-5 h-5 text-amber-400" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 flex-1">
      <div className="glass-panel rounded-2xl border border-neutral-800 bg-neutral-950/60 p-6 lg:col-span-1 flex flex-col justify-between">
        <div className="space-y-4">
          <div className="flex items-center space-x-3 pb-3 border-b border-neutral-900">
            <Network className="w-5 h-5 text-cyan-400" />
            <span className="text-sm font-sans font-semibold tracking-wide text-white">
              Network Graph Controls
            </span>
          </div>
          <div className="relative">
            <Search className="absolute left-3.5 top-3 w-4 h-4 text-neutral-500" />
            <input
              type="text"
              placeholder="Filter graph node..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-neutral-900 border border-neutral-800 text-sm rounded-lg text-neutral-200 focus:outline-none focus:border-cyan-500/50 focus:shadow-[0_0_12px_rgba(6,182,212,0.08)] font-mono"
            />
          </div>
          <div className="space-y-3">
            <label className="text-xs font-mono text-neutral-500 uppercase flex items-center">
              <Layers className="w-4 h-4 mr-1.5 text-cyan-500" />
              LAYER TOGGLES
            </label>
            <div className="flex flex-col space-y-1.5">
              {['Suspects', 'Cases', 'Financial', 'Communications'].map(f => (
                <button
                  key={f}
                  className="w-full text-left px-4 py-2 rounded-lg border border-transparent text-sm font-sans font-medium text-neutral-450 hover:bg-neutral-900 hover:text-white"
                >
                  {f}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-neutral-900 space-y-3">
          <span className="block text-[10px] font-mono text-neutral-600 uppercase font-bold tracking-wider">
            LEGEND INDEX
          </span>
          <div className="grid grid-cols-2 gap-3 text-[11px] font-mono text-neutral-400">
            <div className="flex items-center space-x-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-rose-500 border border-rose-400" />
              <span>Suspect (High)</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-cyan-500 border border-cyan-400" />
              <span>FIR Case</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 border border-emerald-400" />
              <span>Financial Ledger</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-purple-500 border border-purple-400" />
              <span>Cell Terminal</span>
            </div>
          </div>
        </div>
      </div>

      <div className="glass-panel rounded-2xl border border-neutral-800 bg-neutral-950/40 lg:col-span-3 min-h-[500px] relative overflow-hidden flex flex-col justify-between">
        <div className="absolute top-4 left-4 z-10 pointer-events-none">
          <div className="bg-neutral-950/80 border border-neutral-800 p-3 rounded-lg max-w-xs backdrop-blur">
            <span className="block text-[10px] font-mono text-cyan-400 font-bold uppercase tracking-widest">
              CORRELATION LINK MAPPER
            </span>
            <span className="block text-sm font-bold text-neutral-250 mt-1">
              Active Links: {filteredEdges.length} / Total Nodes: {filteredNodes.length}
            </span>
          </div>
        </div>

        <div className="flex-1 w-full flex items-center justify-center relative cursor-crosshair">
          <svg className="w-full h-full min-h-[460px]" viewBox="0 0 700 450">
            <defs>
              <pattern id="smallGrid" width="20" height="20" patternUnits="userSpaceOnUse">
                <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(255, 255, 255, 0.02)" strokeWidth="0.5" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#smallGrid)" />

            {filteredEdges.map((edge) => {
              const source = nodes.find(n => n.id === edge.source);
              const target = nodes.find(n => n.id === edge.target);
              const isSelected = selectedNode && (selectedNode.id === edge.source || selectedNode.id === edge.target);
              if (!source || !target) return null;

              return (
                <g key={edge.id} className="transition-opacity duration-300">
                  <line
                    x1={source.x}
                    y1={source.y}
                    x2={target.x}
                    y2={target.y}
                    stroke="rgba(255, 255, 255, 0.15)"
                    strokeWidth={isSelected ? 2 : 1}
                  />
                  <line
                    x1={source.x}
                    y1={source.y}
                    x2={target.x}
                    y2={target.y}
                    stroke="rgba(14, 165, 233, 0.5)"
                    strokeWidth={1.5}
                    strokeDasharray="4 8"
                    className="animate-data-flow pointer-events-none"
                  />
                </g>
              );
            })}

            {filteredNodes.map((node) => (
              <g
                key={node.id}
                transform={`translate(${node.x},${node.y})`}
                onClick={() => setSelectedNode(node)}
                className={`cursor-pointer transition-all duration-300 ease-out ${
                  selectedNode && selectedNode.id !== node.id ? 'opacity-30 blur-[1px]' : 'opacity-100 hover:scale-110'
                }`}
              >
                <circle
                  r="12"
                  className="fill-transparent stroke-transparent group-hover:stroke-cyan-500/30 group-hover:fill-cyan-500/5 transition duration-300"
                  strokeWidth="6"
                />

                {/* Node Main Circle */}
                <circle
                  cx={0}
                  cy={0}
                  r="6"
                  className={`${getNodeColor(node)} transition duration-200`}
                />

                {/* Label text */}
                <text
                  x={0}
                  y={18}
                  className={`font-mono text-[10px] select-none text-center ${
                    selectedNode?.id === node.id ? 'fill-cyan-400 font-bold' : 'fill-neutral-400 group-hover:fill-neutral-200'
                  }`}
                  textAnchor="middle"
                >
                  {node.label}
                </text>
              </g>
            ))}
          </svg>

          {/* Node detail slide-over inside the graph */}
          {selectedNode && (
            <div className="absolute right-4 bottom-4 w-80 bg-neutral-950 border border-neutral-850 p-5 rounded-xl shadow-2xl backdrop-blur space-y-4 z-10">
              <div className="flex items-center justify-between border-b border-neutral-900 pb-3">
                <span className="text-xs font-mono font-bold tracking-wider text-cyan-400 flex items-center uppercase">
                  {getNodeIcon(selectedNode.type)}
                  <span className="ml-2">{selectedNode.type} dossier</span>
                </span>
                <button
                  onClick={() => setSelectedNode(null)}
                  className="p-1 rounded text-neutral-500 hover:text-white hover:bg-neutral-900 cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-1.5">
                <div className="text-base font-bold text-white">{selectedNode.label}</div>
                <div className="text-xs text-neutral-400 leading-relaxed font-sans">
                  {selectedNode.details}
                </div>
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-neutral-900 text-[11px] font-mono">
                <span className="text-neutral-500">THREAT RISK:</span>
                <span className={`px-2 py-1 rounded uppercase font-semibold ${
                  selectedNode.risk === 'High' ? 'bg-rose-500/15 text-rose-400 border border-rose-500/20' : 
                  selectedNode.risk === 'Medium' ? 'bg-amber-500/15 text-amber-400 border border-amber-500/20' : 
                  'bg-neutral-800 text-neutral-400'
                }`}>
                  {selectedNode.risk} RISK
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
      </div>
    </div>
  );
});

export default NetworkGraphView;
