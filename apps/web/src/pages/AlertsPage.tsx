import { AlertTriangle, CheckCircle2, Clock } from "lucide-react";

import type { AlertItem, AlertSeverity, AlertStatus } from "@/types/homeops";

interface AlertsPageProps {
  activeAlerts: AlertItem[];
  handledAlerts: AlertItem[];
  onDismissAlert: (alertId: number) => void;
  onTakeActionOnAlert: (alert: AlertItem) => void;
}

const renderAlertIcon = (severity: AlertSeverity) => {
  if (severity === "high") return <AlertTriangle className="text-red-400 w-6 h-6 mt-1" />;
  if (severity === "medium") return <Clock className="text-amber-400 w-6 h-6 mt-1" />;
  return <CheckCircle2 className="text-sky-400 w-6 h-6 mt-1" />;
};

const getHandledBadge = (status: AlertStatus) => {
  if (status === "actioned") {
    return <span className="text-[10px] px-3 py-1 rounded-full bg-teal-500/15 text-teal-300">SENT TO AI</span>;
  }
  return <span className="text-[10px] px-3 py-1 rounded-full bg-zinc-700 text-zinc-300">DISMISSED</span>;
};

export function AlertsPage({ activeAlerts, handledAlerts, onDismissAlert, onTakeActionOnAlert }: AlertsPageProps) {
  return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-zinc-900 rounded-3xl p-8">
        <div className="uppercase text-xs tracking-widest text-orange-400 mb-3">
          ACTIVE NOTIFICATIONS • {activeAlerts.length}
        </div>
        <p className="text-xs text-zinc-400 mb-6">
          Dismiss removes the alert from active notifications. Take Action opens AI chat and sends this alert for a guided response.
        </p>

        {activeAlerts.length === 0 ? (
          <div className="border border-zinc-800 bg-zinc-950 rounded-3xl p-8 text-center">
            <div className="text-lg text-white">All alerts are handled.</div>
            <div className="text-sm text-zinc-400 mt-2">New active notifications will appear here.</div>
          </div>
        ) : (
          <div className="space-y-3">
            {activeAlerts.map((alert) => (
              <div key={alert.id} className="border border-zinc-800 bg-zinc-950 rounded-3xl p-6 flex gap-6 group">
                <div>{renderAlertIcon(alert.severity)}</div>
                <div className="flex-1">
                  <div className="flex justify-between">
                    <div className="font-medium text-lg text-white">{alert.title}</div>
                    <div className="text-xs text-zinc-500 whitespace-nowrap">{alert.time}</div>
                  </div>
                  <p className="text-sm text-zinc-400 mt-2 pr-12">{alert.desc}</p>

                  <div className="flex gap-3 mt-7">
                    <button
                      onClick={() => onDismissAlert(alert.id)}
                      className="text-xs border border-white/30 hover:bg-white/5 px-7 py-3 rounded-2xl transition-colors"
                    >
                      DISMISS
                    </button>
                    <button
                      onClick={() => onTakeActionOnAlert(alert)}
                      className="text-xs bg-white text-black px-7 py-3 rounded-2xl"
                    >
                      TAKE ACTION
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {handledAlerts.length > 0 && (
          <div className="mt-8">
            <div className="uppercase text-xs tracking-widest text-zinc-400 mb-4">
              RECENTLY HANDLED • {handledAlerts.length}
            </div>
            <div className="space-y-3">
              {handledAlerts.map((alert) => (
                <div key={alert.id} className="border border-zinc-800/70 bg-zinc-950/70 rounded-3xl p-5 flex items-center justify-between gap-4">
                  <div>
                    <div className="text-sm text-zinc-200">{alert.title}</div>
                    <div className="text-xs text-zinc-500 mt-1">{alert.time}</div>
                  </div>
                  {getHandledBadge(alert.status)}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
