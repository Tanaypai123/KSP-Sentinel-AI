import React, { Component } from 'react';
import type { ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Uncaught rendering error:', error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: undefined });
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 rounded-xl border border-rose-500/20 bg-rose-950/10 flex flex-col items-center justify-center space-y-4 my-4 animate-in fade-in zoom-in duration-300">
          <AlertTriangle className="w-10 h-10 text-rose-500/80 drop-shadow-[0_0_8px_rgba(244,63,94,0.4)]" />
          <div className="text-center">
            <h3 className="text-sm font-mono font-bold text-rose-400 uppercase mb-2">Rendering Error</h3>
            <p className="text-sm text-neutral-300 max-w-md">
              Unable to render search results. The backend returned valid data, but a UI rendering error occurred.
            </p>
          </div>
          <button
            onClick={this.handleReset}
            className="flex items-center px-4 py-2 border border-rose-500/30 rounded-lg text-xs font-mono text-rose-300 hover:bg-rose-950/40 hover:text-white transition-all cursor-pointer"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Reset UI
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
