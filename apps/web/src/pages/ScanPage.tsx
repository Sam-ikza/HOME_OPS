import { Camera } from "lucide-react";

import type { ScanDiagnosisApiResponse } from "@/types/homeops";
import {
  buildExpertAdviceContent,
  getScanDifficulty,
  isDiagnosisComplicated,
  shouldRecommendTechnician,
  SUPPORT_CENTER_LABEL,
  SUPPORT_PHONE_DISPLAY,
  SUPPORT_PHONE_LINK,
} from "@/utils/homeops";

interface ScanPageProps {
  isScanning: boolean;
  scanFile: File | null;
  onSelectScanFile: (file: File | null) => void;
  scanIssueText: string;
  onChangeScanIssueText: (value: string) => void;
  scanErrorCodeHint: string;
  onChangeScanErrorCodeHint: (value: string) => void;
  scanMessage: string;
  onAnalyzeImage: () => void;
  scanDiagnosis: ScanDiagnosisApiResponse | null;
  scanSolved: boolean | null;
  onSetScanSolvedState: (isSolved: boolean) => void;
  onOpenScanManualInChat: () => void;
  onOpenScanDiagnosisInChat: () => void;
  onClearScanResult: () => void;
  onRetryScan: () => void;
  scanResults: string[];
  onAddToInventory: (itemName: string) => void;
}

