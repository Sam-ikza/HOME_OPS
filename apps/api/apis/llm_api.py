"""LLM orchestration for HomeSense diagnosis with strict safety JSON output."""

from __future__ import annotations

import json
import os
import re
from urllib.parse import quote_plus

from groq import Groq
from dotenv import load_dotenv

from config import settings

load_dotenv()

_client = Groq(api_key=os.getenv("GROQ_API_KEY")) if os.getenv("GROQ_API_KEY") else None

_SYSTEM_PROMPT = """
You are HomeSense AI, an expert, safety-first appliance technician.
You must diagnose the issue using ONLY the provided manual text for this specific model.

CRITICAL RULES:
1. DANGER THRESHOLD: If the repair involves high voltage, gas, or internal wiring, set "danger_level" to "HIGH", provide zero DIY steps, and instruct the user to call a professional.
2. FRAGILITY: If a step involves plastic clips, glass, or delicate sensors, you MUST populate the "fragility_warning" field.
3. PHYSICAL BRIEF: You must estimate the time needed, weight/lifting requirements, and mess potential.
4. WARRANTY: If the system flags "warranty_active" as true, do not provide repair steps. Instruct the user to contact the manufacturer.
5. SAFETY PRECHECK: Before any DIY action, require safe shutdown (power/gas/water isolation as applicable) in your reasoning.
6. NEVER BYPASS SAFETY: Never suggest bypassing grounding, fuses, MCB/RCB protection, door interlocks, pressure relief valves, or thermal cutoffs.
7. FIRE/SHOCK/GAS: If smoke, sparks, burning smell, shock, or gas/refrigerant leak indicators are present, escalate to HIGH danger and stop DIY guidance.
8. IMAGE CONTEXT: If image_context is provided, use it as strong evidence for visible causes (e.g., unplugged plug, switch off, visible leak, error code on display).

Output strictly in JSON format.
""".strip()

_CHAT_SYSTEM_PROMPT = """
You are HomeOps, a strict home-appliance maintenance and safety assistant.

Scope Rules:
- Answer ONLY home appliance diagnostics, maintenance, and safety.
- If the request is outside scope, reply exactly with the refusal text provided by the application.

Safety Rules:
- If high-voltage, internal wiring, gas, refrigerant leak, sparks, smoke, or burning smell is implied, do not provide risky DIY instructions.
- In risky scenarios, advise immediate shutdown/isolation and professional service.
- Never suggest bypassing fuses, grounding, MCB/RCB protection, interlocks, or other safety mechanisms.

Response Format Rules:
- Use exactly these section headers:
[Summary]
[Safety]
[Step-by-Step]
[When to Call a Professional]
- Use clear sentences with proper punctuation and spacing.
- Use numbered steps under [Step-by-Step].
- Keep the answer concise and practical.
- If the user asks for technician/support contact, or if professional escalation is appropriate, include this exact line in the final answer: Technician Contact: 8757219362
- The technician contact is inside HomeOps domain and may be shared for appliance safety, escalation, and service requests.
""".strip()

_KNOWN_GOOD_GROQ_MODELS = [
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
]

_OFF_TOPIC_REFUSAL = (
    "HomeOps can only help with home appliance maintenance, diagnostics, and safety. "
    "Ask about issues like fridge overheating, washer leaks, dryer noise, oven not heating, TV no signal, or AC airflow."
)

_TECHNICIAN_PHONE = "8757219362"

_HIGH_RISK_CHAT_TERMS = {
    "gas",
    "gas leak",
    "lpg",
    "cng",
    "refrigerant",
    "coolant leak",
    "freon",
    "r32",
    "r410a",
    "r22",
    "high voltage",
    "mains voltage",
    "live wire",
    "electric shock",
    "electrocution",
    "shock",
    "240v",
    "415v",
    "wiring",
    "internal wiring",
    "capacitor",
    "inverter board",
    "control board",
    "pcb",
    "compressor",
    "sealed system",
    "breaker panel",
    "mcb",
    "rcb",
    "rcbo",
    "earthing",
    "ground fault",
    "short circuit",
    "electrical arc",
    "arc flash",
    "spark",
    "sparks",
    "smoke",
    "fire",
    "flame",
    "burning smell",
    "burnt smell",
    "burning plastic",
    "water near wiring",
    "water in control panel",
    "hissing leak",
}

