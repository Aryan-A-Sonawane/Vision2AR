import React, { useState, useEffect, useRef } from 'react';
import { X, ChevronDown, ChevronUp, Terminal, Database, Brain, FileText } from 'lucide-react';

interface DebugLog {
  timestamp: string;
  source: 'ML_Model' | 'OEM' | 'iFixit' | 'YouTube' | 'Backend' | 'Frontend';
  action: string;
  details: any;
  level: 'info' | 'success' | 'warning' | 'error';
}

interface DebugTerminalProps {
  isOpen: boolean;
  onClose: () => void;
  logs: DebugLog[];
}

const SOURCE_ICONS: Record<string, any> = {
  ML_Model: Brain,
  OEM: FileText,
  iFixit: FileText,
  YouTube: FileText,
  Backend: Database,
  Frontend: Terminal
};

const SOURCE_COLORS: Record<string, string> = {
  ML_Model: 'text-purple-600',
  OEM: 'text-blue-600',
  iFixit: 'text-orange-600',
  YouTube: 'text-red-600',
  Backend: 'text-green-600',
  Frontend: 'text-cyan-600'
};

const LEVEL_COLORS: Record<string, string> = {
  info: 'text-neutral-400',
  success: 'text-green-500',
  warning: 'text-yellow-500',
  error: 'text-red-500'
};

export default function DebugTerminal({ isOpen, onClose, logs }: DebugTerminalProps) {
  const [isMinimized, setIsMinimized] = useState(false);
  const [filter, setFilter] = useState<string | null>(null);
  const [terminalHeight, setTerminalHeight] = useState(384); // 96 * 4 = 384px (h-96 default)
  const [isDragging, setIsDragging] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  // Handle vertical resizing
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    e.preventDefault();
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      
      const newHeight = window.innerHeight - e.clientY;
      // Constrain between 100px and 80% of viewport
      const constrainedHeight = Math.max(100, Math.min(newHeight, window.innerHeight * 0.8));
      setTerminalHeight(constrainedHeight);
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]);

  if (!isOpen) return null;

  const filteredLogs = filter 
    ? logs.filter(log => log.source === filter)
    : logs;

  const sourceCounts = logs.reduce((acc, log) => {
    acc[log.source] = (acc[log.source] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div 
      className={`fixed bottom-0 left-0 right-0 bg-neutral-900 border-t-2 border-neutral-700 shadow-2xl z-50 transition-all ${
        isMinimized ? 'h-12' : ''
      }`}
      style={!isMinimized ? { height: `${terminalHeight}px` } : undefined}
    >
      {/* Vertical Drag Handle */}
      {!isMinimized && (
        <div
          onMouseDown={handleMouseDown}
          className={`absolute top-0 left-0 right-0 h-1 bg-neutral-700 hover:bg-primary-500 transition-colors cursor-ns-resize z-10 ${
            isDragging ? 'bg-primary-500' : ''
          }`}
          title="Drag to resize terminal"
        >
          <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-12 h-1 bg-neutral-500 rounded-b" />
        </div>
      )}
      
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-neutral-800 border-b border-neutral-700">
        <div className="flex items-center gap-3">
          <Terminal className="w-4 h-4 text-green-500" />
          <span className="text-sm font-mono text-green-500">debug_terminal</span>
          <span className="text-xs text-neutral-500">
            {logs.length} events
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Source Filter Pills */}
          <div className="flex gap-1">
            {Object.entries(sourceCounts).map(([source, count]) => {
              const Icon = SOURCE_ICONS[source];
              const isActive = filter === source;
              
              return (
                <button
                  key={source}
                  onClick={() => setFilter(isActive ? null : source)}
                  className={`px-2 py-1 rounded text-xs font-mono flex items-center gap-1 transition-colors ${
                    isActive
                      ? 'bg-neutral-700 text-white'
                      : 'bg-neutral-900 text-neutral-400 hover:bg-neutral-700'
                  }`}
                >
                  <Icon className={`w-3 h-3 ${SOURCE_COLORS[source]}`} />
                  {source}
                  <span className="text-neutral-500">({count})</span>
                </button>
              );
            })}
          </div>

          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="text-neutral-400 hover:text-white"
          >
            {isMinimized ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>

          <button
            onClick={onClose}
            className="text-neutral-400 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Logs */}
      {!isMinimized && (
        <div className="h-full overflow-y-auto p-4 font-mono text-xs">
          {filteredLogs.length === 0 ? (
            <div className="text-neutral-500 text-center py-8">
              No debug logs yet. Start a diagnosis to see the flow.
            </div>
          ) : (
            filteredLogs.map((log, index) => {
              const Icon = SOURCE_ICONS[log.source];
              
              return (
                <div
                  key={index}
                  className="mb-3 border-l-2 border-neutral-700 pl-3 hover:border-neutral-500 transition-colors"
                >
                  {/* Log Header */}
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`${LEVEL_COLORS[log.level]}`}>
                      {log.level === 'error' && '✗'}
                      {log.level === 'success' && '✓'}
                      {log.level === 'warning' && '⚠'}
                      {log.level === 'info' && '●'}
                    </span>
                    
                    <span className="text-neutral-500">
                      [{log.timestamp}]
                    </span>
                    
                    <Icon className={`w-3 h-3 ${SOURCE_COLORS[log.source]}`} />
                    <span className={`${SOURCE_COLORS[log.source]} font-semibold`}>
                      {log.source}
                    </span>
                    
                    <span className="text-neutral-300">
                      {log.action}
                    </span>
                  </div>

                  {/* Log Details */}
                  {log.details && (
                    <div className="mt-1 bg-neutral-800 rounded p-2 text-neutral-400">
                      {typeof log.details === 'string' ? (
                        <div>{log.details}</div>
                      ) : (
                        <pre className="whitespace-pre-wrap break-words text-xs">
                          {JSON.stringify(log.details, null, 2)}
                        </pre>
                      )}
                    </div>
                  )}
                </div>
              );
            })
          )}
          <div ref={logsEndRef} />
        </div>
      )}
    </div>
  );
}

// Hook for managing debug logs
export function useDebugTerminal() {
  const [logs, setLogs] = useState<DebugLog[]>([]);
  const [isOpen, setIsOpen] = useState(true); // Open by default

  const addLog = (
    source: DebugLog['source'],
    action: string,
    details: any = null,
    level: DebugLog['level'] = 'info'
  ) => {
    const log: DebugLog = {
      timestamp: new Date().toLocaleTimeString(),
      source,
      action,
      details,
      level
    };
    setLogs(prev => [...prev, log]);
  };

  const clearLogs = () => setLogs([]);
  
  const toggleTerminal = () => setIsOpen(prev => !prev);

  return {
    logs,
    isOpen,
    addLog,
    clearLogs,
    toggleTerminal,
    setIsOpen
  };
}
