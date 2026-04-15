import { Bell, Camera, Home, ListChecks, MessageCircle, User } from "lucide-react";

import type { ActiveTab } from "@/types/homeops";

interface SidebarProps {
  activeTab: ActiveTab;
  onSelectTab: (tab: ActiveTab) => void;
}

const NAV_ITEMS: Array<{ id: ActiveTab; label: string; icon: typeof Home }> = [
  { id: "dashboard", label: "Dashboard", icon: Home },
  { id: "inventory", label: "Inventory", icon: ListChecks },
  { id: "chat", label: "AI Assistant", icon: MessageCircle },
  { id: "scan", label: "Home Scan", icon: Camera },
  { id: "alerts", label: "Alerts", icon: Bell },
];

export function Sidebar({ activeTab, onSelectTab }: SidebarProps) {
  return (
    <div className="w-72 bg-zinc-900 border-r border-zinc-800 flex flex-col">
      <div className="p-6 border-b border-zinc-800">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-teal-500 rounded-2xl flex items-center justify-center">
            <Home className="w-5 h-5 text-white" />
          </div>
          <div>
            <button
              type="button"
              onClick={() => onSelectTab("dashboard")}
              className="font-semibold text-2xl tracking-tighter text-white hover:text-teal-300 transition-colors"
            >
              HOME_SENSE
            </button>
            <div className="text-[10px] text-teal-400 -mt-1">your home's memory</div>
          </div>
        </div>
      </div>

      <div className="px-3 pt-6">
        <div className="px-3 mb-2 text-xs font-medium text-zinc-500">MAIN</div>

        <nav className="space-y-1">
          {NAV_ITEMS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onSelectTab(tab.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-sm transition-all ${
                  isActive ? "bg-teal-500/10 text-teal-400" : "hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200"
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? "text-teal-400" : ""}`} />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      <div className="mt-auto p-4 border-t border-zinc-800">
        <div className="flex items-center gap-3 bg-zinc-800 rounded-3xl p-2">
          <div className="w-9 h-9 bg-zinc-700 rounded-2xl flex items-center justify-center">
            <User className="w-4 h-4" />
          </div>
          <div className="text-sm">
            <div>SAM</div>
            <div className="text-xs text-zinc-500">123 Maple Lane</div>
          </div>
        </div>
      </div>
    </div>
  );
}
