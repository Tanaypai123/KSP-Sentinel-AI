import { useState, Suspense, lazy } from 'react';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import DashboardHeader from './components/DashboardHeader';
import DashboardKPIs from './components/DashboardKPIs';
import MissionIntelligencePanel from './components/MissionIntelligencePanel';
import DashboardFooter from './components/DashboardFooter';
import AIWorkspace from './components/AIWorkspace';
import DashboardAIPreview from './components/DashboardAIPreview';
import BottomSection from './components/BottomSection';
import type { FIR } from './types';
import { FileDown, Printer, Sliders, Database } from 'lucide-react';

// Lazy loaded heavy views
const NetworkGraphView = lazy(() => import('./components/NetworkGraphView'));
const CrimeMapView = lazy(() => import('./components/CrimeMapView'));
const DossierView = lazy(() => import('./components/DossierView'));

const ViewSkeleton = () => (
  <div className="w-full h-full space-y-6 animate-pulse-slow">
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      <div className="h-24 skeleton-shimmer rounded-xl border border-neutral-800 bg-neutral-900/50"></div>
      <div className="h-24 skeleton-shimmer rounded-xl border border-neutral-800 bg-neutral-900/50"></div>
      <div className="h-24 skeleton-shimmer rounded-xl border border-neutral-800 bg-neutral-900/50"></div>
      <div className="h-24 skeleton-shimmer rounded-xl border border-neutral-800 bg-neutral-900/50"></div>
    </div>
    <div className="h-[500px] skeleton-shimmer rounded-2xl border border-neutral-800 bg-neutral-900/50"></div>
  </div>
);

