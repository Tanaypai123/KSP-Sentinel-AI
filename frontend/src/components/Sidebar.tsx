import { memo } from 'react';
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

const Sidebar = memo(function Sidebar({
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
    <aside
      className={`glass-panel flex flex-col h-full transition-all duration-300 ease-in-out border-r border-neutral-800 bg-neutral-950/80 ${
        isCollapsed ? 'w-16' : 'w-64'
      } relative z-20`}
    >
      {/* Sidebar Header */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-neutral-800">
        {!isCollapsed && (
          <div className="flex items-center space-x-3">
            <div className="relative flex items-center justify-center w-10 h-10 rounded border border-cyan-500/30 bg-cyan-950/20 text-cyan-400">
              <ShieldCheck className="w-6 h-6" />
              <div className="absolute -top-0.5 -right-0.5 w-3 h-3 rounded-full bg-emerald-500 status-indicator border border-neutral-900" />
            </div>
            <div className="flex flex-col">
              <span className="font-mono text-sm tracking-widest text-neutral-400">KSP CORE</span>
              <span className="font-sans text-base font-bold tracking-tight text-white leading-none mt-1">SENTINEL AI</span>
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
      <nav className="flex-1 px-3 py-6 space-y-2 overflow-y-auto">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setCurrentTab(item.id)}
              className={`flex items-center relative w-full px-4 py-3 rounded-lg text-base font-medium transition-all group ${
                isActive
                  ? 'bg-cyan-950/30 border border-cyan-500/30 text-cyan-400 shadow-[inset_0_0_12px_rgba(6,182,212,0.08)]'
                  : 'text-neutral-400 hover:bg-neutral-900/60 hover:text-white border border-transparent'
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
              {isCollapsed && (
                <div className="absolute left-full ml-4 px-2 py-1 bg-neutral-900 border border-neutral-800 text-white text-[10px] font-mono uppercase tracking-wider rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50 whitespace-nowrap">
                  {item.name}
                </div>
              )}
            </button>
          );
        })}
      </nav>

      {/* System Status Dashboard Footer */}
      <div className="p-4 border-t border-neutral-900 bg-neutral-950/60">
        {isCollapsed ? (
          <div className="flex justify-center text-emerald-500 animate-pulse-slow">
            <Activity className="w-6 h-6" />
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center space-x-2 text-xs font-mono">
              <Terminal className="w-4 h-4 text-neutral-500" />
              <span className="text-neutral-500">ENGINE VER:</span>
              <span className="text-cyan-400 font-bold">v3.5.7-KSP</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-neutral-900/50 border border-neutral-800">
              <span className="text-xs font-mono text-neutral-500 tracking-wider">INTEL FEED</span>
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
                <span className="text-xs font-mono text-emerald-400 font-bold uppercase">ONLINE</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
});

export default Sidebar;
