import { useState, useRef, useEffect } from 'react';
import {
  Send,
  Sparkles,
  RefreshCw,
  Paperclip,
  CheckCircle2,
  Eye,
  FileCode
} from 'lucide-react';
import type { Message } from '../types';
import { getAIResponse } from '../mockData';

interface AIWorkspaceProps {
  initialSearchQuery?: string;
  onSelectEntity?: (name: string) => void;
}

export default function AIWorkspace({ initialSearchQuery = '', onSelectEntity }: AIWorkspaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'm-welcome',
      sender: 'assistant',
      text: 'SYSTEM BOOT SUCCESSFUL. KSP Sentinel AI Core initialized. Access clearance verified. I have indexed 5 active FIR files, 4 high-risk accused profiles, and real-time cellular towers. Ask about any FIR, accused profile, location, or cross-case correlation.',
      timestamp: new Date().toLocaleTimeString(),
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [selectedModel, setSelectedModel] = useState('KSP-Sentinel-v3.5-Intelligence');
  const [isTyping, setIsTyping] = useState(false);
  const [expandedJson, setExpandedJson] = useState<Record<string, boolean>>({});
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // Handle external query injections from suggested queries or search
  useEffect(() => {
    if (initialSearchQuery) {
      handleSend(initialSearchQuery);
    }
  }, [initialSearchQuery]);

  const handleSend = (textToSend?: string) => {
    const query = textToSend || inputValue;
    if (!query.trim()) return;

    // Add user message
    const userMsg: Message = {
      id: `usr-${Date.now()}`,
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsTyping(true);

    // Simulate response delay and streaming effect
    setTimeout(() => {
      const response = getAIResponse(query);
      
      // Simulate slight response stream
      setIsTyping(false);
      setMessages(prev => [...prev, response]);
    }, 1200);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleJson = (id: string) => {
    setExpandedJson(prev => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="glass-panel flex flex-col h-[520px] rounded-2xl border border-neutral-800 bg-neutral-950/60 overflow-hidden relative shadow-2xl">
      {/* Workspace Header */}
      <div className="flex items-center justify-between px-5 h-12 border-b border-neutral-800 bg-neutral-900/30">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-cyan-400 animate-pulse" />
          <span className="text-xs font-mono font-bold tracking-widest text-white">AI INVESTIGATION CO-PILOT</span>
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
        </div>
        <div className="flex items-center space-x-3">
          <label className="text-[10px] font-mono text-neutral-500 uppercase">Model Asset:</label>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="bg-neutral-900 border border-neutral-800 text-[10px] font-mono text-cyan-400 rounded px-2 py-0.5 focus:outline-none focus:border-cyan-500 cursor-pointer"
          >
            <option value="KSP-Sentinel-v3.5-Intelligence">KSP-Sentinel-v3.5 (GovFineTuned)</option>
            <option value="Llama-3-Gov-Security">Llama-3-Gov-Security (8B)</option>
            <option value="DeepSeek-R1-District">DeepSeek-R1-District-Core</option>
          </select>
          <button 
            onClick={() => setMessages([messages[0]])}
            title="Clear Investigation Log"
            className="p-1 text-neutral-500 hover:text-cyan-400 hover:bg-neutral-900 rounded transition cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Message Output Workspace */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col max-w-[85%] ${
              msg.sender === 'user' ? 'ml-auto items-end' : 'mr-auto items-start'
            }`}
          >
            {/* Timestamp label */}
            <span className="text-[9px] font-mono text-neutral-600 mb-1">
              {msg.sender === 'user' ? 'OFFICER RATHORE' : 'KSP-SENTINEL-CORE'} • {msg.timestamp}
            </span>

            {/* Bubble */}
            <div
              className={`p-3.5 rounded-xl border leading-relaxed text-sm ${
                msg.sender === 'user'
                  ? 'bg-neutral-900 border-neutral-850 text-neutral-200 rounded-tr-none'
                  : 'bg-neutral-900/40 border-neutral-800 text-neutral-300 rounded-tl-none font-sans'
              }`}
            >
              {msg.text}

              {/* Render Structured response items if present */}
              {msg.structuredAnswer && (
                <div className="mt-4 pt-4 border-t border-neutral-800/80 space-y-4">
                  {/* Summary Card */}
                  <div className="p-3 bg-neutral-950/80 border border-neutral-850 rounded-lg">
                    <span className="block text-[10px] font-mono font-bold tracking-wider text-cyan-400 uppercase mb-1">
                      INTELLIGENCE BRIEF
                    </span>
                    <p className="text-xs text-neutral-300 leading-normal">{msg.structuredAnswer.summary}</p>
                  </div>

                  {/* Timeline block */}
                  {msg.structuredAnswer.timeline && (
                    <div>
                      <span className="block text-[10px] font-mono font-bold tracking-wider text-cyan-400 uppercase mb-2">
                        TIMELINE SEGMENTATION
                      </span>
                      <div className="relative border-l border-neutral-800 pl-3.5 ml-1 space-y-2">
                        {msg.structuredAnswer.timeline.map((item, idx) => (
                          <div key={idx} className="relative text-xs">
                            <span className="absolute -left-[19px] top-1.5 w-2 h-2 rounded-full bg-cyan-500 shadow-[0_0_6px_rgba(6,182,212,0.8)]" />
                            <span className="font-mono text-[10px] text-neutral-500 mr-2">{item.time}:</span>
                            <span className="text-neutral-300">{item.event}</span>
                            <span className="inline-block px-1 ml-1.5 text-[8px] font-mono bg-neutral-850 border border-neutral-800 text-neutral-400 rounded">
                              {item.status}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Entity links */}
                  {msg.structuredAnswer.entities && (
                    <div>
                      <span className="block text-[10px] font-mono font-bold tracking-wider text-cyan-400 uppercase mb-2">
                        DETECTOR LINKAGES
                      </span>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {msg.structuredAnswer.entities.map((ent, idx) => (
                          <div
                            key={idx}
                            onClick={() => onSelectEntity && onSelectEntity(ent.name)}
                            className="p-2.5 rounded-lg border border-neutral-800 bg-neutral-900/60 hover:bg-neutral-850 hover:border-neutral-700 transition cursor-pointer flex items-center justify-between"
                          >
                            <div>
                              <div className="flex items-center space-x-1.5">
                                <span className="text-xs font-bold text-neutral-200">{ent.name}</span>
                                <span className={`text-[8px] font-mono font-semibold uppercase px-1 rounded ${
                                  ent.risk === 'High' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 
                                  ent.risk === 'Medium' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 
                                  'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                                }`}>
                                  {ent.risk} Risk
                                </span>
                              </div>
                              <span className="text-[10px] font-mono text-neutral-500">{ent.type} - {ent.details}</span>
                            </div>
                            <Eye className="w-3.5 h-3.5 text-neutral-500 hover:text-cyan-400" />
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Actions list */}
                  {msg.structuredAnswer.recommendedActions && (
                    <div className="space-y-1.5">
                      <span className="block text-[10px] font-mono font-bold tracking-wider text-cyan-400 uppercase">
                        RECOMMENDED PROTOCOLS
                      </span>
                      <div className="space-y-1">
                        {msg.structuredAnswer.recommendedActions.map((act, idx) => (
                          <div key={idx} className="flex items-start text-xs text-neutral-300">
                            <CheckCircle2 className="w-3.5 h-3.5 text-cyan-500 mr-2 flex-shrink-0 mt-0.5" />
                            <span>{act}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Raw JSON viewer */}
                  {msg.structuredAnswer.jsonPayload && (
                    <div className="border border-neutral-800 rounded-lg overflow-hidden">
                      <button
                        onClick={() => toggleJson(msg.id)}
                        className="flex items-center justify-between w-full px-3 py-1.5 bg-neutral-900 border-b border-neutral-800 text-[10px] font-mono text-neutral-400 hover:bg-neutral-850 cursor-pointer"
                      >
                        <span className="flex items-center">
                          <FileCode className="w-3.5 h-3.5 mr-1.5 text-cyan-400" />
                          RAW DATA STRUCT (JSON)
                        </span>
                        <span className="text-[9px] hover:underline">
                          {expandedJson[msg.id] ? 'COLLAPSE' : 'EXPAND'}
                        </span>
                      </button>
                      {expandedJson[msg.id] && (
                        <pre className="p-3 bg-black text-[10px] font-mono text-emerald-400 overflow-x-auto max-h-40">
                          <code>{msg.structuredAnswer.jsonPayload}</code>
                        </pre>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* AI Typing Indicator */}
        {isTyping && (
          <div className="flex flex-col mr-auto items-start max-w-[80%]">
            <span className="text-[9px] font-mono text-neutral-600 mb-1">
              KSP-SENTINEL-CORE • COMPUTING LOGS...
            </span>
            <div className="p-3.5 rounded-xl border border-neutral-800 bg-neutral-900/20 text-neutral-400 rounded-tl-none flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input bar */}
      <div className="p-4 border-t border-neutral-800 bg-neutral-950">
        <div className="relative rounded-xl border border-neutral-800 bg-neutral-900/60 focus-within:border-cyan-500/40 focus-within:bg-neutral-900 transition duration-200">
          <textarea
            rows={1}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about any FIR, accused, location, or crime pattern..."
            className="w-full pl-4 pr-24 py-3 bg-transparent text-sm text-neutral-200 focus:outline-none resize-none placeholder:text-neutral-500 font-sans leading-relaxed"
          />
          <div className="absolute right-2.5 bottom-2 flex items-center space-x-2">
            <button
              onClick={() => alert('File upload simulated. Select FIR payload or JSON file.')}
              title="Attach File/Payload"
              className="p-1.5 rounded-lg text-neutral-500 hover:text-cyan-400 hover:bg-neutral-800 transition cursor-pointer"
            >
              <Paperclip className="w-4 h-4" />
            </button>
            <button
              onClick={() => handleSend()}
              className="p-1.5 rounded-lg bg-cyan-950 text-cyan-400 border border-cyan-500/20 hover:bg-cyan-900 hover:text-white transition cursor-pointer shadow-[0_0_10px_rgba(6,182,212,0.1)]"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
        <div className="flex items-center justify-between mt-2 px-1">
          <span className="text-[10px] font-mono text-neutral-600">
            SECURE PORTAL LINK • SSH ENCRYPTED SESSION
          </span>
          <span className="text-[10px] font-mono text-neutral-600">
            SHIFT + ENTER FOR MULTI-LINE
          </span>
        </div>
      </div>
    </div>
  );
}
