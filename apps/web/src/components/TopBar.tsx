import { Droplet, Settings, ThermometerSun } from "lucide-react";

import type { ActiveTab } from "@/types/homeops";

interface TopBarProps {
  activeTab: ActiveTab;
  backendReady: boolean | null;
  temperatureF: number | null;
  humidityPct: number | null;
}

export function TopBar({ activeTab, backendReady, temperatureF, humidityPct }: TopBarProps) {
  return (
    <div className="h-16 bg-zinc-900 border-b border-zinc-800 px-8 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div className="text-xl font-semibold text-white capitalize">{activeTab}</div>
        <div className={`px-3 py-1 text-xs rounded-full font-medium ${backendReady ? "bg-teal-500/10 text-teal-400" : "bg-red-500/10 text-red-400"}`}>
          {backendReady ? "BACKEND CONNECTED" : "BACKEND OFFLINE"}
        </div>
      </div>

      <div className="flex items-center gap-6 text-sm">
        <div className="flex items-center gap-2 bg-zinc-800 px-5 py-2 rounded-3xl">
          <ThermometerSun className="w-4 h-4 text-orange-400" />
          <span>{temperatureF === null ? "Weather --" : `${temperatureF}°F`}</span>
        </div>
        <div className="flex items-center gap-2 bg-zinc-800 px-5 py-2 rounded-3xl">
          <Droplet className="w-4 h-4 text-sky-400" />
          <span>{humidityPct === null ? "Humidity --" : `Humidity ${humidityPct}%`}</span>
        </div>

        <div className="w-8 h-8 bg-zinc-700 rounded-2xl flex items-center justify-center cursor-pointer hover:bg-zinc-600">
          <Settings className="w-4 h-4" />
        </div>
      </div>
    </div>
  );
}
