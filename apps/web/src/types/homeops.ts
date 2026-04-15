export type ActiveTab = "dashboard" | "inventory" | "chat" | "scan" | "alerts";

export interface InventoryItem {
  id: number;
  dbId?: number;
  name: string;
  category: string;
  brand?: string;
  model: string;
  serialNumber?: string;
  purchaseDate: string;
  lastServiced: string;
  nextMaintenance: string;
  notes?: string;
  status: "good" | "attention" | "critical";
  health: number;
}

export interface ServiceHistoryEntry {
  id: number;
  event_type: string;
  event_date: string;
  description?: string;
  technician?: string;
  cost?: string;
}

export interface InventoryApiResponse {
  id: number;
  name: string;
  category: string;
  brand?: string;
  model_number: string;
  serial_number?: string;
  purchase_date?: string;
  last_serviced?: string;
  next_maintenance?: string;
  notes?: string;
  status: string;
  health: number;
  history: ServiceHistoryEntry[];
}

export interface LogServiceForm {
  event_type: string;
  event_date: string;
  description: string;
  technician: string;
  cost: string;
}

export interface Message {
  id: number;
  text: string;
  isUser: boolean;
  timestamp: string;
}

export interface ChatApiResponse {
  answer: string;
  video_url?: string;
  source: string;
}

export interface ScanApiResponse {
  brand?: string;
  model?: string;
  confidence?: number;
  source?: string;
}

export interface ScanExtractionResponse {
  appliance_type?: string | null;
  brand: string;
  model_number: string;
  error_code?: string | null;
  display_text?: string | null;
  likely_issue: string;
  visible_signals: string[];
  risk_flags: string[];
  summary?: string | null;
  confidence: number;
  needs_confirmation: boolean;
  source: string;
}

export interface DiagnosisPayload {
  danger_level: "LOW" | "MEDIUM" | "HIGH";
  call_pro: boolean;
  warranty_active: boolean;
  warranty_block_reason?: string | null;
  manufacturer_support?: string | null;
  fragility_warning: string;
  physical_brief: {
    estimated_time_minutes: number;
    heavy_lifting_required: boolean;
    estimated_weight_lbs: number;
    spill_risk: "LOW" | "MEDIUM" | "HIGH";
  };
  software_lock_warning?: string | null;
  diagnosis_summary: string;
  diy_steps: string[];
  required_parts: string[];
  escalation_message: string;
}

export interface ScanDiagnosisApiResponse {
  extraction: ScanExtractionResponse;
  diagnosis: DiagnosisPayload;
  chat_prompt: string;
  event_id?: number;
}

export type ScanDifficulty = "BASIC" | "INTERMEDIATE" | "ADVANCED";

export interface ExpertAdviceContent {
  title: string;
  message: string;
  reasons: string[];
  recommendedAction: string;
}

export interface HealthResponse {
  ok: boolean;
  checks?: {
    database_ok?: boolean;
  };
}

export type AlertSeverity = "high" | "medium" | "low";
export type AlertStatus = "active" | "dismissed" | "actioned";

export interface AlertItem {
  id: number;
  title: string;
  time: string;
  severity: AlertSeverity;
  desc: string;
  status: AlertStatus;
}

export interface AddItemForm {
  productName: string;
  category: string;
  brand: string;
  modelNumber: string;
  serialNumber: string;
  purchaseDate: string;
  lastServiced: string;
  nextMaintenance: string;
  notes: string;
}

export type AlertSeed = Omit<AlertItem, "id" | "status">;