_SEVERE_DANGER_CHAT_TERMS = {
    "gas leak",
    "smell gas",
    "burning smell",
    "burnt smell",
    "smoke",
    "fire",
    "sparks",
    "electric shock",
    "electrocution",
    "arc flash",
}

_SUPPORT_CONTACT_CHAT_TERMS = {
    "technician number",
    "technician contact",
    "expert number",
    "support number",
    "service center number",
    "contact expert",
    "call technician",
    "helpline",
    "phone number",
}

_APPLIANCE_DEVICE_TERMS = {
    "appliance",
    "home appliance",
    "fridge",
    "refrigerator",
    "freezer",
    "wine cooler",
    "washer",
    "washing machine",
    "washer dryer",
    "dryer",
    "tumble dryer",
    "dishwasher",
    "oven",
    "electric oven",
    "gas oven",
    "stove",
    "cooktop",
    "induction cooktop",
    "range",
    "range hood",
    "chimney hood",
    "microwave",
    "microwave oven",
    "toaster",
    "toaster oven",
    "air fryer",
    "blender",
    "mixer",
    "coffee maker",
    "espresso machine",
    "electric kettle",
    "rice cooker",
    "pressure cooker",
    "water purifier",
    "water dispenser",
    "ac",
    "air conditioner",
    "aircon",
    "split ac",
    "window ac",
    "heat pump",
    "hvac",
    "boiler",
    "water heater",
    "geyser",
    "furnace",
    "dehumidifier",
    "humidifier",
    "air purifier",
    "vacuum",
    "robot vacuum",
    "ceiling fan",
    "exhaust fan",
    "inverter",
    "ups",
    "generator",
    "home theater",
    "soundbar",
    "filter",
    "compressor",
    "thermostat",
    "tv",
    "television",
    "smart tv",
    "oled tv",
    "qled tv",
    "led tv",
    "lcd tv",
    "android tv",
    "fire tv",
    "roku tv",
    "google tv",
    "apple tv",
    "set top box",
    "cable box",
    "dth box",
    "satellite receiver",
    # ── Additional Indian & universal appliance categories ─────────────────
    "air cooler",
    "desert cooler",
    "evaporative cooler",
    "mixer grinder",
    "juicer mixer grinder",
    "hand blender",
    "food processor",
    "juicer",
    "otg",
    "oven toaster griller",
    "electric iron",
    "steam iron",
    "dry iron",
    "stabilizer",
    "voltage stabilizer",
    "immersion rod",
    "immersion heater",
    "room heater",
    "oil heater",
    "water softener",
    "sewing machine",
    "induction stove",
    "induction cooker",
    "electric cooker",
    "multi cooker",
    "slow cooker",
    "sandwich maker",
    "electric chimney",
    "hand mixer",
    "stand mixer",
    "deep freezer",
    "chest freezer",
    "upright freezer",
    "treadmill",
}

_APPLIANCE_BRAND_TERMS: set[str] = {
    # ── Global leaders ────────────────────────────────────────────────────────
    "lg", "samsung", "sony", "whirlpool", "bosch", "haier", "panasonic",
    "hitachi", "daikin", "siemens", "philips", "midea", "hisense", "tcl",
    "electrolux", "sharp", "toshiba", "frigidaire", "kenmore", "maytag",
    "amana", "miele", "beko", "ariston", "indesit", "zanussi",
    "fisher paykel", "sub-zero", "thermador", "dacor", "viking", "wolf",
    "smeg", "candy", "hoover", "hotpoint", "grundig", "aeg",
    # ── India-popular brands ───────────────────────────────────────────────
    "voltas", "godrej", "bajaj", "ifb", "v-guard", "vguard", "havells",
    "usha", "crompton", "orient", "prestige", "hawkins", "pigeon",
    "butterfly", "preethi", "sujata", "maharaja whiteline", "inalsa",
    "morphy richards", "kenstar", "sunflame",
    "kent", "eureka forbes", "aquaguard", "livpure", "pureit", "zero b",
    "ao smith", "racold", "venus geyser", "bajaj water heater",
    "blue star", "bluestar", "carrier", "o general", "lloyd",
    "onida", "videocon", "kelvinator", "voltas beko",
    "symphony", "bajaj cooler",
    # ── India OTT / Smart TV brands ────────────────────────────────────────
    "mi tv", "xiaomi tv", "redmi tv", "oneplus tv", "realme tv",
    "vu tv", "iffalcon", "motorola tv", "thomson tv",
    # ── Emerging / electrical component brands ─────────────────────────────
    "croma", "surya", "wipro lighting", "finolex", "polycab",
    "anchor electrical", "legrand", "schneider electric",
    # ── Samsung & LG premium sub-lines ────────────────────────────────────
    "samsung bespoke", "lg instaview", "lg signature",
}

