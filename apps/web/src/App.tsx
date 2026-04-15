import { useEffect, useMemo, useRef, useState } from "react";

import { AlertsPage } from "@/pages/AlertsPage";
import { ChatPage } from "@/pages/ChatPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { InventoryPage } from "@/pages/InventoryPage";
import { ScanPage } from "@/pages/ScanPage";
import { Sidebar } from "@/components/Sidebar";
import { TopBar } from "@/components/TopBar";
import type {
  ActiveTab,
  AlertItem,
  ChatApiResponse,
  HealthResponse,
  InventoryApiResponse,
  InventoryItem,
  Message,
  ScanDiagnosisApiResponse,
} from "@/types/homeops";
import {
  DEFAULT_ALERT_SEED,
  formatMaintenanceCountdown,
  formatStoredDate,
  getOrCreateUserKey,
  parseDaysUntilMaintenance,
  toFahrenheit,
} from "@/utils/homeops";

const INITIAL_INVENTORY: InventoryItem[] = [
  {
    id: 1,
    name: "Samsung Washer",
    category: "Appliances",
    brand: "Samsung",
    serialNumber: "SAMS-WF45-2107",
    model: "WF45R6100AW",
    purchaseDate: "Mar 2023",
    lastServiced: "2 months ago",
    nextMaintenance: "14 days",
    status: "good",
    health: 92,
  },
  {
    id: 2,
    name: "LG Refrigerator",
    category: "Appliances",
    brand: "LG",
    serialNumber: "LG-LFXS-9821",
    model: "LFXS28968S",
    purchaseDate: "Jan 2022",
    lastServiced: "1 month ago",
    nextMaintenance: "45 days",
    status: "good",
    health: 88,
  },
  {
    id: 3,
    name: "Honeywell HVAC",
    category: "Systems",
    brand: "Honeywell",
    serialNumber: "HON-HVAC-5520",
    model: "TH6320R1004",
    purchaseDate: "Nov 2021",
    lastServiced: "4 months ago",
    nextMaintenance: "3 days",
    status: "attention",
    health: 64,
  },
  {
    id: 4,
    name: "Bosch Dishwasher",
    category: "Appliances",
    brand: "Bosch",
    serialNumber: "BOSCH-SHP-1765",
    model: "SHP78CM5N",
    purchaseDate: "Jun 2023",
    lastServiced: "3 weeks ago",
    nextMaintenance: "60 days",
    status: "good",
    health: 95,
  },
];

const INITIAL_MESSAGES: Message[] = [
  {
    id: 1,
    text: "Hi! How can I help with your home today?",
    isUser: false,
    timestamp: "just now",
  },
];