export default function App() {
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [searchValue, setSearchValue] = useState('');
  const [aiWorkspaceQuery, setAiWorkspaceQuery] = useState('');
  const [isAIFullscreen, setIsAIFullscreen] = useState(false);

  // Handle suggested queries or clicking an alert
  const handleQueryRoute = (query: string) => {
    setSearchValue(query);
    setAiWorkspaceQuery(query);
    setCurrentTab('dashboard'); // Route back to dashboard to process AI chat
  };

  const handleSelectFIR = (fir: FIR) => {
    setSearchValue(fir.caseNumber);
    setAiWorkspaceQuery(`Summarize FIR ${fir.caseNumber} details`);
    setCurrentTab('dashboard');
  };

  const handleSelectEntity = (name: string) => {
    setSearchValue(name);
    // If the name belongs to an accused, let's redirect them to Accused tab or query the AI
    if (name.includes('Rajesh') || name.includes('Gowda') || name.includes('Munna') || name.includes('Elena')) {
      setCurrentTab('accused');
    } else {
      setAiWorkspaceQuery(`Analyze connections for accused ${name}`);
      setCurrentTab('dashboard');
    }
  };

  // Render secondary sub-views depending on tab routing
  const renderMainContent = () => {
    switch (currentTab) {
      case 'dashboard':
        return (
          <div className="h-full">
            {/* SECTION 1: Header */}
            <DashboardHeader />
            
            <div className="columns-1 md:columns-2 xl:columns-3 gap-6 mt-6">
              {/* SECTION 2: Four KPI Cards */}
              <DashboardKPIs />
              
              {/* SECTION 3: AI Co-Pilot & Mission Intelligence */}
              <DashboardAIPreview 
                onOpenWorkspace={() => setCurrentTab('assistant')} 
              />

              <MissionIntelligencePanel onQuerySelect={handleQueryRoute} />
              
              {/* SECTION 4: Recent FIRs & Tactical Alerts */}
              <BottomSection 
                onSelectFIR={handleSelectFIR} 
                onSelectSearch={handleQueryRoute}
              />
              
              {/* SECTION 5: Recent Investigations, Quick Access, Searches */}
              <DashboardFooter onQuerySelect={handleQueryRoute} />
            </div>
          </div>
        );
      case 'assistant':
        return (
          <div className={isAIFullscreen ? "w-full h-full flex flex-col" : "space-y-4 flex flex-col h-full"}>
            {!isAIFullscreen && (
              <div className="pb-3 border-b border-neutral-900 flex-shrink-0">
                <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-widest">
                  KSP VIRTUAL WORKSPACE
                </span>
                <h2 className="text-lg font-bold text-white m-0">Dedicated AI Intelligence Assistant</h2>
              </div>
            )}
            <div className={isAIFullscreen ? "flex-1 min-h-0" : "flex-1 min-h-[500px]"}>
              <AIWorkspace 
                initialSearchQuery={aiWorkspaceQuery} 
                onSelectEntity={handleSelectEntity} 
                className="h-full"
                isFullscreen={isAIFullscreen}
                onToggleFullscreen={() => setIsAIFullscreen(!isAIFullscreen)}
              />
            </div>
          </div>
        );
      case 'cases':
        return (
          <div className="space-y-4">
            <div className="pb-3 border-b border-neutral-900">
              <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-widest">
                POLICE STATION ARCHIVES
              </span>
              <h2 className="text-lg font-bold text-white m-0">First Information Reports Directory</h2>
            </div>
            
            {/* FIR Page Summary KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="glass-panel p-4 rounded-xl border border-neutral-800 bg-neutral-950/60">
                <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider block mb-1">Total FIR Count</span>
                <span className="text-2xl font-bold text-white block">12,482</span>
                <span className="text-[10px] text-emerald-400 mt-1 block">↑ 12% vs last month</span>
              </div>
              <div className="glass-panel p-4 rounded-xl border border-neutral-800 bg-neutral-950/60">
                <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider block mb-1">Active Investigations</span>
                <span className="text-2xl font-bold text-cyan-400 block">3,190</span>
                <span className="text-[10px] text-neutral-400 mt-1 block">Across 42 stations</span>
              </div>
              <div className="glass-panel p-4 rounded-xl border border-neutral-800 bg-neutral-950/60">
                <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider block mb-1">Critical Priority</span>
                <span className="text-2xl font-bold text-rose-500 block">142</span>
                <span className="text-[10px] text-rose-400/80 mt-1 block">Requires immediate attention</span>
              </div>
              <div className="glass-panel p-4 rounded-xl border border-neutral-800 bg-neutral-950/60">
                <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider block mb-1">Closed / Resolved</span>
                <span className="text-2xl font-bold text-neutral-300 block">8,450</span>
                <span className="text-[10px] text-emerald-400 mt-1 block">68% resolution rate</span>
              </div>
            </div>

            <BottomSection 
              onSelectFIR={handleSelectFIR} 
              onSelectSearch={handleQueryRoute} 
            />
          </div>
        );
      case 'accused':
        return (
          <Suspense fallback={<ViewSkeleton />}>
            <DossierView searchFilter={searchValue} />
          </Suspense>
        );
      case 'map':
        return (
          <Suspense fallback={<ViewSkeleton />}>
            <CrimeMapView />
          </Suspense>
        );
      case 'network':
        return (
          <Suspense fallback={<ViewSkeleton />}>
            <NetworkGraphView />
          </Suspense>
        );
      case 'reports':
        return (
          <div className="space-y-6">
            <div className="pb-3 border-b border-neutral-900 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-widest">
                  DOCUMENT GENERATOR
                </span>
                <h2 className="text-lg font-bold text-white m-0">Intelligence Briefing Reports</h2>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => alert('Downloading encrypted intelligence PDF...')}
                  className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-cyan-950 border border-cyan-500/20 text-cyan-400 rounded-lg text-xs font-mono transition hover:bg-cyan-900 hover:text-white cursor-pointer"
                >
                  <FileDown className="w-3.5 h-3.5" />
                  <span>EXPORT PDF</span>
                </button>
                <button
                  onClick={() => alert('Printing brief...')}
                  className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-neutral-900 border border-neutral-805 text-neutral-400 rounded-lg text-xs font-mono transition hover:text-white cursor-pointer"
                >
                  <Printer className="w-3.5 h-3.5" />
                  <span>PRINT</span>
                </button>
              </div>
            </div>

            {/* Reports Layout Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              
              {/* Left Sidebar: Report Analytics & History */}
              <div className="lg:col-span-1 space-y-6">
                <div className="glass-panel rounded-xl border border-neutral-800 bg-neutral-950/60 p-5 space-y-4">
                  <span className="block text-[10px] font-mono text-neutral-500 uppercase tracking-wider mb-2 border-b border-neutral-900 pb-2">Document Statistics</span>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-neutral-400">Total Generated</span>
                    <span className="text-sm font-bold text-white">1,402</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-neutral-400">PDF Exports (Month)</span>
                    <span className="text-sm font-bold text-cyan-400">845</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-neutral-400">Dossiers Printed</span>
                    <span className="text-sm font-bold text-neutral-300">312</span>
                  </div>
                </div>

                <div className="glass-panel rounded-xl border border-neutral-800 bg-neutral-950/60 p-5 space-y-4">
                  <span className="block text-[10px] font-mono text-neutral-500 uppercase tracking-wider mb-2 border-b border-neutral-900 pb-2">Recent Archives</span>
                  <div className="space-y-3">
                    <div className="cursor-pointer hover:bg-neutral-900/50 p-2 -mx-2 rounded transition">
                      <span className="block text-xs font-bold text-white">Gowda_Net Correlation</span>
                      <span className="block text-[10px] text-neutral-500 mt-0.5">2 hrs ago • KSP-INTEL-281-06</span>
                    </div>
                    <div className="cursor-pointer hover:bg-neutral-900/50 p-2 -mx-2 rounded transition">
                      <span className="block text-xs font-bold text-neutral-300">Q2 Cyber Incidents Summary</span>
                      <span className="block text-[10px] text-neutral-500 mt-0.5">1 day ago • KSP-REP-442-12</span>
                    </div>
                    <div className="cursor-pointer hover:bg-neutral-900/50 p-2 -mx-2 rounded transition">
                      <span className="block text-xs font-bold text-neutral-300">Financial Ledger Analysis</span>
                      <span className="block text-[10px] text-neutral-500 mt-0.5">3 days ago • KSP-FIN-109-04</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Simulated report brief layout */}
              <div className="glass-panel rounded-2xl border border-neutral-800 bg-neutral-950/60 p-6 space-y-6 lg:col-span-3 font-mono text-xs text-neutral-400 relative overflow-hidden">
              {/* Draft Watermark */}
              <div className="absolute inset-0 flex items-center justify-center rotate-12 opacity-[0.015] pointer-events-none select-none">
                <span className="text-8xl font-bold font-sans">SECRET</span>
              </div>

              <div className="flex items-center justify-between border-b border-neutral-900 pb-4">
                <div className="space-y-1">
                  <span className="text-xs font-bold text-white">KARNATAKA STATE POLICE HEADQUARTERS</span>
                  <span className="block text-[10px] text-neutral-500">CYBER CRIME & FORENSICS DIV. • BENGALURU</span>
                </div>
                <div className="text-right text-[10px] text-neutral-500">
                  <span>DATE: 2026.07.04</span>
                  <span className="block">REF_NUM: KSP-INTEL-281-06</span>
                </div>
              </div>

              <div className="space-y-2">
                <span className="block text-cyan-400 font-bold tracking-widest text-[10px]">CASE DOSSIER EXECUTIVE SUMMARY</span>
                <p className="leading-relaxed font-sans text-neutral-350">
                  This dossier documents the tactical tracking and analysis of syndicate "Gowda_Net" and primary operator Rajesh Gowda. Correlation analysis by Sentinel AI indicates financial routing from Apex Realty Group diversion funds (FIR 310/2026) to the Gowda_Net bitcoin tumblers. Initial intrusion vector mapped to compromised Citrix gateways.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div className="p-4 bg-neutral-900/40 border border-neutral-850 rounded-xl space-y-2">
                  <span className="block font-bold text-white text-[10px]">THREAT ACTOR DIRECTORY</span>
                  <ul className="space-y-1 text-neutral-350 font-sans">
                    <li>• Rajesh "Gowda" Gowda (At Large - Threat 92%)</li>
                    <li>• Vikram "Techie" Rao (In Custody - Threat 78%)</li>
                    <li>• Munna "Safe-Cracker" Qureshi (At Large - Threat 85%)</li>
                  </ul>
                </div>
                <div className="p-4 bg-neutral-900/40 border border-neutral-850 rounded-xl space-y-2">
                  <span className="block font-bold text-white text-[10px]">FORENSIC EVIDENCE BLOCKS</span>
                  <ul className="space-y-1 text-neutral-350 font-sans">
                    <li>• Compromised Citrix VPN Log dump (Narayana Health)</li>
                    <li>• Safe cutting metallurgical residue (Jayanagar Jewellers)</li>
                    <li>• Crypto Tumbler receipt (0x74a...81)</li>
                  </ul>
                </div>
              </div>

              <div className="border-t border-neutral-900 pt-4 flex items-center justify-between text-[9px] text-neutral-600">
                <span>SECURITY CLEARANCE: STRICTLY INTERNAL CONFIDENTIAL</span>
                <span>AUTHENTICATED BY SENTINEL ENGINE v3.5</span>
              </div>
            </div>
            </div>
          </div>
        );
      case 'settings':
        return (
          <div className="space-y-6">
            <div className="pb-3 border-b border-neutral-900">
              <span className="text-[10px] font-mono text-neutral-500 uppercase tracking-widest">
                SYSTEM CALIBRATION
              </span>
              <h2 className="text-lg font-bold text-white m-0">Sentinel Config Operations</h2>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              {/* Configuration panel */}
              <div className="glass-panel rounded-2xl border border-neutral-800 bg-neutral-950/60 p-5 space-y-5 lg:col-span-1">
                <div className="flex items-center space-x-2 pb-2 border-b border-neutral-900">
                  <Sliders className="w-4 h-4 text-cyan-400" />
                  <span className="text-xs font-mono font-bold tracking-wider text-white uppercase">
                    AI AGENT PARAMETERS
                  </span>
                </div>

                <div className="space-y-4">
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-mono text-neutral-500 uppercase flex justify-between">
                      <span>Inference Temperature</span>
                      <span className="text-cyan-400">0.15 (Strict)</span>
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.05"
                      defaultValue="0.15"
                      className="w-full h-1 bg-neutral-900 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-[10px] font-mono text-neutral-500 uppercase flex justify-between">
                      <span>Maximum Token Threshold</span>
                      <span className="text-cyan-400">4,096 tokens</span>
                    </label>
                    <input
                      type="range"
                      min="512"
                      max="8192"
                      step="512"
                      defaultValue="4096"
                      className="w-full h-1 bg-neutral-900 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                    />
                  </div>

                  <div className="pt-2">
                    <span className="block text-[10px] font-mono text-neutral-500 uppercase mb-2">
                      SYSTEM PROMPT CORE
                    </span>
                    <textarea
                      rows={5}
                      defaultValue="You are KSP Sentinel AI, a specialized law enforcement intelligence investigator co-pilot. Analyze FIRs, cellular tracking reports, biometric databases, and transaction ledgers to detect correlations. Maintain top-secret clearance protocols."
                      className="w-full p-2.5 bg-neutral-900 border border-neutral-850 text-[10.5px] font-mono text-neutral-400 rounded-lg focus:outline-none focus:border-cyan-500/40"
                    />
                  </div>
                </div>
              </div>

              {/* System Audit logs console */}
              <div className="glass-panel rounded-2xl border border-neutral-800 bg-neutral-950/60 p-5 space-y-4 lg:col-span-2 flex flex-col">
                <div className="flex items-center justify-between pb-2 border-b border-neutral-900">
                  <div className="flex items-center space-x-2">
                    <Database className="w-4 h-4 text-cyan-400" />
                    <span className="text-xs font-mono font-bold tracking-wider text-white uppercase">
                      Sentinel Operations Audit Logs
                    </span>
                  </div>
                  <span className="text-[9px] font-mono text-emerald-400">SYNCING LIVE</span>
                </div>

                <div className="cyber-terminal p-4 rounded-xl flex-1 font-mono text-[10px] text-emerald-500/90 space-y-2 overflow-y-auto max-h-[300px]">
                  <div>[2026-07-04 14:10:02] INITIALIZING SENTINEL AI ENGINE v3.5.7-KSP...</div>
                  <div>[2026-07-04 14:10:04] DB CONNECTIONS ESTABLISHED: KSP_FIR_ARCHIVE, BIOMETRIC_IDENT_v4</div>
                  <div>[2026-07-04 14:10:05] MODEL WEIGHTS SYNCED: SECURE_ENCLAVE_LOC (99.8% STABILITY INDEX)</div>
                  <div>[2026-07-04 14:12:12] CELLULAR RADAR SCANNER INSTANTIATED: TOWER_GRID_SOUTH</div>
                  <div>[2026-07-04 14:15:30] DETECTED SURVEILLANCE CORRELATION [SIGNATURE: GOWDA_NET // ID: 0x74a]</div>
                  <div className="text-amber-500">[2026-07-04 14:20:45] WARNING: TOWER PING REGISTERED FOR TARGET: MUNNA QURESHI [GRID SECTOR: HUBBALLI]</div>
                  <div>[2026-07-04 14:25:04] AI INFERENCE REQUEST PROCESSED (TOKEN_LENGTH: 412) IN 0.88s</div>
                </div>
              </div>

              {/* System Health Diagnostics */}
              <div className="glass-panel rounded-2xl border border-neutral-800 bg-neutral-950/60 p-5 space-y-5 lg:col-span-1">
                <div className="flex items-center space-x-2 pb-2 border-b border-neutral-900">
                  <Database className="w-4 h-4 text-cyan-400" />
                  <span className="text-xs font-mono font-bold tracking-wider text-white uppercase">
                    SYSTEM HEALTH
                  </span>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-[10px] font-mono text-neutral-500 mb-1">
                      <span>API GATEWAY</span>
                      <span className="text-emerald-400">ONLINE</span>
                    </div>
                    <div className="w-full bg-neutral-900 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-emerald-500 h-full w-full" />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-[10px] font-mono text-neutral-500 mb-1">
                      <span>AI INFERENCE ENGINE</span>
                      <span className="text-emerald-400">NOMINAL</span>
                    </div>
                    <div className="w-full bg-neutral-900 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-emerald-500 h-full w-[95%]" />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-[10px] font-mono text-neutral-500 mb-1">
                      <span>MEMORY ALLOCATION</span>
                      <span className="text-amber-400">82%</span>
                    </div>
                    <div className="w-full bg-neutral-900 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-amber-500 h-full w-[82%]" />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-[10px] font-mono text-neutral-500 mb-1">
                      <span>GPU COMPUTE NODE</span>
                      <span className="text-cyan-400">45%</span>
                    </div>
                    <div className="w-full bg-neutral-900 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-cyan-500 h-full w-[45%]" />
                    </div>
                  </div>
                  <div className="pt-2 border-t border-neutral-900 flex justify-between items-center text-[10px] font-mono text-neutral-500">
                    <span>ENGINE VERSION:</span>
                    <span className="text-white">v3.5.7-KSP</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className={`h-screen overflow-hidden bg-neutral-950 text-neutral-200 font-sans ${isAIFullscreen ? 'flex flex-col' : 'intelligence-grid flex flex-row'}`}>
      {/* Sidebar Navigation */}
      {!isAIFullscreen && (
        <Sidebar
          currentTab={currentTab}
          setCurrentTab={(tab) => {
            setCurrentTab(tab);
            // clear search state if navigating tabs
            if (tab !== 'accused') setSearchValue('');
          }}
          isCollapsed={isSidebarCollapsed}
          setIsCollapsed={setIsSidebarCollapsed}
        />
      )}

      {/* Main Console */}
      <div className={`flex-1 flex flex-col min-w-0 ${isAIFullscreen ? 'w-screen h-screen' : ''}`}>
        <main className="flex-1 flex flex-col h-screen overflow-hidden">
          {!isAIFullscreen && (
            <Navbar 
              searchValue={searchValue} 
              setSearchValue={setSearchValue} 
            />
          )}
          
          <div className={isAIFullscreen ? "flex-1 overflow-y-auto animate-fade-in" : "flex-1 overflow-y-auto p-4 lg:px-6 lg:py-5 animate-fade-in custom-scrollbar"} key={currentTab}>
            <div className={isAIFullscreen ? "w-full h-full flex flex-col" : "max-w-7xl mx-auto h-full flex flex-col"}>
              {renderMainContent()}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