_APPLIANCE_MODEL_TERMS: set[str] = {
    # ── Samsung TV series (2015-2025) ──────────────────────────────────────
    "crystal 4k", "neo qled", "the frame", "the serif", "the sero",
    "au8000", "au9000", "cu8000", "cu7000", "du8000", "du7000",
    "qn90", "qn85", "qn800", "qn900", "q80t", "q70t", "q60t",
    "ru8000", "ru7100", "mu6100",
    # ── LG TV series (2015-2025) ───────────────────────────────────────────
    "oled c2", "oled c3", "oled c4", "oled g3", "oled g4",
    "oled b2", "oled b3", "nanocell", "qned", "ur80", "ur90", "ur75",
    "uk6360", "sk8000", "sm8100",
    # ── Sony Bravia series (2015-2025) ────────────────────────────────────
    "bravia xr", "bravia x80l", "bravia x85l", "bravia x90l", "bravia x95l",
    "a80l", "a90l", "a95l", "x80k", "x90k", "x8000g", "x9500g",
    # ── India budget/OTT TVs ───────────────────────────────────────────────
    "vu iconium", "vu masterpiece", "vu glo", "vu premium",
    "tcl p735", "tcl c835", "tcl p615", "tcl s65a",
    # ── Samsung Washing Machine series ────────────────────────────────────
    "ecobubble", "quickdrive", "activ dualwash", "ai ecobubble",
    "wobble technology", "diamond drum", "ww80t", "ww60t", "ww70t",
    "wt70m", "wt65m",
    # ── LG Washing Machine series ──────────────────────────────────────────
    "turbowash", "twinwash", "ai direct drive", "fhm1065", "fhd0905",
    "t7288", "fht1408",
    # ── IFB Washing Machine models (India very popular) ───────────────────
    "ifb senator", "ifb senorita", "ifb executive plus", "ifb avante",
    "ifb maestro", "ifb elena", "ifb neo", "serene plus", "serene sx",
    "ifb tlrdw", "ifb aqua",
    # ── Whirlpool models ──────────────────────────────────────────────────
    "intellifresh", "protton", "acticool", "ace wash", "stainwash",
    "360 bloom wash", "fresh magic", "arctic steel",
    # ── Godrej models ─────────────────────────────────────────────────────
    "godrej eon", "godrej edge", "godrej nxg", "wteon",
    "godrej rb", "godrej rt", "godrej gfc",
    # ── Haier models ──────────────────────────────────────────────────────
    "haier triple door", "haier bottom mount", "haier side by side",
    "hrf-619", "hrf-719", "hrf-522",
    # ── AC models / series ────────────────────────────────────────────────
    "kashikoi", "toushi", "merai", "zunoh",              # Hitachi
    "adjustable inverter", "voltas adjustable", "voltas fastcooler",
    "blue star ic5", "blue star ic3",
    "carrier durafresh", "carrier ester",
    "daikin ftkf", "daikin jtkj", "daikin ftkg", "daikin rks",
    "panasonic cs/cu", "lg ls-q", "lg ps-q",
    # ── Refrigerator models ───────────────────────────────────────────────
    "french door", "side by side", "bottom freezer", "triple door fridge",
    "multi door", "convertible freezer",
    # ── Geysers / Water Heaters ───────────────────────────────────────────
    "pronto neo", "racold omnis", "racold buono", "racold eterno",
    "bajaj calenta", "bajaj juvel", "bajaj new shakti",
    "havells instanio", "havells monza", "havells adonia", "havells quatro",
    "v-guard victo", "v-guard milan", "v-guard sprinhot",
    "ao smith z9", "ao smith z8", "ao smith x4", "ao smith hse",
    "crompton solarium", "crompton gracee",
    # ── Water Purifiers ───────────────────────────────────────────────────
    "kent grand plus", "kent supreme", "kent prime plus", "kent pearl",
    "kent maxx", "kent ultra storage", "kent gold optima",
    "aquaguard enhance", "aquaguard marvel", "aquaguard 3000",
    "aquaguard reviva", "aquaguard nxt",
    "livpure glo", "livpure fresho2", "livpure touch screen",
    "pureit copper plus", "pureit advanced plus", "pureit eco mineral",
    # ── Mixer Grinders (India-popular) ────────────────────────────────────
    "preethi zodiac", "preethi blue leaf", "preethi eco chef",
    "bajaj gx8", "bajaj pluto", "maharaja sonic",
    "butterfly rapid", "sujata powermatic", "inalsa tulip",
    # ── Air Coolers (India-popular) ───────────────────────────────────────
    "symphony hicool", "symphony diet", "symphony jumbo",
    "symphony touch plus", "symphony sumo",
    "bajaj frio", "bajaj platini", "bajaj tc2007",
    "kenstar double cool", "kenstar slim trim",
    # ── Fans ──────────────────────────────────────────────────────────────
    "atomberg renesa", "atomberg gorilla", "orient aeroslim",
    "havells fusion", "usha striker", "bajaj regal",
    # ── Smart / Flagship features ─────────────────────────────────────────
    "bespoke refrigerator", "instaview door-in-door",
    "family hub fridge", "lg craft ice",
}

