import { useState, useEffect } from 'react';
import { Search, Bell, Shield, ChevronDown, User, LogOut, Terminal, Check } from 'lucide-react';
import { mockNotifications } from '../mockData';
import type { Notification } from '../types';

interface NavbarProps {
  onSearchChange: (search: string) => void;
  searchValue: string;
}

export default function Navbar({ onSearchChange, searchValue }: NavbarProps) {
  const [notifications, setNotifications] = useState<Notification[]>(mockNotifications);
  const [isOpenNotifications, setIsOpenNotifications] = useState(false);
  const [isOpenProfile, setIsOpenProfile] = useState(false);
  const [currentTime, setCurrentTime] = useState('');

  useEffect(() => {
    const updateTime = () => {
      const date = new Date();
      const timeStr = date.toLocaleTimeString('en-US', { hour12: false });
      const dateStr = date.toLocaleDateString('en-US', { year: 'numeric', month: '2-digit', day: '2-digit' }).replace(/\//g, '.');
      setCurrentTime(`${dateStr} // ${timeStr}`);
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const unreadCount = notifications.filter(n => n.unread).length;

  const markAllAsRead = () => {
    setNotifications(notifications.map(n => ({ ...n, unread: false })));
  };

  const getSeverityStyles = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-rose-500/10 text-rose-400 border border-rose-500/20';
      case 'warning':
        return 'bg-amber-500/10 text-amber-400 border border-amber-500/20';
      default:
        return 'bg-blue-500/10 text-blue-400 border border-blue-500/20';
    }
  };

  const handleNotificationSelect = (text: string) => {
    setIsOpenNotifications(false);
    // Extract FIR name or accused name from text if possible
    if (text.includes('FIR 402/2026') || text.includes('Gowda_Net')) {
      onSearchChange('FIR 402/2026');
    } else if (text.includes('Munna Qureshi') || text.includes('Hubballi')) {
      onSearchChange('Munna Qureshi');
    } else if (text.includes('FIR 156/2026') || text.includes('Rostova')) {
      onSearchChange('Elena Rostova');
    } else {
      onSearchChange(text);
    }
  };

  return (
    <header className="glass-panel sticky top-0 z-30 flex items-center justify-between h-16 px-6 border-b border-neutral-800 bg-neutral-950/80 backdrop-blur-md">
      {/* Search Input */}
      <div className="flex-1 max-w-lg">
        <div className="relative group">
          <Search className="absolute left-3.5 top-2.5 w-4 h-4 text-neutral-500 group-focus-within:text-cyan-400 transition-colors" />
          <input
            type="text"
            placeholder="Search FIR, accused dossier, tower location..."
            value={searchValue}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full h-9 pl-10 pr-12 text-sm font-sans text-neutral-200 bg-neutral-900/60 border border-neutral-800 rounded-lg focus:outline-none focus:border-cyan-500/40 focus:bg-neutral-900 transition-all placeholder:text-neutral-600"
          />
          <div className="absolute right-3 top-2 flex items-center space-x-0.5 px-1.5 py-0.5 border border-neutral-800 bg-neutral-950 rounded text-[9px] font-mono text-neutral-500 select-none">
            <span>⌘</span>
            <span>K</span>
          </div>
        </div>
      </div>

      {/* Action Items */}
      <div className="flex items-center space-x-6">
        {/* Intelligence Time Clock */}
        <div className="hidden md:flex items-center space-x-2 px-3 py-1.5 border border-neutral-800 bg-neutral-950/40 rounded-lg text-xs font-mono text-neutral-400">
          <Terminal className="w-3.5 h-3.5 text-cyan-500 animate-pulse" />
          <span className="tracking-widest">{currentTime}</span>
        </div>

        {/* Clearance Badge */}
        <div className="hidden lg:flex items-center space-x-1.5 px-2.5 py-1 border border-rose-500/10 bg-rose-500/5 text-rose-500 rounded text-[10px] font-mono font-bold tracking-widest">
          <Shield className="w-3 h-3 text-rose-500" />
          <span>SEC CLEARANCE: TOP SECRET</span>
        </div>

        {/* Notifications Popover */}
        <div className="relative">
          <button
            onClick={() => setIsOpenNotifications(!isOpenNotifications)}
            className={`relative p-2 rounded-lg border border-neutral-800 bg-neutral-900/40 text-neutral-400 hover:text-white hover:border-neutral-750 transition ${
              isOpenNotifications ? 'bg-neutral-900 border-neutral-700 text-white' : ''
            }`}
          >
            <Bell className="w-4 h-4" />
            {unreadCount > 0 && (
              <span className="absolute -top-1.5 -right-1.5 flex items-center justify-center w-5 h-5 text-[10px] font-bold text-black bg-cyan-400 rounded-full ring-2 ring-neutral-950 shadow-[0_0_10px_rgba(6,182,212,0.4)]">
                {unreadCount}
              </span>
            )}
          </button>

          {isOpenNotifications && (
            <div className="absolute right-0 mt-2 w-80 max-h-96 overflow-y-auto rounded-lg border border-neutral-800 bg-neutral-950 shadow-2xl z-50">
              <div className="flex items-center justify-between p-3 border-b border-neutral-800 bg-neutral-950">
                <span className="text-xs font-mono font-bold tracking-wider text-neutral-400">INTELLIGENCE ALERTS</span>
                {unreadCount > 0 && (
                  <button
                    onClick={markAllAsRead}
                    className="flex items-center space-x-1 text-[10px] font-mono text-cyan-400 hover:underline cursor-pointer"
                  >
                    <Check className="w-3 h-3" />
                    <span>MARK ALL READ</span>
                  </button>
                )}
              </div>
              <div className="divide-y divide-neutral-900">
                {notifications.length === 0 ? (
                  <div className="p-4 text-center text-xs font-mono text-neutral-500">
                    No active notifications
                  </div>
                ) : (
                  notifications.map((notif) => (
                    <div
                      key={notif.id}
                      onClick={() => handleNotificationSelect(notif.text)}
                      className={`p-3 text-xs hover:bg-neutral-900/50 transition cursor-pointer ${
                        notif.unread ? 'bg-neutral-900/20' : ''
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-semibold uppercase ${getSeverityStyles(notif.severity)}`}>
                          {notif.severity}
                        </span>
                        <span className="text-[10px] font-mono text-neutral-500">{notif.time}</span>
                      </div>
                      <p className="text-neutral-300 leading-relaxed font-sans">{notif.text}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Profile Dropdown */}
        <div className="relative">
          <button
            onClick={() => setIsOpenProfile(!isOpenProfile)}
            className="flex items-center space-x-2.5 p-1 px-2 rounded-lg border border-neutral-800 bg-neutral-900/40 hover:border-neutral-700 transition cursor-pointer"
          >
            <div className="relative w-7 h-7 rounded border border-cyan-500/20 bg-neutral-800 flex items-center justify-center text-cyan-400 font-bold font-mono text-xs">
              VR
            </div>
            <div className="hidden sm:flex flex-col text-left">
              <span className="text-xs font-bold font-sans text-neutral-200 leading-tight">Insp. Vikram Rathore</span>
              <span className="text-[9px] font-mono text-neutral-500 tracking-wider">KSP-CYBER-CRIME</span>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-neutral-500" />
          </button>

          {isOpenProfile && (
            <div className="absolute right-0 mt-2 w-48 rounded-lg border border-neutral-800 bg-neutral-950 shadow-2xl py-1 z-50">
              <div className="px-3 py-2 border-b border-neutral-900">
                <span className="block text-[10px] font-mono text-neutral-500">LOGGED IN AS</span>
                <span className="block text-xs font-bold text-neutral-300">V.Rathore@ksp.gov.in</span>
              </div>
              <button
                onClick={() => alert('Profile panel simulated.')}
                className="flex items-center w-full px-3 py-2 text-xs text-neutral-400 hover:text-white hover:bg-neutral-900 transition"
              >
                <User className="w-3.5 h-3.5 mr-2 text-neutral-500" />
                <span>My Profile</span>
              </button>
              <button
                onClick={() => alert('Logout simulated. State preserved in memory.')}
                className="flex items-center w-full px-3 py-2 text-xs text-rose-400 hover:text-rose-300 hover:bg-rose-950/20 transition border-t border-neutral-900"
              >
                <LogOut className="w-3.5 h-3.5 mr-2" />
                <span>De-authenticate</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
