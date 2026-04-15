import { AlertTriangle, CheckCircle2, Clock, Droplet, ListChecks } from "lucide-react";

import type { InventoryItem } from "@/types/homeops";
import { getHealthColor, getStatusColor } from "@/utils/homeops";

interface DashboardPageProps {
  inventory: InventoryItem[];
  totalHealth: number;
  maintenanceDueCount: number;
  maintenanceDueLabel: string;
  estimatedSavings: number;
  pairedItemsCount: number;
  dashboardActionMessage: string;
  onOpenInventory: () => void;
  onOpenItemDetail: (item: InventoryItem) => void;
  onOpenProactiveGuide: (guideType: "hvac-filter" | "washer-check") => void;
}

export function DashboardPage({
  inventory,
  totalHealth,
  maintenanceDueCount,
  maintenanceDueLabel,
  estimatedSavings,
  pairedItemsCount,
  dashboardActionMessage,
  onOpenInventory,
  onOpenItemDetail,
  onOpenProactiveGuide,
}: DashboardPageProps) {
  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div>
        <div className="flex justify-between items-end mb-2">
          <div>
            <div className="text-teal-400 text-sm font-medium tracking-[2px]">WELCOME BACK</div>
            <h1 className="text-5xl font-semibold text-white tracking-tighter">Good morning, Sam</h1>
          </div>

          <div className="text-right">
            <div className="text-xs text-zinc-400">HOME HEALTH SCORE</div>
            <div className="flex items-baseline gap-1 justify-end">
              <span className="text-7xl font-semibold text-white tabular-nums">{totalHealth}</span>
              <span className="text-3xl text-zinc-400">/100</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <div className="bg-zinc-900 rounded-3xl p-6">
          <div className="flex justify-between">
            <div>
              <div className="text-sm text-zinc-400">Appliances</div>
              <div className="text-4xl font-semibold mt-2 text-white">{inventory.length}</div>
            </div>
            <div className="w-11 h-11 bg-teal-500/10 rounded-2xl flex items-center justify-center">
              <ListChecks className="text-teal-400" />
            </div>
          </div>
          <div className="mt-8 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
            <div className="h-1.5 w-[82%] bg-teal-400 rounded-full"></div>
          </div>
        </div>

        <div className="bg-zinc-900 rounded-3xl p-6 border border-amber-500/30">
          <div className="flex justify-between">
            <div>
              <div className="text-sm text-amber-400">Maintenance Due</div>
              <div className="text-4xl font-semibold mt-2 text-white">{maintenanceDueCount}</div>
            </div>
            <div className="w-11 h-11 bg-amber-500/10 rounded-2xl flex items-center justify-center">
              <Clock className="text-amber-400" />
            </div>
          </div>
          <div className="text-xs mt-6 text-amber-400">{maintenanceDueLabel}</div>
        </div>

        <div className="bg-zinc-900 rounded-3xl p-6">
          <div className="flex justify-between">
            <div>
              <div className="text-sm text-zinc-400">Est. Savings</div>
              <div className="text-4xl font-semibold mt-2 text-white">${estimatedSavings}</div>
            </div>
            <div className="w-11 h-11 bg-emerald-500/10 rounded-2xl flex items-center justify-center">
              <CheckCircle2 className="text-emerald-400" />
            </div>
          </div>
          <div className="text-xs mt-6 text-emerald-400">Conservative annual estimate from preventive maintenance</div>
        </div>

        <div className="bg-zinc-900 rounded-3xl p-6">
          <div className="flex justify-between">
            <div>
              <div className="text-sm text-zinc-400">Paired Items</div>
              <div className="text-4xl font-semibold mt-2 text-white">{pairedItemsCount}</div>
            </div>
            <div className="w-11 h-11 bg-purple-500/10 rounded-2xl flex items-center justify-center">
              <Droplet className="text-purple-400" />
            </div>
          </div>
          <div className="text-xs mt-6 text-purple-400">Based on inventory items with matched brand and model</div>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-7 bg-zinc-900 rounded-3xl p-8">
          <div className="flex items-center justify-between mb-6">
            <div className="font-medium">Your Home Inventory</div>
            <button
              onClick={onOpenInventory}
              className="text-teal-400 text-sm flex items-center gap-1 hover:text-teal-300"
            >
              Manage all <span className="text-xs">→</span>
            </button>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {inventory.slice(0, 4).map((item) => (
              <div
                key={item.id}
                onClick={() => onOpenItemDetail(item)}
                className="bg-zinc-950 hover:bg-zinc-800 border border-zinc-800 rounded-2xl p-5 cursor-pointer transition-all active:scale-[0.985]"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-medium text-white">{item.name}</div>
                    <div className="text-xs text-zinc-500 mt-0.5">{item.model}</div>
                  </div>
                  <div className={`px-3 py-0.5 text-xs rounded-3xl font-medium ${getStatusColor(item.status)}`}>
                    {item.status}
                  </div>
                </div>

                <div className="mt-8 flex justify-between items-end">
                  <div>
                    <div className="text-xs text-zinc-400">NEXT SERVICE</div>
                    <div className="font-mono text-lg text-white">{item.nextMaintenance}</div>
                  </div>

                  <div className={`font-mono text-4xl font-semibold tabular-nums ${getHealthColor(item.health)}`}>
                    {item.health}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="col-span-5 bg-zinc-900 rounded-3xl p-8">
          <div className="font-medium mb-6 flex items-center gap-2">
            <AlertTriangle className="text-orange-400" /> Proactive Insights
          </div>

          {dashboardActionMessage && (
            <div className="mb-4 rounded-2xl border border-teal-500/30 bg-teal-500/10 px-4 py-3 text-xs text-teal-300">
              {dashboardActionMessage}
            </div>
          )}

          <div className="space-y-4">
            <div className="flex gap-4 bg-zinc-950 border-l-4 border-orange-400 p-5 rounded-r-2xl">
              <div className="mt-px">
                <Clock className="w-5 h-5 text-orange-400" />
              </div>
              <div className="flex-1">
                <div className="font-medium text-sm">HVAC Filter Replacement</div>
                <div className="text-xs text-zinc-400 mt-1 leading-snug">Due in 3 days. Size: 16x25x1. I can show you how to replace it in under 7 minutes.</div>
                <button
                  onClick={() => onOpenProactiveGuide("hvac-filter")}
                  className="mt-4 text-xs bg-white text-black px-4 py-2 rounded-2xl font-medium"
                >
                  View Instructions
                </button>
              </div>
            </div>

            <div className="flex gap-4 bg-zinc-950 p-5 rounded-2xl">
              <div className="mt-px">
                <CheckCircle2 className="w-5 h-5 text-teal-400" />
              </div>
              <div className="flex-1">
                <div className="font-medium text-sm">Washer is running efficiently</div>
                <div className="text-xs text-zinc-400 mt-1">No unusual vibration patterns detected this month.</div>
                <button
                  onClick={() => onOpenProactiveGuide("washer-check")}
                  className="mt-4 text-xs border border-zinc-600 hover:bg-zinc-800 px-4 py-2 rounded-2xl font-medium"
                >
                  Run Preventive Checklist
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