_APPLIANCE_ISSUE_TERMS = {
    "not working",
    "not turning on",
    "won't turn on",
    "won't start",
    "no power",
    "tripping",
    "trip",
    "fuse",
    "error",
    "error code",
    "fault",
    "issue",
    "problem",
    "repair",
    "service",
    "maintenance",
    "overheating",
    "leak",
    "leaking",
    "noise",
    "vibration",
    "smell",
    "burning smell",
    "not cooling",
    "not heating",
    "cooling issue",
    "heating issue",
    "frost buildup",
    "ice buildup",
    "water not draining",
    "drain",
    "clog",
    "blocked",
    "low airflow",
    "not spinning",
    "not drying",
    "flashing light",
    "blinking",
    "no signal",
    "signal",
    "hdmi",
    "antenna",
    "remote",
    "screen",
    "display",
    "black screen",
    "stuck on logo",
    "pairing",
    "wifi disconnect",
    "wifi not connecting",
    "not purifying",
    "water quality",
    "tds high",
    "overload",
    "short circuit",
    "compressor noise",
    "remote not working",
    "panel not responding",
    "door gasket",
    "filter clogged",
    "voltage fluctuation",
    "not charging",
    "auto shutdown",
    "power cut",
}

_APPLIANCE_CONTEXT_TERMS = {
    "home",
    "house",
    "kitchen",
    "laundry",
    "living room",
    "bedroom",
    "utility room",
    "appliance",
    "machine",
    "balcony",
    "hall",
    "drawing room",
    "dining room",
    "bathroom",
    "garage",
}


def _contains_keyword(text: str, keyword: str) -> bool:
    escaped = re.escape(keyword.lower())

    if " " in keyword or "-" in keyword:
        pattern = escaped.replace(r"\ ", r"(?:\s+|-)").replace(r"\-", r"(?:\s+|-)")
        return re.search(rf"(?<!\w){pattern}(?!\w)", text) is not None

    return re.search(rf"\b{escaped}\b", text) is not None


def _keyword_hits(text: str, keywords: set[str]) -> int:
    return sum(1 for keyword in keywords if _contains_keyword(text, keyword))


def _contains_high_risk_term(text: str) -> bool:
    return any(_contains_keyword(text, term) for term in _HIGH_RISK_CHAT_TERMS)


def _contains_severe_risk_term(text: str) -> bool:
    return any(_contains_keyword(text, term) for term in _SEVERE_DANGER_CHAT_TERMS)


def _contains_device_term(text: str) -> bool:
    return (
        any(_contains_keyword(text, term) for term in _APPLIANCE_DEVICE_TERMS)
        or any(_contains_keyword(text, term) for term in _APPLIANCE_BRAND_TERMS)
        or any(_contains_keyword(text, term) for term in _APPLIANCE_MODEL_TERMS)
    )


