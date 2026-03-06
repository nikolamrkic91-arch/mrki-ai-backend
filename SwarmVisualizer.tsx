import React from 'react';

export const SwarmVisualizer = ({ agents }) => {
  return (
    <div className="grid grid-cols-8 gap-2 p-4 bg-slate-900 rounded-xl">
      {agents.map((agent) => (
        <div key={agent.id} className={`p-2 border rounded ${agent.isActive ? 'border-green-500 animate-pulse' : 'border-slate-700'}`}>
          <p className="text-[10px] text-slate-400 uppercase font-bold">{agent.role}</p>
          <div className={`h-1 w-full mt-1 ${agent.isActive ? 'bg-green-500' : 'bg-slate-700'}`} />
        </div>
      ))}
    </div>
  );
};
