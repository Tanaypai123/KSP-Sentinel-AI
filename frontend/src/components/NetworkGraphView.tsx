import { useState } from 'react';
import { Network, Search, Shield, User, Smartphone, Database, Globe, Layers, X } from 'lucide-react';

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
  source: string;
  target: string;
  label: string;
}

export default function NetworkGraphView() {
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [activeFilter, setActiveFilter] = useState<string>('all');
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
    { source: '1', target: '4', label: 'Orchestrated' },
    { source: '2', target: '4', label: 'Access Point' },
    { source: '2', target: '1', label: 'Supplied credentials' },
    { source: '1', target: '3', label: 'Laundered booking cash' },
    { source: '3', target: '5', label: 'Transferred funds' },
    { source: '1', target: '5', label: 'Controls cashout' },
    { source: '1', target: '6', label: 'Uses device' },
    { source: '6', target: '7', label: 'Connected cell tower' },
    { source: '8', target: '9', label: 'Primary Suspect' },
    { source: '8', target: '1', label: 'Syndicate affiliate' }
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
    if (activeFilter === 'all') return matchesSearch;
    return node.type === activeFilter && matchesSearch;
  });

  const nodeIds = new Set(filteredNodes.map(n => n.id));
  const filteredEdges = edges.filter(edge => nodeIds.has(edge.source) && nodeIds.has(edge.target));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-full min-h-[580px]">
      {/* Sidebar Controls */}
      <div className="glass-panel rounded-2xl border border-neutral-800 bg-neutral-950/60 p-4 lg:col-span-1 flex flex-col justify-between">
        <div className="space-y-4">
          <div className="flex items-center space-x-2 pb-2.5 border-b border-neutral-900">
            <Network className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-mono font-bold tracking-wider text-white uppercase">
              NETWORK GRAPH CONTROLS
            </span>
          </div>

          {/* Search bar */}
          <div className="relative">
            <Search className="absolute left-3 top-2.5 w-3.5 h-3.5 text-neutral-500" />
            <input
              type="text"
              placeholder="Filter graph node..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-neutral-900 border border-neutral-800 text-xs rounded-lg text-neutral-200 focus:outline-none focus:border-cyan-500/40 font-mono"
            />
          </div>

          {/* Filter Layers */}
          <div className="space-y-2">
            <label className="text-[10px] font-mono text-neutral-500 uppercase flex items-center">
              <Layers className="w-3.5 h-3.5 mr-1 text-cyan-500" />
              LAYER TOGGLES
            </label>
            <div className="flex flex-col space-y-1.5">
              {[
                { id: 'all', label: 'Show All Layers' },
                { id: 'suspect', label: 'Suspect Profiles' },
                { id: 'case', label: 'Cases (FIRs)' },
                { id: 'phone', label: 'Cellular Assets' },
                { id: 'financial', label: 'Financial Nodes' }
              ].map(f => (
                <button
                  key={f.id}
                  onClick={() => setActiveFilter(f.id)}
                  className={`w-full text-left px-3 py-1.5 rounded-lg border text-xs font-mono transition cursor-pointer ${
                    activeFilter === f.id
                      ? 'bg-cyan-950/20 border-cyan-500/30 text-cyan-400'
                      : 'border-transparent text-neutral-450 hover:bg-neutral-900 hover:text-white'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="pt-4 border-t border-neutral-900 space-y-2">
          <span className="block text-[9px] font-mono text-neutral-600 uppercase font-bold tracking-wider">
            LEGEND INDEX
          </span>
          <div className="grid grid-cols-2 gap-2 text-[10px] font-mono text-neutral-400">
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

      {/* SVG Canvas Workspace - Span 3 */}
      <div className="glass-panel rounded-2xl border border-neutral-800 bg-neutral-950/40 lg:col-span-3 min-h-[500px] relative overflow-hidden flex flex-col justify-between">
        {/* Graph Header details */}
        <div className="absolute top-4 left-4 z-10 pointer-events-none">
          <div className="bg-neutral-950/80 border border-neutral-800 p-2.5 rounded-lg max-w-xs backdrop-blur">
            <span className="block text-[9px] font-mono text-cyan-400 font-bold uppercase tracking-widest">
              CORRELATION LINK MAPPER
            </span>
            <span className="block text-xs font-bold text-neutral-250 mt-1">
              Active Links: {filteredEdges.length} / Total Nodes: {filteredNodes.length}
            </span>
          </div>
        </div>

        {/* Live Vector Viewport */}
        <div className="flex-1 w-full flex items-center justify-center relative cursor-crosshair">
          <svg className="w-full h-full min-h-[460px]" viewBox="0 0 700 450">
            {/* Grid Pattern Background */}
            <defs>
              <pattern id="smallGrid" width="20" height="20" patternUnits="userSpaceOnUse">
                <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(255, 255, 255, 0.02)" strokeWidth="0.5" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#smallGrid)" />

            {/* Glowing lines between nodes */}
            {filteredEdges.map((edge, idx) => {
              const fromNode = nodes.find(n => n.id === edge.source);
              const toNode = nodes.find(n => n.id === edge.target);
              if (!fromNode || !toNode) return null;

              return (
                <g key={idx} className="group/edge cursor-pointer">
                  <line
                    x1={fromNode.x}
                    y1={fromNode.y}
                    x2={toNode.x}
                    y2={toNode.y}
                    className="stroke-neutral-800 group-hover/edge:stroke-cyan-500/50 transition duration-300"
                    strokeWidth="1.5"
                  />
                  <line
                    x1={fromNode.x}
                    y1={fromNode.y}
                    x2={toNode.x}
                    y2={toNode.y}
                    className="stroke-transparent group-hover/edge:stroke-cyan-500/20 stroke-[10px] transition duration-300"
                  />
                  {/* Subtle edge label in center */}
                  <text
                    x={(fromNode.x + toNode.x) / 2}
                    y={(fromNode.y + toNode.y) / 2 - 4}
                    className="fill-neutral-600 font-mono text-[8px] text-center select-none pointer-events-none opacity-0 group-hover/edge:opacity-100 transition duration-200"
                    textAnchor="middle"
                  >
                    {edge.label}
                  </text>
                </g>
              );
            })}

            {/* Glowing Node Circles */}
            {filteredNodes.map((node) => (
              <g
                key={node.id}
                onClick={() => setSelectedNode(node)}
                className="group/node cursor-pointer"
                transform={`translate(0, 0)`}
              >
                {/* Node Outer Glow Ring */}
                <circle
                  cx={node.x}
                  cy={node.y}
                  r="12"
                  className="fill-transparent stroke-transparent group-hover/node:stroke-cyan-500/30 group-hover/node:fill-cyan-500/5 transition duration-300"
                  strokeWidth="6"
                />

                {/* Node Main Circle */}
                <circle
                  cx={node.x}
                  cy={node.y}
                  r="6"
                  className={`${getNodeColor(node)} transition duration-200`}
                />

                {/* Label text */}
                <text
                  x={node.x}
                  y={node.y + 18}
                  className={`font-mono text-[9px] select-none text-center ${
                    selectedNode?.id === node.id ? 'fill-cyan-400 font-bold' : 'fill-neutral-400 group-hover/node:fill-neutral-200'
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
            <div className="absolute right-4 bottom-4 w-72 bg-neutral-950 border border-neutral-850 p-4 rounded-xl shadow-2xl backdrop-blur space-y-3 z-10">
              <div className="flex items-center justify-between border-b border-neutral-900 pb-2">
                <span className="text-[10px] font-mono font-bold tracking-wider text-cyan-400 flex items-center uppercase">
                  {getNodeIcon(selectedNode.type)}
                  <span className="ml-1.5">{selectedNode.type} dossier</span>
                </span>
                <button
                  onClick={() => setSelectedNode(null)}
                  className="p-0.5 rounded text-neutral-500 hover:text-white hover:bg-neutral-900 cursor-pointer"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="space-y-1">
                <div className="text-xs font-bold text-white">{selectedNode.label}</div>
                <div className="text-[10px] text-neutral-400 leading-normal font-sans">
                  {selectedNode.details}
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-neutral-900 text-[10px] font-mono">
                <span className="text-neutral-500">THREAT RISK:</span>
                <span className={`px-1.5 py-0.5 rounded uppercase font-semibold ${
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
  );
}