def _contains_appliance_issue_pattern(text: str) -> bool:
    issue_hits = _keyword_hits(text, _APPLIANCE_ISSUE_TERMS)
    context_hits = _keyword_hits(text, _APPLIANCE_CONTEXT_TERMS)
    return issue_hits >= 2 and context_hits >= 1


def _is_home_appliance_query(message: str) -> bool:
    lowered = message.lower()
    return _is_support_contact_request(lowered) or _contains_device_term(lowered) or _contains_appliance_issue_pattern(lowered)


def _is_high_risk_chat_query(message: str) -> bool:
    return _contains_high_risk_term(message.lower())


def _is_severe_chat_query(message: str) -> bool:
    return _contains_severe_risk_term(message.lower())


def _build_youtube_search_url(message: str) -> str:
    compact = re.sub(r"\s+", " ", message).strip()
    search_query = f"{compact} repair {settings.app_name} safe troubleshooting"
    return f"https://www.youtube.com/results?search_query={quote_plus(search_query)}"


def _normalize_spacing_and_punctuation(text: str) -> str:
    cleaned = text.replace("\r\n", "\n")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r" ?\n ?", "\n", cleaned)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"([,.;:!?])(\S)", r"\1 \2", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _ensure_terminal_punctuation(text: str) -> str:
    stripped = text.rstrip()
    if not stripped:
        return stripped
    if stripped.endswith((".", "!", "?", "]")):
        return stripped
    return stripped + "."


def _ensure_structured_chat_sections(text: str) -> str:
    normalized = _normalize_spacing_and_punctuation(text)
    required_headers = [
        "[Summary]",
        "[Safety]",
        "[Step-by-Step]",
        "[When to Call a Professional]",
    ]
    if all(header in normalized for header in required_headers):
        return _ensure_terminal_punctuation(normalized)

    return _ensure_terminal_punctuation(
        "\n\n".join(
            [
                "[Summary]\n" + (normalized or "Please share appliance brand, model, and exact symptom."),
                "[Safety]\nDisconnect power before inspection. Stop immediately if you notice sparks, smoke, burning smell, shock, or gas odor.",
                "[Step-by-Step]\n1. Confirm the exact symptom and any error code on display.\n2. Perform only external visual checks and basic reset steps.\n3. Share brand, model, and photo/error code for deeper guidance.",
                "[When to Call a Professional]\nCall a qualified technician immediately for electrical, gas, sealed-system, or burning-smell issues.",
            ]
        )
    )


def _support_contact_line() -> str:
    return f"Technician Contact: {_TECHNICIAN_PHONE}"


def _is_support_contact_request(message: str) -> bool:
    lowered = (message or "").lower()
    return any(term in lowered for term in _SUPPORT_CONTACT_CHAT_TERMS)


def _should_include_support_contact(message: str, answer: str) -> bool:
    if _is_support_contact_request(message):
        return True

    combined = f"{message}\n{answer}".lower()
    escalation_terms = (
        "call a professional",
        "call a technician",
        "professional service",
        "service center",
        "certified technician",
        "urgent professional inspection",
        "high-risk",
        "high risk",
        "danger",
    )
    return any(term in combined for term in escalation_terms)


def _append_support_contact(answer: str) -> str:
    normalized = answer.rstrip()
    if _TECHNICIAN_PHONE in normalized:
        return normalized

    contact_line = _support_contact_line()
    marker = "[When to Call a Professional]"
    if marker in normalized:
        head, tail = normalized.split(marker, 1)
        tail = tail.strip()
        tail = f"{tail}\n{contact_line}" if tail else contact_line
        return f"{head}{marker}\n{tail}".rstrip()

    return f"{normalized}\n\n{contact_line}".rstrip()


def _candidate_models(primary: str | None, configured: str) -> list[str]:
    candidates: list[str] = []
    for model_name in [primary, configured, *_KNOWN_GOOD_GROQ_MODELS]:
        if model_name and model_name not in candidates:
            candidates.append(model_name)
    return candidates


