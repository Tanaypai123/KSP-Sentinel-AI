import { MoreHorizontal, FileText, GitMerge, FileQuestion } from 'lucide-react';
import { memo } from 'react';
import { mockFIRs } from '../mockData';
import type { FIR } from '../types';

interface BottomSectionProps {
  onSelectFIR: (fir: FIR) => void;
  onSelectSearch: (query: string) => void;
}

const BottomSection = memo(function BottomSection({ onSelectFIR }: BottomSectionProps) {
  const filteredData = mockFIRs;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Closed':
        return 'text-emerald-400 bg-emerald-500/10 border border-emerald-500/25';
      case 'Open':
        return 'text-indigo-400 bg-indigo-500/10 border border-indigo-500/25';
      default: // Investigation / Under Review
        return 'text-cyan-400 bg-cyan-500/10 border border-cyan-500/25';
    }
  };

  return (
    <>
      <div className="premium-card p-4 overflow-hidden flex flex-col justify-between break-inside-avoid mb-6">
        <div className="flex items-center justify-between pb-3 border-b border-neutral-800/80">
          <div className="flex items-center space-x-3">
            <FileText className="w-5 h-5 text-cyan-400" />
            <span className="text-sm font-sans font-semibold tracking-wide text-white">
              Recent First Information Reports (FIR)
            </span>
          </div>
          <span className="text-xs font-mono text-neutral-500 uppercase">
            LIVE SYNC • ACTIVE DISTRICT
          </span>
        </div>

        <div className="overflow-x-auto mt-4 overflow-y-auto max-h-[350px]">
          <table className="w-full text-left text-[13px] font-sans">
            <thead className="sticky top-0 bg-[#0c0c0e]/90 backdrop-blur z-10">
              <tr className="border-b border-neutral-800/80 text-neutral-500 font-sans font-medium text-[11px] uppercase tracking-widest">
                <th className="py-3.5 px-4 font-semibold">FIR ID</th>
                <th className="py-3.5 px-4 font-semibold">Date</th>
                <th className="py-3.5 px-4 font-semibold">Subject</th>
                <th className="py-3.5 px-4 font-semibold">Status</th>
                <th className="py-3.5 px-4 font-semibold">District</th>
                <th className="py-3.5 px-4 font-semibold">Officer</th>
                <th className="py-3.5 px-4 text-right font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-800/40 relative">
              {filteredData.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-16 text-center">
                    <div className="flex flex-col items-center justify-center text-neutral-500">
                      <FileQuestion className="w-8 h-8 mb-3 opacity-50" />
                      <span className="text-[13px] font-sans">No matching reports found</span>
                      <span className="text-[10px] font-mono mt-1 opacity-70">Adjust filters to see results</span>
                    </div>
                  </td>
                </tr>
              )}
              {filteredData.map((fir) => (
                <tr 
                  key={fir.id}
                  onClick={() => onSelectFIR(fir)}
                  className="group hover:bg-neutral-800/30 transition-colors duration-200 cursor-pointer"
                >
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-medium ${getStatusBadge(fir.status)}`}>
                      {fir.status.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      <span className="text-[11.5px] font-mono text-neutral-400 group-hover:text-neutral-300 transition-colors">{fir.dateRegistered}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-[13px] text-neutral-300 group-hover:text-white transition-colors line-clamp-1">{fir.title}</span>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="flex items-center space-x-2 text-neutral-400 group-hover:text-neutral-300 transition-colors">
                      <span className="text-[11px] uppercase tracking-wide">{fir.location}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-cyan-500 opacity-80"></span>
                      <span className="text-[11.5px] font-mono text-neutral-300">{fir.officersAssigned[0]}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-right">
                    <div className="flex items-center space-x-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-cyan-500"></span>
                      <span className="text-[11px] font-mono text-neutral-300">{fir.officersAssigned[0]}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3.5 whitespace-nowrap text-right">
                    <button className="p-1.5 rounded bg-transparent hover:bg-neutral-800 text-neutral-500 hover:text-white transition-colors">
                      <MoreHorizontal className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="flex flex-col h-full break-inside-avoid mb-6">
        {/* Investigation Timeline */}
        <div className="premium-card p-4 flex-1 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-neutral-800/80">
            <div className="flex items-center space-x-3">
              <GitMerge className="w-[18px] h-[18px] text-indigo-400" />
              <span className="text-[13px] font-sans font-semibold tracking-wide text-white">
                Investigation Timeline
              </span>
            </div>
            <span className="bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-[10px] font-mono px-2 py-0.5 rounded uppercase">
              Rajesh Gowda Syndicate
            </span>
          </div>

          <div className="relative pl-3 space-y-5 pt-2 border-l border-neutral-800/60 ml-2">
            
            <div className="relative">
              <div className="absolute -left-[17px] top-1 w-2.5 h-2.5 rounded-full bg-indigo-500 ring-4 ring-[#0c0c0e]" />
              <div className="pl-4">
                <span className="text-[10px] font-mono text-neutral-500">TODAY, 14:30</span>
                <p className="text-[13px] text-neutral-200 mt-0.5 font-medium leading-snug">Raid initiated at Koramangala hideout.</p>
                <span className="inline-block mt-1.5 px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-[9px] font-mono border border-emerald-500/20">IN PROGRESS</span>
              </div>
            </div>

            <div className="relative">
              <div className="absolute -left-[17px] top-1 w-2.5 h-2.5 rounded-full bg-neutral-700 ring-4 ring-[#0c0c0e]" />
              <div className="pl-4">
                <span className="text-[10px] font-mono text-neutral-500">YESTERDAY, 19:15</span>
                <p className="text-[13px] text-neutral-300 mt-0.5 leading-snug">Warrant approved by Magistrate.</p>
              </div>
            </div>

            <div className="relative">
              <div className="absolute -left-[17px] top-1 w-2.5 h-2.5 rounded-full bg-neutral-700 ring-4 ring-[#0c0c0e]" />
              <div className="pl-4">
                <span className="text-[10px] font-mono text-neutral-500">YESTERDAY, 09:00</span>
                <p className="text-[13px] text-neutral-300 mt-0.5 leading-snug">AI identified signature match from 4 cyber extortion FIRs.</p>
              </div>
            </div>
            
            <div className="relative">
              <div className="absolute -left-[17px] top-1 w-2.5 h-2.5 rounded-full bg-neutral-700 ring-4 ring-[#0c0c0e]" />
              <div className="pl-4">
                <span className="text-[10px] font-mono text-neutral-500">AUG 12, 11:30</span>
                <p className="text-[13px] text-neutral-400 mt-0.5 leading-snug opacity-80">Initial complaint filed by victim.</p>
              </div>
            </div>

          </div>
        </div>
      </div>
    </>
  );
});

export default BottomSection;