export function ScanPage({
  isScanning,
  scanFile,
  onSelectScanFile,
  scanIssueText,
  onChangeScanIssueText,
  scanErrorCodeHint,
  onChangeScanErrorCodeHint,
  scanMessage,
  onAnalyzeImage,
  scanDiagnosis,
  scanSolved,
  onSetScanSolvedState,
  onOpenScanManualInChat,
  onOpenScanDiagnosisInChat,
  onClearScanResult,
  onRetryScan,
  scanResults,
  onAddToInventory,
}: ScanPageProps) {
  return (
    <div className="max-w-5xl mx-auto">
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-2 bg-zinc-900 rounded-3xl px-5 py-2 text-sm">
          <Camera className="text-teal-400" /> LIVE CAMERA MODE
        </div>
        <h2 className="text-4xl font-semibold mt-3">Scan your room</h2>
        <p className="text-zinc-400 max-w-sm mx-auto mt-3">Upload any appliance image and HOME_SENSE will diagnose visible issues, error codes, and safety risks.</p>
      </div>

      <div className="bg-zinc-900 rounded-3xl overflow-hidden border border-zinc-700 relative h-[460px] flex items-center justify-center">
        {isScanning ? (
          <div className="flex flex-col items-center">
            <div className="w-16 h-16 border-4 border-teal-400 border-t-transparent animate-spin rounded-full mb-6"></div>
            <div className="text-xl">Scanning room...</div>
            <div className="text-xs text-teal-400 mt-1">Using on-device vision model</div>
          </div>
        ) : (
          <div className="w-full h-full bg-[radial-gradient(#27272a_1px,transparent_1px)] bg-size-[20px_20px] flex items-center justify-center relative">
            <div className="text-center">
              <div className="mx-auto mb-8 w-40 h-40 border-2 border-dashed border-zinc-600 rounded-3xl flex items-center justify-center">
                <Camera className="w-16 h-16 text-zinc-600" />
              </div>
              <input
                type="file"
                accept="image/*"
                aria-label="Upload appliance image"
                title="Upload appliance image"
                onChange={(event) => onSelectScanFile(event.target.files?.[0] ?? null)}
                className="mx-auto mb-4 block text-xs text-zinc-400 file:mr-4 file:rounded-2xl file:border-0 file:bg-zinc-800 file:px-4 file:py-3 file:text-zinc-200"
              />
              <div className="mx-auto max-w-md mb-4 space-y-2 text-left">
                <input
                  type="text"
                  value={scanIssueText}
                  onChange={(event) => onChangeScanIssueText(event.target.value)}
                  placeholder="Optional: describe what is wrong (e.g., not turning on, noisy)"
                  title="Describe issue"
                  aria-label="Describe issue"
                  className="w-full bg-zinc-800 border border-zinc-700 rounded-2xl px-4 py-2 text-xs text-zinc-200 placeholder:text-zinc-500"
                />
                <input
                  type="text"
                  value={scanErrorCodeHint}
                  onChange={(event) => onChangeScanErrorCodeHint(event.target.value)}
                  placeholder="Optional: typed error code (e.g., E03)"
                  title="Error code"
                  aria-label="Error code"
                  className="w-full bg-zinc-800 border border-zinc-700 rounded-2xl px-4 py-2 text-xs text-zinc-200 placeholder:text-zinc-500"
                />
              </div>
              <button
                disabled={!scanFile || isScanning}
                onClick={onAnalyzeImage}
                className="bg-white hover:bg-amber-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-black px-10 py-4 rounded-3xl font-medium flex items-center gap-3 mx-auto shadow-xl shadow-black/60"
              >
                <Camera className="w-5 h-5" />
                ANALYZE IMAGE
              </button>
              <div className="text-xs text-zinc-500 mt-6">{scanMessage}</div>
            </div>
          </div>
        )}
      </div>

      {scanDiagnosis && (
        <div className="mt-8 bg-zinc-900 border border-zinc-700 rounded-3xl p-6">
          {(() => {
            const difficulty = getScanDifficulty(scanDiagnosis.diagnosis);
            const expertAdvice = buildExpertAdviceContent(scanDiagnosis.diagnosis);
            const diagnosisComplicated = isDiagnosisComplicated(scanDiagnosis.diagnosis);
            const technicianRecommended = shouldRecommendTechnician(scanDiagnosis.diagnosis);
            return (
              <>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="text-xs text-zinc-400 uppercase tracking-wide">Scan Diagnosis</div>
                    <div className="text-xl text-white font-semibold mt-1">
                      {scanDiagnosis.extraction.brand || "Unknown"} {scanDiagnosis.extraction.model_number || ""}
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    {scanDiagnosis.extraction.source === "demo_manifest" && (
                      <div className="px-4 py-2 rounded-2xl text-xs font-semibold border border-sky-800 bg-sky-950 text-sky-300">
                        DEMO MATCH
                      </div>
                    )}
                    <div className={`px-4 py-2 rounded-2xl text-xs font-semibold ${
                      scanDiagnosis.diagnosis.danger_level === "HIGH"
                        ? "bg-red-950 text-red-300 border border-red-800"
                        : scanDiagnosis.diagnosis.danger_level === "MEDIUM"
                          ? "bg-amber-950 text-amber-300 border border-amber-800"
                          : "bg-emerald-950 text-emerald-300 border border-emerald-800"
                    }`}>
                      {scanDiagnosis.diagnosis.danger_level} RISK
                    </div>
                  </div>
                </div>

                <div className="grid sm:grid-cols-3 gap-3 mt-4">
                  <div className="bg-zinc-950 border border-zinc-800 rounded-2xl p-3">
                    <div className="text-[11px] text-zinc-500 uppercase">Risk Level</div>
                    <div className="text-sm text-zinc-100 mt-1">{scanDiagnosis.diagnosis.danger_level}</div>
                  </div>
                  <div className="bg-zinc-950 border border-zinc-800 rounded-2xl p-3">
                    <div className="text-[11px] text-zinc-500 uppercase">Difficulty</div>
                    <div className="text-sm text-zinc-100 mt-1">{difficulty}</div>
                  </div>
                  <div className="bg-zinc-950 border border-zinc-800 rounded-2xl p-3">
                    <div className="text-[11px] text-zinc-500 uppercase">Estimated Fix Time</div>
                    <div className="text-sm text-zinc-100 mt-1">{scanDiagnosis.diagnosis.physical_brief.estimated_time_minutes} mins</div>
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-5 mt-5 text-sm">
                  <div className="bg-zinc-950 border border-zinc-800 rounded-2xl p-4">
                    <div className="text-zinc-400 text-xs">Likely Visible Issue</div>
                    <div className="text-zinc-100 mt-1">{scanDiagnosis.extraction.likely_issue}</div>
                    {scanDiagnosis.extraction.error_code && (
                      <div className="mt-3 text-xs text-teal-300">Error code: {scanDiagnosis.extraction.error_code}</div>
                    )}
                    {scanDiagnosis.extraction.display_text && (
                      <div className="mt-2 text-xs text-zinc-400">Display text: {scanDiagnosis.extraction.display_text}</div>
                    )}
                  </div>
                  <div className="bg-zinc-950 border border-zinc-800 rounded-2xl p-4">
                    <div className="text-zinc-400 text-xs">First Safe Action</div>
                    <div className="text-zinc-100 mt-1">
                      {scanDiagnosis.diagnosis.diy_steps.length > 0
                        ? scanDiagnosis.diagnosis.diy_steps[0]
                        : scanDiagnosis.diagnosis.escalation_message}
                    </div>
                    <div className="mt-3 text-xs text-zinc-500">
                      Confidence: {Math.round((scanDiagnosis.extraction.confidence || 0) * 100)}%
                    </div>
                  </div>
                </div>

                <div className="mt-5 bg-zinc-950 border border-zinc-800 rounded-2xl p-4">
                  <div className="text-zinc-400 text-xs">Step-by-step Fix Instructions</div>
                  {scanDiagnosis.diagnosis.diy_steps.length > 0 ? (
                    <ol className="mt-2 space-y-2 text-sm text-zinc-100 list-decimal pl-5">
                      {scanDiagnosis.diagnosis.diy_steps.map((step, idx) => (
                        <li key={`${idx}-${step.slice(0, 24)}`}>{step}</li>
                      ))}
                    </ol>
                  ) : (
                    <div className="mt-2 text-sm text-amber-300">{scanDiagnosis.diagnosis.escalation_message}</div>
                  )}
                </div>

                {scanSolved !== true && technicianRecommended && (
                  <div className="mt-4 rounded-2xl border border-red-700 bg-red-950/40 p-4">
                    <div className="text-sm font-semibold text-red-200">Technician Recommended</div>
                    <div className="text-xs text-red-100/90 mt-1">
                      {scanDiagnosis.diagnosis.danger_level === "HIGH"
                        ? "Major safety concern detected. Stop further repair attempts and contact support now."
                        : diagnosisComplicated
                          ? "The LLM diagnosis indicates this is a complicated repair. Technician help is recommended."
                          : "Professional support is recommended for this issue."}
                    </div>
                    <div className="mt-3 text-sm text-zinc-200">Technician Number: {SUPPORT_PHONE_DISPLAY}</div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <a
                        href={`tel:${SUPPORT_PHONE_LINK}`}
                        className="px-4 py-2 rounded-2xl text-xs border border-red-700 bg-red-950 text-red-300 hover:bg-red-900"
                      >
                        CALL TECHNICIAN
                      </a>
                      <button
                        onClick={onOpenScanManualInChat}
                        className="px-4 py-2 rounded-2xl text-xs border border-zinc-700 text-zinc-200 hover:bg-zinc-800"
                      >
                        VIEW MANUAL FIRST
                      </button>
                    </div>
                  </div>
                )}

                {scanDiagnosis.extraction.visible_signals.length > 0 && (
                  <div className="mt-5">
                    <div className="text-zinc-400 text-xs mb-2">Visible Signals</div>
                    <div className="flex flex-wrap gap-2">
                      {scanDiagnosis.extraction.visible_signals.map((signal) => (
                        <span key={signal} className="px-3 py-1 rounded-xl bg-zinc-800 text-zinc-300 text-xs">{signal}</span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="mt-6 bg-zinc-950 border border-zinc-800 rounded-2xl p-4">
                  <div className="text-sm font-medium text-white">Did this solve your issue?</div>
                  <div className="mt-3 flex flex-wrap gap-3">
                    <button
                      onClick={() => onSetScanSolvedState(true)}
                      className="px-4 py-2 rounded-2xl text-xs border border-emerald-700 bg-emerald-950 text-emerald-300 hover:bg-emerald-900"
                    >
                      YES, SOLVED
                    </button>
                    <button
                      onClick={() => onSetScanSolvedState(false)}
                      className="px-4 py-2 rounded-2xl text-xs border border-red-700 bg-red-950 text-red-300 hover:bg-red-900"
                    >
                      NO, NEED HELP
                    </button>
                  </div>
                </div>

                {scanSolved === true && (
                  <div className="mt-4 rounded-2xl border border-emerald-700 bg-emerald-950/60 px-4 py-3 text-sm text-emerald-200">
                    Resolved. Keep monitoring and run a preventive check in 24 hours.
                  </div>
                )}

                {scanSolved === false && (
                  <div className="mt-4 rounded-2xl border border-amber-700 bg-amber-950/40 p-4">
                    <div className="text-sm font-semibold text-amber-200">{expertAdvice.title}</div>
                    <div className="text-xs text-amber-100/90 mt-1">{expertAdvice.message}</div>

                    <div className="mt-3 text-xs text-zinc-300">Reasons:</div>
                    <ul className="mt-1 list-disc pl-5 text-sm text-zinc-200 space-y-1">
                      {expertAdvice.reasons.map((reason) => (
                        <li key={reason}>{reason}</li>
                      ))}
                    </ul>

                    <div className="mt-3 text-sm text-amber-100">Recommended Action: {expertAdvice.recommendedAction}</div>
                    <div className="mt-2 text-sm text-zinc-200">Helpline: {SUPPORT_PHONE_DISPLAY}</div>
                    <div className="text-xs text-zinc-400">Nearest: {SUPPORT_CENTER_LABEL}</div>

                    <div className="mt-4 flex flex-wrap gap-2">
                      <button
                        onClick={onRetryScan}
                        disabled={!scanFile || isScanning}
                        className="px-4 py-2 rounded-2xl text-xs border border-zinc-700 text-zinc-200 hover:bg-zinc-800 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        TRY AGAIN
                      </button>
                      <a
                        href={`tel:${SUPPORT_PHONE_LINK}`}
                        className="px-4 py-2 rounded-2xl text-xs border border-amber-700 bg-amber-950 text-amber-300 hover:bg-amber-900"
                      >
                        CONTACT EXPERT
                      </a>
                      <button
                        onClick={onOpenScanManualInChat}
                        className="px-4 py-2 rounded-2xl text-xs border border-sky-700 bg-sky-950 text-sky-300 hover:bg-sky-900"
                      >
                        VIEW MANUAL
                      </button>
                    </div>
                  </div>
                )}

                <div className="mt-6 flex flex-wrap gap-3">
                  <button
                    onClick={onOpenScanDiagnosisInChat}
                    className="bg-white text-black hover:bg-amber-100 px-5 py-2.5 rounded-2xl text-xs font-medium"
                  >
                    CONTINUE IN CHAT
                  </button>
                  <button
                    onClick={onClearScanResult}
                    className="border border-zinc-700 hover:bg-zinc-800 px-5 py-2.5 rounded-2xl text-xs"
                  >
                    CLEAR RESULT
                  </button>
                </div>
              </>
            );
          })()}
        </div>
      )}

      {scanResults.length > 0 && (
        <div className="mt-8">
          <div className="font-medium mb-4 px-1">Detected Items</div>
          <div className="grid grid-cols-3 gap-4">
            {scanResults.map((item, idx) => (
              <div key={idx} className="bg-zinc-900 border border-zinc-700 rounded-3xl p-6 flex justify-between items-center">
                <div>{item}</div>
                <button
                  onClick={() => onAddToInventory(item)}
                  className="text-xs bg-teal-500 hover:bg-teal-400 text-black px-5 py-2.5 rounded-2xl"
                >
                  ADD
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