def _extract_json(text: str) -> dict:
    raw = text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw.replace("json", "", 1).strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _safe_fallback(citations: list[dict], warranty_active: bool) -> dict:
    if warranty_active:
        return {
            "danger_level": "LOW",
            "call_pro": True,
            "warranty_active": True,
            "warranty_block_reason": "Appliance appears under warranty coverage window.",
            "manufacturer_support": "Contact the manufacturer support line with model and serial details.",
            "fragility_warning": "Do not remove panels while under warranty unless manufacturer authorizes.",
            "physical_brief": {
                "estimated_time_minutes": 15,
                "heavy_lifting_required": False,
                "estimated_weight_lbs": 0,
                "spill_risk": "LOW",
            },
            "software_lock_warning": None,
            "diagnosis_summary": "Warranty-active case. Route through authorized service.",
            "diy_steps": [],
            "required_parts": [],
            "citations": citations,
            "escalation_message": "Contact manufacturer support with purchase proof and serial number.",
        }

    return {
        "danger_level": "MEDIUM",
        "call_pro": False,
        "warranty_active": False,
        "warranty_block_reason": None,
        "manufacturer_support": None,
        "fragility_warning": "Handle clips and sensors gently during inspection.",
        "physical_brief": {
            "estimated_time_minutes": 30,
            "heavy_lifting_required": False,
            "estimated_weight_lbs": 10,
            "spill_risk": "MEDIUM",
        },
        "software_lock_warning": None,
        "diagnosis_summary": "Initial checks suggest a maintenance-related issue.",
        "diy_steps": [
            "Power cycle the appliance and inspect the visible filter or drain path.",
            "Run a short diagnostic cycle and note any displayed code.",
            "If issue persists, share error code/photo for deeper troubleshooting.",
        ],
        "required_parts": [],
        "citations": citations,
        "escalation_message": "If symptoms worsen or electrical smell appears, stop and contact a professional.",
    }


def generate_diagnosis_json(
    issue_text: str,
    manual_chunks: list[dict],
    appliance_brand: str,
    appliance_model: str,
    warranty_active: bool,
    image_context: dict | None = None,
    model: str | None = None,
) -> dict:
    requested_model = model or settings.groq_diagnosis_model
    citations = [
        {
            "manual_id": chunk.get("metadata", {}).get("manual_id"),
            "chunk_id": chunk.get("metadata", {}).get("chunk_id"),
            "source": chunk.get("metadata", {}).get("source", "manual"),
            "snippet": chunk.get("document", "")[:200],
        }
        for chunk in manual_chunks
    ]

    if not _client:
        fallback = _safe_fallback(citations=citations, warranty_active=warranty_active)
        fallback["_model"] = "local_fallback"
        return fallback

    required_format = {
        "danger_level": "LOW|MEDIUM|HIGH",
        "call_pro": "boolean",
        "warranty_active": "boolean",
        "warranty_block_reason": "string|null",
        "manufacturer_support": "string|null",
        "fragility_warning": "string",
        "physical_brief": {
            "estimated_time_minutes": "int",
            "heavy_lifting_required": "boolean",
            "estimated_weight_lbs": "number",
            "spill_risk": "LOW|MEDIUM|HIGH",
        },
        "software_lock_warning": "string|null",
        "diagnosis_summary": "string",
        "diy_steps": ["string"],
        "required_parts": ["string"],
        "citations": [
            {
                "manual_id": "int|null",
                "chunk_id": "int|null",
                "source": "string",
                "snippet": "string",
            }
        ],
        "escalation_message": "string",
    }

    user_prompt = {
        "appliance": {"brand": appliance_brand, "model": appliance_model},
        "warranty_active": warranty_active,
        "issue_text": issue_text,
        "manual_context": manual_chunks,
        "image_context": image_context or {},
        "required_json_schema": required_format,
    }

    for candidate_model in _candidate_models(requested_model, settings.groq_diagnosis_model):
        try:
            completion = _client.chat.completions.create(
                model=candidate_model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(user_prompt)},
                ],
                temperature=0.2,
                max_tokens=900,
            )
            content = completion.choices[0].message.content or "{}"
            parsed = _extract_json(content)
            parsed.setdefault("citations", citations)
            parsed["_model"] = candidate_model
            return parsed
        except Exception:
            continue

    fallback = _safe_fallback(citations=citations, warranty_active=warranty_active)
    fallback["_model"] = "fallback_on_error"
    return fallback


