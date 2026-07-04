import {
  LayoutDashboard,
  MessageSquare,
  FileDigit,
  UserX,
  Map,
  Network,
  FileBarChart,
  Settings,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  Terminal,
  Activity
} from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
}

export default function Sidebar({
  currentTab,
  setCurrentTab,
  isCollapsed,
  setIsCollapsed
}: SidebarProps) {
  const menuItems = [
    { id: 'dashboard', name: 'Dashboard', icon: LayoutDashboard },
    { id: 'assistant', name: 'AI Assistant', icon: MessageSquare },
    { id: 'cases', name: 'Cases (FIR)', icon: FileDigit },
    { id: 'accused', name: 'Accused Dossiers', icon: UserX },
    { id: 'map', name: 'Crime Map', icon: Map },
    { id: 'network', name: 'Network Graph', icon: Network },
    { id: 'reports', name: 'Reports', icon: FileBarChart },
    { id: 'settings', name: 'Settings', icon: Settings },
  ];

  return (
    <div
      className={`glass-panel flex flex-col h-full transition-all duration-300 ease-in-out border-r border-neutral-800 bg-neutral-950/80 ${
        isCollapsed ? 'w-16' : 'w-64'
      } relative z-20`}
    >
      {/* Sidebar Header */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-neutral-800">
        {!isCollapsed && (
          <div className="flex items-center space-x-2">
            <div className="relative flex items-center justify-center w-8 h-8 rounded border border-cyan-500/30 bg-cyan-950/20 text-cyan-400">
              <ShieldCheck className="w-5 h-5" />
              <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-500 status-indicator border border-neutral-900" />
            </div>
            <div className="flex flex-col">
              <span className="font-mono text-xs tracking-widest text-neutral-400">KSP CORE</span>
              <span className="font-sans text-sm font-bold tracking-tight text-white leading-none">SENTINEL AI</span>
            </div>
          </div>
        )}
        {isCollapsed && (
          <div className="relative flex items-center justify-center w-8 h-8 mx-auto rounded border border-cyan-500/30 bg-cyan-950/20 text-cyan-400">
            <ShieldCheck className="w-5 h-5" />
            <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-500 status-indicator border border-neutral-900" />
          </div>
        )}
        
        {/* Collapse Button */}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="absolute top-4 -right-3 flex items-center justify-center w-6 h-6 rounded-full border border-neutral-800 bg-neutral-900 text-neutral-400 hover:text-white hover:border-neutral-700 hover:bg-neutral-850 transition"
        >
          {isCollapsed ? <ChevronRight className="w-3.5 h-3.5" /> : <ChevronLeft className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setCurrentTab(item.id)}
              className={`flex items-center w-full px-3 py-2.5 rounded-lg text-sm font-medium transition-all group ${
                isActive
                  ? 'bg-cyan-950/30 border border-cyan-500/20 text-cyan-400 shadow-[inset_0_0_12px_rgba(6,182,212,0.05)]'
                  : 'text-neutral-400 hover:bg-neutral-900/50 hover:text-white border border-transparent'
              }`}
            >
              <Icon
                className={`w-5 h-5 flex-shrink-0 transition ${
                  isActive ? 'text-cyan-400' : 'text-neutral-400 group-hover:text-neutral-200'
                } ${isCollapsed ? 'mx-auto' : 'mr-3'}`}
              />
              {!isCollapsed && <span className="truncate">{item.name}</span>}
              {!isCollapsed && isActive && (
                <div className="w-1.5 h-1.5 ml-auto rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(6,182,212,0.6)] animate-pulse" />
              )}
            </button>
          );
        })}
      </nav>

      {/* System Status Dashboard Footer */}
      <div className="p-3 border-t border-neutral-900 bg-neutral-950/40">
        {isCollapsed ? (
          <div className="flex justify-center text-emerald-500 animate-pulse-slow">
            <Activity className="w-5 h-5" />
          </div>
        ) : (
          <div className="space-y-2">
            <div className="flex items-center space-x-2 text-xs font-mono">
              <Terminal className="w-3.5 h-3.5 text-neutral-500" />
              <span className="text-neutral-500">ENGINE VER:</span>
              <span className="text-cyan-400 font-bold">v3.5.7-KSP</span>
            </div>
            <div className="flex items-center justify-between p-2 rounded bg-neutral-900/50 border border-neutral-900">
              <span className="text-[10px] font-mono text-neutral-500 tracking-wider">INTEL FEED</span>
              <div className="flex items-center space-x-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-[10px] font-mono text-emerald-400 uppercase">ONLINE</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