export function App() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("dashboard");
  const [inventory, setInventory] = useState<InventoryItem[]>(INITIAL_INVENTORY);
  const [searchTerm, setSearchTerm] = useState("");
  const [isInventoryLoading, setIsInventoryLoading] = useState(false);

  const [messages, setMessages] = useState<Message[]>(INITIAL_MESSAGES);
  const [chatInput, setChatInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [backendReady, setBackendReady] = useState<boolean | null>(null);
  const [apiError, setApiError] = useState("");
  const [dashboardActionMessage, setDashboardActionMessage] = useState("");

  const [temperatureF, setTemperatureF] = useState<number | null>(null);
  const [humidityPct, setHumidityPct] = useState<number | null>(null);

  const [scanFile, setScanFile] = useState<File | null>(null);
  const [scanIssueText, setScanIssueText] = useState("");
  const [scanErrorCodeHint, setScanErrorCodeHint] = useState("");
  const [scanMessage, setScanMessage] = useState("Upload an appliance sticker or receipt image to analyze it.");
  const [isScanning, setIsScanning] = useState(false);
  const [scanDiagnosis, setScanDiagnosis] = useState<ScanDiagnosisApiResponse | null>(null);
  const [scanSolved, setScanSolved] = useState<boolean | null>(null);
  const [scanResults, setScanResults] = useState<string[]>([]);

  const userKeyRef = useRef<string>(getOrCreateUserKey());
  const chatBottomRef = useRef<HTMLDivElement | null>(null);

  const filteredInventory = useMemo(
    () =>
      inventory.filter(
        (item) =>
          item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          item.model.toLowerCase().includes(searchTerm.toLowerCase()),
      ),
    [inventory, searchTerm],
  );

  const activeAlerts = useMemo(() => alerts.filter((item) => item.status === "active"), [alerts]);
  const handledAlerts = useMemo(() => alerts.filter((item) => item.status !== "active"), [alerts]);

  const totalHealth = useMemo(() => {
    if (inventory.length === 0) return 0;
    return Math.round(inventory.reduce((sum, item) => sum + item.health, 0) / inventory.length);
  }, [inventory]);

  const maintenanceDueCount = useMemo(() => {
    return inventory.reduce((count, item) => {
      const days = parseDaysUntilMaintenance(item.nextMaintenance);
      return count + (days !== null && days <= 7 ? 1 : 0);
    }, 0);
  }, [inventory]);

  const maintenanceDueLabel = maintenanceDueCount > 0
    ? `${maintenanceDueCount} item${maintenanceDueCount === 1 ? "" : "s"} due in 7 days`
    : "No urgent maintenance this week";

  const estimatedSavings = useMemo(() => Math.max(120, Math.round(inventory.length * 72)), [inventory.length]);

  const pairedItemsCount = useMemo(
    () => inventory.filter((item) => Boolean(item.brand?.trim()) && Boolean(item.model?.trim())).length,
    [inventory],
  );

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  useEffect(() => {
    let ignore = false;

    const loadHealth = async () => {
      try {
        const response = await fetch("/health");
        if (!response.ok) throw new Error("Health check failed");

        const data: HealthResponse = await response.json();
        if (!ignore) {
          setBackendReady(Boolean(data.ok && data.checks?.database_ok));
        }
      } catch {
        if (!ignore) setBackendReady(false);
      }
    };

    void loadHealth();
    return () => {
      ignore = true;
    };
  }, []);

  useEffect(() => {
    let ignore = false;

    const loadAlerts = async () => {
      try {
        const response = await fetch("/api/alerts/bootstrap", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-HomeOps-User-Key": userKeyRef.current,
          },
          body: JSON.stringify({ alerts: DEFAULT_ALERT_SEED }),
        });

        if (!response.ok) throw new Error("Alert bootstrap failed");

        const data: AlertItem[] = await response.json();
        if (!ignore) setAlerts(data);
      } catch {
        if (!ignore) {
          setAlerts(DEFAULT_ALERT_SEED.map((item, index) => ({ ...item, id: index + 1, status: "active" })));
          setApiError("Alerts are running in local-only mode. Backend sync is temporarily unavailable.");
        }
      }
    };

    void loadAlerts();
    return () => {
      ignore = true;
    };
  }, []);

  useEffect(() => {
    let ignore = false;

    const loadInventory = async () => {
      setIsInventoryLoading(true);
      try {
        const response = await fetch("/api/inventory", {
          headers: { "X-HomeOps-User-Key": userKeyRef.current },
        });

        if (!response.ok) {
          throw new Error("Inventory request failed");
        }

        const data: InventoryApiResponse[] = await response.json();

        if (!ignore && data.length > 0) {
          setInventory(
            data.map((item) => {
              const maintenanceDays = parseDaysUntilMaintenance(item.next_maintenance);
              return {
                id: item.id,
                dbId: item.id,
                name: item.name,
                category: item.category || "Appliances",
                brand: item.brand || "",
                model: item.model_number || "Unknown",
                serialNumber: item.serial_number || "",
                purchaseDate: formatStoredDate(item.purchase_date, "Unknown"),
                lastServiced: formatStoredDate(item.last_serviced, "Not recorded"),
                nextMaintenance: formatMaintenanceCountdown(
                  maintenanceDays,
                  item.next_maintenance?.trim() || "Not scheduled",
                ),
                notes: item.notes || "",
                status: item.status === "critical" || item.status === "attention" ? item.status : "good",
                health: Number.isFinite(item.health) ? item.health : 80,
              } as InventoryItem;
            }),
          );
        }
      } catch {
        if (!ignore) {
          setApiError("Inventory is running in local-only mode. Backend sync is temporarily unavailable.");
        }
      } finally {
        if (!ignore) setIsInventoryLoading(false);
      }
    };

    void loadInventory();
    return () => {
      ignore = true;
    };
  }, []);

  useEffect(() => {
    let ignore = false;

    const loadWeather = async () => {
      try {
        const latitude = 30.7333;
        const longitude = 76.7794;
        const response = await fetch(
          `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}` +
            "&current=temperature_2m,relative_humidity_2m&temperature_unit=celsius",
        );

        if (!response.ok) throw new Error("Weather request failed");

        const data = await response.json();
        const temp = Number(data?.current?.temperature_2m);
        const humidity = Number(data?.current?.relative_humidity_2m);

        if (!ignore) {
          if (Number.isFinite(temp)) setTemperatureF(toFahrenheit(temp));
          if (Number.isFinite(humidity)) setHumidityPct(Math.round(humidity));
        }
      } catch {
        if (!ignore) {
          setTemperatureF(null);
          setHumidityPct(null);
        }
      }
    };

    void loadWeather();
    return () => {
      ignore = true;
    };
  }, []);

  const appendAssistantMessage = (text: string) => {
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now() + Math.floor(Math.random() * 1000),
        text,
        isUser: false,
        timestamp: "just now",
      },
    ]);
  };

  const sendMessage = async () => {
    const trimmed = chatInput.trim();
    if (!trimmed || isTyping) return;

    setApiError("");
    const userMessage: Message = {
      id: Date.now(),
      text: trimmed,
      isUser: true,
      timestamp: "just now",
    };

    setMessages((prev) => [...prev, userMessage]);
    setChatInput("");
    setIsTyping(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-HomeOps-User-Key": userKeyRef.current,
        },
        body: JSON.stringify({ message: trimmed }),
      });

      if (!response.ok) throw new Error("Chat request failed");

      const data: ChatApiResponse = await response.json();
      appendAssistantMessage(data.answer || "I could not generate a response right now.");
    } catch {
      appendAssistantMessage("I am currently offline. I can still help with general guidance based on your local context.");
      setApiError("Chat backend is unavailable. Showing local fallback responses.");
    } finally {
      setIsTyping(false);
    }
  };

  const handleChatKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      void sendMessage();
    }
  };

  const dismissAlert = (alertId: number) => {
    setAlerts((prev) => prev.map((a) => (a.id === alertId ? { ...a, status: "dismissed" } : a)));
  };

  const takeActionOnAlert = (alert: AlertItem) => {
    setAlerts((prev) => prev.map((a) => (a.id === alert.id ? { ...a, status: "actioned" } : a)));
    setActiveTab("chat");
    setChatInput(`Help me resolve this alert: ${alert.title}. Details: ${alert.desc}`);
  };

  const openProactiveGuide = (guideType: "hvac-filter" | "washer-check") => {
    setActiveTab("chat");
    if (guideType === "hvac-filter") {
      setChatInput("Show me a 7-minute HVAC filter replacement guide with safety checks.");
      return;
    }
    setChatInput("Run a preventive washer checklist with what to inspect and warning signs.");
  };

  const openItemDetail = (item: InventoryItem) => {
    setDashboardActionMessage(`${item.name} selected. Health ${item.health}/100. Next maintenance: ${item.nextMaintenance}.`);
    setActiveTab("inventory");
  };

  const openAddItemModal = () => {
    const name = window.prompt("Enter appliance name:", "New Appliance")?.trim() || "";
    if (!name) return;

    const model = window.prompt("Enter model number:", "MODEL-001")?.trim() || "MODEL-001";

    const nextItem: InventoryItem = {
      id: Date.now(),
      name,
      category: "Appliances",
      brand: "",
      model,
      serialNumber: "",
      purchaseDate: "Today",
      lastServiced: "Not recorded",
      nextMaintenance: "30 days",
      notes: "",
      status: "good",
      health: 85,
    };

    setInventory((prev) => [nextItem, ...prev]);

    void fetch("/api/inventory", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-HomeOps-User-Key": userKeyRef.current,
      },
      body: JSON.stringify({
        name,
        category: "Appliances",
        brand: "",
        model_number: model,
        serial_number: "",
        purchase_date: null,
        last_serviced: null,
        next_maintenance: null,
        notes: "",
      }),
    }).catch(() => undefined);
  };

  const addDetectedItemToInventory = (itemName: string) => {
    const nextItem: InventoryItem = {
      id: Date.now(),
      name: itemName,
      category: "Appliances",
      brand: "",
      model: "Unknown",
      purchaseDate: "Unknown",
      lastServiced: "Not recorded",
      nextMaintenance: "30 days",
      status: "good",
      health: 80,
    };
    setInventory((prev) => [nextItem, ...prev]);
  };

  const analyzeScanImage = async () => {
    if (!scanFile || isScanning) return;

    setApiError("");
    setScanDiagnosis(null);
    setScanSolved(null);
    setIsScanning(true);
    setScanMessage("Analyzing image and generating safe repair guidance...");

    const formData = new FormData();
    formData.append("file", scanFile);
    if (scanIssueText.trim()) formData.append("issue_text", scanIssueText.trim());
    if (scanErrorCodeHint.trim()) formData.append("error_code_hint", scanErrorCodeHint.trim());

    try {
      const response = await fetch("/api/diagnose/from-image", {
        method: "POST",
        headers: {
          "X-HomeOps-User-Key": userKeyRef.current,
        },
        body: formData,
      });

      if (!response.ok) throw new Error("Scan diagnose failed");
      const data: ScanDiagnosisApiResponse = await response.json();

      setScanDiagnosis(data);
      setScanResults([
        [data.extraction.brand, data.extraction.model_number].filter(Boolean).join(" ").trim() || "Unknown appliance",
      ]);
      setScanMessage("Scan complete. Review diagnosis and next steps below.");
    } catch {
      setScanMessage("Scan failed. Please retry or continue in chat for manual guidance.");
      setApiError("Scan backend is unavailable. Try again or use chat for manual troubleshooting.");
    } finally {
      setIsScanning(false);
    }
  };

  const openScanManualInChat = () => {
    setActiveTab("chat");
    const prompt = scanDiagnosis
      ? `Find manual and safe troubleshooting for ${scanDiagnosis.extraction.brand} ${scanDiagnosis.extraction.model_number}.`
      : "Find the right manual and basic troubleshooting for my appliance.";
    setChatInput(prompt);
  };

  const openScanDiagnosisInChat = () => {
    setActiveTab("chat");
    if (scanDiagnosis?.chat_prompt) {
      setChatInput(scanDiagnosis.chat_prompt);
      return;
    }
    setChatInput("Continue diagnosis from the latest scan and suggest the safest next action.");
  };

  const clearScanResult = () => {
    setScanDiagnosis(null);
    setScanSolved(null);
    setScanResults([]);
    setScanIssueText("");
    setScanErrorCodeHint("");
    setScanMessage("Upload an appliance sticker or receipt image to analyze it.");
  };

  const retryScan = () => {
    void analyzeScanImage();
  };

  return (
    <div className="h-screen bg-zinc-950 text-zinc-100 flex overflow-hidden">
      <Sidebar activeTab={activeTab} onSelectTab={setActiveTab} />

      <div className="flex-1 min-w-0 flex flex-col">
        <TopBar
          activeTab={activeTab}
          backendReady={backendReady}
          temperatureF={temperatureF}
          humidityPct={humidityPct}
        />

        <main className="flex-1 overflow-auto p-8">
          {activeTab === "dashboard" && (
            <DashboardPage
              inventory={inventory}
              totalHealth={totalHealth}
              maintenanceDueCount={maintenanceDueCount}
              maintenanceDueLabel={maintenanceDueLabel}
              estimatedSavings={estimatedSavings}
              pairedItemsCount={pairedItemsCount}
              dashboardActionMessage={dashboardActionMessage}
              onOpenInventory={() => setActiveTab("inventory")}
              onOpenItemDetail={openItemDetail}
              onOpenProactiveGuide={openProactiveGuide}
            />
          )}

          {activeTab === "inventory" && (
            <InventoryPage
              searchTerm={searchTerm}
              onChangeSearchTerm={setSearchTerm}
              onOpenAddItemModal={openAddItemModal}
              isInventoryLoading={isInventoryLoading}
              filteredInventory={filteredInventory}
              onOpenItemDetail={openItemDetail}
            />
          )}

          {activeTab === "chat" && (
            <ChatPage
              messages={messages}
              isTyping={isTyping}
              apiError={apiError}
              chatInput={chatInput}
              onChangeChatInput={setChatInput}
              onChatKeyDown={handleChatKeyDown}
              onSendMessage={() => {
                void sendMessage();
              }}
              chatBottomRef={chatBottomRef}
            />
          )}

          {activeTab === "scan" && (
            <ScanPage
              isScanning={isScanning}
              scanFile={scanFile}
              onSelectScanFile={setScanFile}
              scanIssueText={scanIssueText}
              onChangeScanIssueText={setScanIssueText}
              scanErrorCodeHint={scanErrorCodeHint}
              onChangeScanErrorCodeHint={setScanErrorCodeHint}
              scanMessage={scanMessage}
              onAnalyzeImage={() => {
                void analyzeScanImage();
              }}
              scanDiagnosis={scanDiagnosis}
              scanSolved={scanSolved}
              onSetScanSolvedState={setScanSolved}
              onOpenScanManualInChat={openScanManualInChat}
              onOpenScanDiagnosisInChat={openScanDiagnosisInChat}
              onClearScanResult={clearScanResult}
              onRetryScan={retryScan}
              scanResults={scanResults}
              onAddToInventory={addDetectedItemToInventory}
            />
          )}

          {activeTab === "alerts" && (
            <AlertsPage
              activeAlerts={activeAlerts}
              handledAlerts={handledAlerts}
              onDismissAlert={dismissAlert}
              onTakeActionOnAlert={takeActionOnAlert}
            />
          )}
        </main>
      </div>
    </div>
  );
}