def chat(message: str, model: str | None = None) -> dict[str, str]:
    """
    Send a user message to the Groq LLM and return the assistant reply.

    Args:
        message: The user's chat message.
        model:   Groq model ID to use (default: settings.groq_chat_model).

    Returns:
        Dict with formatted answer text and a YouTube search link.
    """
    content = (message or "").strip()

    if not content:
        return {
            "answer": "Please describe your appliance issue, for example: Why is my fridge overheating?",
            "video_url": "",
        }

    if _is_support_contact_request(content):
        return {
            "answer": (
                "[Summary]\nYou can use this technician contact for appliance repair, safety escalation, and expert service requests.\n\n"
                "[Safety]\nUse this contact when the issue involves major safety risk, complex internal components, or when guided steps do not resolve the problem.\n\n"
                "[Step-by-Step]\n"
                "1. Keep your appliance brand, model, and issue summary ready.\n"
                "2. Mention any error code, smoke, sparks, leak, or burning smell.\n"
                "3. Call the technician and share the problem details clearly.\n\n"
                "[When to Call a Professional]\n"
                f"{_support_contact_line()}"
            ),
            "video_url": "",
        }

    if not _is_home_appliance_query(content):
        return {"answer": _OFF_TOPIC_REFUSAL, "video_url": ""}

    video_url = _build_youtube_search_url(content)

    if _is_severe_chat_query(content):
        return {
            "answer": (
                "[Summary]\nPotentially dangerous condition detected.\n\n"
                "[Safety]\n"
                "Turn OFF the appliance immediately, isolate power/gas supply, keep distance, and ventilate the area if needed. "
                "Do not continue DIY troubleshooting.\n\n"
                "[Step-by-Step]\n"
                "1. Switch off the mains/MCB for the appliance.\n"
                "2. If gas odor is present, avoid sparks/flames and ventilate immediately.\n"
                "3. Arrange urgent professional inspection.\n\n"
                "[When to Call a Professional]\n"
                f"{settings.danger_escalation_text}\n{_support_contact_line()}"
            ),
            "video_url": video_url,
        }

    if _is_high_risk_chat_query(content):
        return {
            "answer": (
                "[Summary]\nYour issue appears high-risk and may involve hazardous internal components.\n\n"
                "[Safety]\nAvoid internal disassembly and do not bypass any protective devices.\n\n"
                "[Step-by-Step]\n"
                "1. Turn off power to the appliance.\n"
                "2. Stop troubleshooting if there are signs of heat, smell, sparks, or leakage.\n"
                "3. Keep the unit off until inspected.\n\n"
                "[When to Call a Professional]\n"
                f"{settings.danger_escalation_text}\n{_support_contact_line()}"
            ),
            "video_url": video_url,
        }

    if not _client:
        return {
            "answer": "LLM not configured. Set GROQ_API_KEY to enable chat responses.",
            "video_url": video_url,
        }

    requested_model = model or settings.groq_chat_model

    for candidate_model in _candidate_models(requested_model, settings.groq_chat_model):
        try:
            completion = _client.chat.completions.create(
                model=candidate_model,
                messages=[
                    {
                        "role": "system",
                        "content": _CHAT_SYSTEM_PROMPT
                        + "\n\n"
                        + "Out-of-scope refusal text (use exact sentence): "
                        + _OFF_TOPIC_REFUSAL,
                    },
                    {"role": "user", "content": content},
                ],
                temperature=0.2,
                max_tokens=420,
            )
            answer = completion.choices[0].message.content or ""
            polished = _ensure_structured_chat_sections(answer.strip())

            if polished.strip() == _OFF_TOPIC_REFUSAL:
                return {"answer": _OFF_TOPIC_REFUSAL, "video_url": ""}

            if _should_include_support_contact(content, polished):
                polished = _append_support_contact(polished)

            return {
                "answer": polished
                or "[Summary]\nPlease share appliance model and exact symptom for troubleshooting.",
                "video_url": video_url,
            }
        except Exception:
            continue

    return {
        "answer": "The AI provider is temporarily unavailable. Please try again in a moment.",
        "video_url": video_url,
    }
