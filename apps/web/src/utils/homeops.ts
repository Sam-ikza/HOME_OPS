import type {
  AddItemForm,
  AlertSeed,
  DiagnosisPayload,
  ExpertAdviceContent,
  ScanDifficulty,
} from "@/types/homeops";

export const SUPPORT_PHONE_DISPLAY = "8757219362";
export const SUPPORT_PHONE_LINK = "+918757219362";
export const SUPPORT_CENTER_LABEL = "Chandigarh Service Center";

export const DEFAULT_ALERT_SEED: AlertSeed[] = [
  {
    title: "HVAC filter needs replacement",
    time: "2 days ago",
    severity: "high",
    desc: "Last changed 87 days ago. Average lifespan is 90 days.",
  },
  {
    title: "Refrigerator running 12% hotter than usual",
    time: "14 hours ago",
    severity: "medium",
    desc: "Coils may need cleaning. Energy consumption is up 8%.",
  },
  {
    title: "New recall on your smoke detector model",
    time: "Yesterday",
    severity: "high",
    desc: "Manufacturer issued a voluntary recall. Review recall steps now.",
  },
  {
    title: "Water softener salt low",
    time: "3 days ago",
    severity: "low",
    desc: "Refill is recommended within the next week.",
  },
];

export const DEFAULT_ADD_ITEM_FORM: AddItemForm = {
  productName: "",
  category: "Appliances",
  brand: "",
  modelNumber: "",
  serialNumber: "",
  purchaseDate: "",
  lastServiced: "",
  nextMaintenance: "30 days",
  notes: "",
};

const ISO_DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/;

export const todayIsoDate = () => new Date().toISOString().slice(0, 10);

export const getOrCreateUserKey = () => {
  const storageKey = "homeops-user-key";

  try {
    const existing = window.localStorage.getItem(storageKey);
    if (existing && existing.length >= 8) return existing;

    const generated = `usr_${Math.random().toString(36).slice(2, 12)}${Date.now().toString(36)}`;
    window.localStorage.setItem(storageKey, generated);
    return generated;
  } catch {
    return `usr_fallback_${Date.now().toString(36)}`;
  }
};

export const formatStoredDate = (value: string | null | undefined, fallback: string) => {
  const normalized = value?.trim();
  if (!normalized) return fallback;

  if (ISO_DATE_PATTERN.test(normalized)) {
    const parsed = new Date(`${normalized}T00:00:00`);
    if (!Number.isNaN(parsed.getTime())) {
      return parsed.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
    }
  }

  return normalized;
};

export const parseDaysUntilMaintenance = (value: string | null | undefined): number | null => {
  const normalized = (value || "").trim().toLowerCase();
  if (!normalized) return null;

  if (ISO_DATE_PATTERN.test(normalized)) {
    const dueDate = new Date(`${normalized}T00:00:00`);
    if (Number.isNaN(dueDate.getTime())) return null;
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    return Math.ceil((dueDate.getTime() - now.getTime()) / 86_400_000);
  }

  if (normalized === "today") return 0;
  if (normalized.includes("overdue")) return -1;

  const dayMatch = normalized.match(/(\d+)\s*day/);
  if (dayMatch) return Number(dayMatch[1]);

  const weekMatch = normalized.match(/(\d+)\s*week/);
  if (weekMatch) return Number(weekMatch[1]) * 7;

  const monthMatch = normalized.match(/(\d+)\s*month/);
  if (monthMatch) return Number(monthMatch[1]) * 30;

  return null;
};

export const formatMaintenanceCountdown = (daysUntil: number | null, fallback: string) => {
  if (daysUntil === null) return fallback;
  if (daysUntil < 0) return `Overdue by ${Math.abs(daysUntil)} day${Math.abs(daysUntil) === 1 ? "" : "s"}`;
  if (daysUntil === 0) return "Due today";
  if (daysUntil === 1) return "Due in 1 day";
  return `Due in ${daysUntil} days`;
};

export const toFahrenheit = (tempCelsius: number) => Math.round((tempCelsius * 9) / 5 + 32);

export const getStatusColor = (status: string) => {
  if (status === "good") return "bg-emerald-100 text-emerald-700";
  if (status === "attention") return "bg-amber-100 text-amber-700";
  return "bg-red-100 text-red-700";
};

export const getHealthColor = (health: number) => {
  if (health > 85) return "text-emerald-500";
  if (health > 65) return "text-amber-500";
  return "text-red-500";
};

export const getScanDifficulty = (diagnosis: DiagnosisPayload): ScanDifficulty => {
  if (diagnosis.danger_level === "HIGH" || diagnosis.call_pro) return "ADVANCED";
  if (diagnosis.danger_level === "MEDIUM" || diagnosis.physical_brief.estimated_time_minutes > 30) {
    return "INTERMEDIATE";
  }
  return "BASIC";
};

export const isDiagnosisComplicated = (diagnosis: DiagnosisPayload): boolean => {
  const longProcedure = diagnosis.diy_steps.length >= 5;
  const requiresManyParts = diagnosis.required_parts.length >= 2;
  const timeIntensive = diagnosis.physical_brief.estimated_time_minutes >= 45;
  const heavyWork = diagnosis.physical_brief.heavy_lifting_required;
  const escalationSuggestsPro = /(professional|technician|service center|certified)/i.test(
    diagnosis.escalation_message || "",
  );

  return longProcedure || requiresManyParts || timeIntensive || heavyWork || escalationSuggestsPro;
};

export const shouldRecommendTechnician = (diagnosis: DiagnosisPayload): boolean => {
  if (diagnosis.danger_level === "HIGH" || diagnosis.call_pro) return true;
  return isDiagnosisComplicated(diagnosis);
};

export const buildExpertAdviceContent = (diagnosis: DiagnosisPayload): ExpertAdviceContent => {
  if (diagnosis.danger_level === "HIGH") {
    return {
      title: "High Risk Issue Detected",
      message: "Do not attempt further repair. This issue may involve safety hazards or internal damage.",
      reasons: [
        "Possible electrical hazard",
        "Internal component damage may be present",
        "Advanced tools and technician checks are likely required",
      ],
      recommendedAction: "Turn the appliance off and contact a certified technician immediately.",
    };
  }

  if (diagnosis.danger_level === "MEDIUM") {
    return {
      title: "Issue Still Not Fixed?",
      message: "This problem may require professional assistance if the guided steps did not work.",
      reasons: [
        "The issue could be hardware-related",
        "Internal wiring or sensors may need inspection",
        "Proper diagnostic tools may be required",
      ],
      recommendedAction: "Contact a technician for in-person diagnosis and safe repair.",
    };
  }

  return {
    title: "Need Expert Help?",
    message: "If retrying the basic steps did not solve it, expert support is recommended.",
    reasons: [
      "Hidden internal issues may not be visible externally",
      "Manual reset and checks may need professional validation",
      "A technician can prevent repeat failures",
    ],
    recommendedAction: "Try once more, then contact expert support if the issue persists.",
  };
};
