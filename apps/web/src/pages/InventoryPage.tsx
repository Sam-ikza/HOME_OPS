import { Plus, Search } from "lucide-react";

import type { InventoryItem } from "@/types/homeops";
import { getHealthColor, getStatusColor } from "@/utils/homeops";

interface InventoryPageProps {
  searchTerm: string;
  onChangeSearchTerm: (value: string) => void;
  onOpenAddItemModal: () => void;
  isInventoryLoading: boolean;
  filteredInventory: InventoryItem[];
  onOpenItemDetail: (item: InventoryItem) => void;
}

export function InventoryPage({
  searchTerm,
  onChangeSearchTerm,
  onOpenAddItemModal,
  isInventoryLoading,
  filteredInventory,
  onOpenItemDetail,
}: InventoryPageProps) {
  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-5 top-3.5 text-zinc-500 w-4 h-4" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => onChangeSearchTerm(e.target.value)}
            placeholder="Search appliances or model numbers..."
            className="w-full bg-zinc-900 border border-zinc-700 focus:border-teal-400 pl-12 py-3.5 rounded-3xl text-sm outline-none"
          />
        </div>

        <button
          onClick={onOpenAddItemModal}
          className="flex items-center gap-2 bg-white text-black px-6 py-3 rounded-3xl text-sm font-medium"
        >
          <Plus className="w-4 h-4" /> Add New Item
        </button>
      </div>

      {isInventoryLoading && (
        <div className="mb-4 text-xs text-zinc-400">Loading inventory from database...</div>
      )}

      <div className="grid grid-cols-3 gap-5">
        {filteredInventory.map((item) => (
          <div
            key={item.id}
            onClick={() => onOpenItemDetail(item)}
            className="bg-zinc-900 rounded-3xl p-6 cursor-pointer hover:-translate-y-1 transition-all border border-transparent hover:border-zinc-700 group"
          >
            <div className="flex justify-between items-start">
              <div className="text-xs uppercase tracking-widest text-teal-400">{item.category}</div>
              <div className={`px-4 py-1 text-[10px] font-mono rounded-3xl ${getStatusColor(item.status)}`}>{item.status.toUpperCase()}</div>
            </div>

            <div className="mt-5 text-2xl font-semibold text-white leading-none">{item.name}</div>
            <div className="font-mono text-xs text-zinc-500 mt-1">{item.model}</div>

            <div className="mt-auto pt-12 flex items-center justify-between">
              <div>
                <div className="text-xs text-zinc-400">HEALTH</div>
                <div className={`text-5xl font-semibold tabular-nums ${getHealthColor(item.health)}`}>{item.health}</div>
              </div>

              <div className="text-right text-xs">
                <div className="text-zinc-400">DUE</div>
                <div className="font-medium text-white">{item.nextMaintenance}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
