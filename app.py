"""
Adobe Creative Cloud & Firefly Operations Agentic Copilot
Autonomous diagnostic and support triage copilot for Adobe Creative Cloud,
Express, Document Cloud, and Firefly GenAI workflows.
"""

import os
import re
import math
import socket
import webbrowser
import threading
from collections import Counter
import gradio as gr

# ==============================================================================
# 1. COLLISION-PROOF DYNAMIC PORT FINDER
# ==============================================================================
def find_available_port(start_port=7860, max_attempts=50):
    """Finds an open loopback port to prevent Address already in use crashes."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start_port

# ==============================================================================
# 2. LIGHTWEIGHT TF-IDF VECTOR RAG ENGINE (<35 MB RAM)
# ==============================================================================
ADOBE_SOP_KNOWLEDGE_BASE = [
    {
        "doc_id": "SOP-FIREFLY-CREDIT-01",
        "title": "Firefly Generative Credits & Commercial Safety Policy",
        "content": (
            "Generative Credits reset on the first day of each billing cycle. If an enterprise "
            "or Pro subscriber reaches zero credits, Firefly switches to throttled generation "
            "(slower generation queue). When an active production batch fails with ERR_FIREFLY_CREDIT_CAP "
            "and the user has an active Creative Cloud All Apps or Teams license, Tier-1 specialists "
            "can issue an automated 48-hour 50-credit courtesy burst token. Generative AI outputs "
            "generated under paid Enterprise plans are eligible for commercial indemnification "
            "provided enterprise content safety filters were not circumvented."
        ),
        "tags": ["firefly", "credits", "indemnification", "throttled", "burst", "generative", "genfill"]
    },
    {
        "doc_id": "SOP-FONTS-SYNC-02",
        "title": "Adobe Fonts Enterprise Sync & PostScript Licensing",
        "content": (
            "Adobe Fonts are licensed for personal and commercial digital design and desktop publishing. "
            "Error FONT_SYNC_REVOKED_403 occurs when an enterprise seat is reassigned, or when local "
            "TypeSupport caches corrupt the PostScript token binding. If an active entitlement exists "
            "in Adobe Admin Console, resolve the missing font lockout by triggering a remote token "
            "refresh and clearing the Creative Cloud Desktop CoreSync font lockfile. Third-party font "
            "embedding in EPUB/mobile apps requires an extended foundry license not covered by standard CC."
        ),
        "tags": ["fonts", "type", "sync", "licensing", "postscript", "core_sync", "missing_font", "acumin"]
    },
    {
        "doc_id": "SOP-CLOUD-DOCS-03",
        "title": "Cloud Document Version Conflict & Sync Lock Triage",
        "content": (
            "Cloud Documents (.psdc, .aic, .dcx) utilize block-level incremental sync. Error "
            "CLOUD_DOC_CONFLICT_409 occurs when concurrent edits occur across disconnected sessions "
            "or when Adobe Content Platform (ACP) locks fail to release post-crash. SOP mandate: "
            "Never overwrite the remote master. The diagnostic copilot must initiate an automated "
            "non-destructive snapshot rollback to the previous clean hash (N-1) and fork the local "
            "conflicted version into a recovery branch to protect customer assets from unrecoverable data loss."
        ),
        "tags": ["cloud_doc", "psdc", "aic", "conflict", "sync_lock", "acp", "version_rollback", "offline"]
    },
    {
        "doc_id": "SOP-PERF-SCRATCH-04",
        "title": "Photoshop Scratch Disk Allocation & Virtual Memory Saturation",
        "content": (
            "Error SCRATCH_DISK_ALLOCATION_FAIL indicates Photoshop primary scratch volume has "
            "under 20 GB free space during high-bit-depth rendering, smart object rasterization, or multi-artboard "
            "exports. Resolution: Instruct user to hold Cmd+Option (Mac) or Ctrl+Alt (Win) during launch "
            "to reassign secondary high-speed NVMe scratch volumes. Purge volatile undo history via Edit > Purge > All "
            "and verify that Camera Raw disk cache is not colocated on the boot partition."
        ),
        "tags": ["scratch_disk", "photoshop", "memory", "cache", "performance", "allocation", "full"]
    },
    {
        "doc_id": "SOP-STOCK-COMM-05",
        "title": "Adobe Stock Standard vs. Extended Commercial Licensing",
        "content": (
            "Standard Adobe Stock licenses grant up to 500,000 print/view impressions and digital advertising rights, "
            "but strictly prohibit use on merchandise for resale (apparel, packaging for sale, print-on-demand). "
            "Error STOCK_COMMERCIAL_RESTRICTED_401 halts export if an asset flagged for commercial packaging lacks an "
            "Extended License. Resolution: Verify organization pool balance in Adobe Admin Console and issue an "
            "automated asset upgrade token if the account possesses unallocated enterprise stock credits."
        ),
        "tags": ["stock", "licensing", "commercial", "extended_license", "merchandise", "resale", "packaging"]
    },
    {
        "doc_id": "SOP-PRINT-COLOR-06",
        "title": "InDesign & Illustrator CMYK Gamut Clipping & Spot Color Separation",
        "content": (
            "Error COLOR_GAMUT_CLIPPING_WARN occurs during PDF/X-4 export when out-of-gamut RGB saturated elements "
            "are converted to standard US Web Coated (SWOP) v2 or GRACoL2006. Uncalibrated conversions cause muddy "
            "shifts in corporate brand colors. SOP: Apply standard Adobe ACE color management, verify embedded ICC "
            "profiles, preserve K-only black channels for text (100% K vs. Rich Black), and verify spot color separation tables."
        ),
        "tags": ["cmyk", "color_gamut", "pdf_x4", "indesign", "illustrator", "icc_profile", "print", "preflight"]
    },
    {
        "doc_id": "SOP-VIDEO-PREM-07",
        "title": "Premiere Pro GPU Acceleration Dropouts & ProRes Rendering",
        "content": (
            "Error VIDEO_GPU_PIPELINE_DROP occurs during 4K/8K timeline rendering when the Mercury Playback Engine "
            "GPU driver crashes (CUDA/Metal out-of-memory). SOP mandate: Auto-switch renderer from GPU Acceleration "
            "to Software Only for the corrupted frame buffer, flush Media Cache files located under Common/Media Cache Files, "
            "and generate temporary 1080p Apple ProRes 422 Proxy streams to maintain uninterrupted editing playback."
        ),
        "tags": ["premiere", "video", "gpu", "mercury", "cuda", "metal", "prores", "render_drop", "media_cache"]
    },
    {
        "doc_id": "SOP-EXPR-BRAND-08",
        "title": "Adobe Express Enterprise Brand Kit Governance & Asset Locks",
        "content": (
            "Error EXPRESS_BRAND_POLICY_LOCK occurs in Adobe Express for Teams and Enterprise when non-admin members "
            "attempt to publish or download marketing collateral containing locked brand fonts, unapproved hex palettes, "
            "or non-compliant logo placements. Remediation: Cross-reference member permissions in Admin Console Brand Kit, "
            "auto-replace non-compliant color codes with approved primary brand hex values, or request an expedited admin exception."
        ),
        "tags": ["express", "brand_kit", "brand_locks", "governance", "templates", "enterprise", "unapproved"]
    }
]

class LeanVectorRAG:
    """In-memory TF-IDF semantic vector similarity matcher."""
    def __init__(self, docs):
        self.docs = docs
        self.vocab = {}
        self.doc_vectors = []
        self._build_index()

    def _tokenize(self, text):
        return re.findall(r'\b[a-z0-9_\-\.]{2,}\b', text.lower())

    def _build_index(self):
        doc_tokens = [self._tokenize(d["title"] + " " + d["content"] + " " + " ".join(d["tags"])) for d in self.docs]
        df = Counter()
        for tokens in doc_tokens:
            for t in set(tokens):
                df[t] += 1
        num_docs = len(self.docs)
        self.vocab = {t: math.log((num_docs + 1) / (df[t] + 1)) + 1.0 for t in df}
        
        for tokens in doc_tokens:
            tf = Counter(tokens)
            vec = {t: (tf[t] / len(tokens)) * self.vocab[t] for t in tokens if t in self.vocab}
            norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
            self.doc_vectors.append({t: v / norm for t, v in vec.items()})

    def search(self, query, top_k=2):
        q_tokens = self._tokenize(query)
        if not q_tokens:
            return [(self.docs[0], 0.5)]
        tf = Counter(q_tokens)
        q_vec = {t: (tf[t] / len(q_tokens)) * self.vocab.get(t, 1.0) for t in q_tokens}
        q_norm = math.sqrt(sum(v * v for v in q_vec.values())) or 1.0
        q_vec_norm = {t: v / q_norm for t, v in q_vec.items()}

        scores = []
        for idx, d_vec in enumerate(self.doc_vectors):
            dot = sum(d_vec.get(t, 0.0) * val for t, val in q_vec_norm.items())
            scores.append((self.docs[idx], dot))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

rag_engine = LeanVectorRAG(ADOBE_SOP_KNOWLEDGE_BASE)

# ==============================================================================
# 3. 8 EXTENDED PRODUCTION INCIDENTS
# ==============================================================================
SCENARIOS = {
    "ADB-FIREFLY-801 (Firefly Credit Cap Reached in Deadline Batch)": {
        "ticket_id": "ADB-FIREFLY-801",
        "app": "Adobe Firefly / Photoshop GenFill",
        "user_tier": "Creative Cloud Enterprise VIP",
        "error_code": "ERR_FIREFLY_CREDIT_CAP",
        "asset_urn": "urn:aaid:sc:US:f892a01b-419b-4682-a052-192a5df12001",
        "details": "User ran 200 high-res Generative Fill iterations during agency campaign launch. Credit balance hit 0 and jobs dropped to throttled queue with generation timeouts."
    },
    "ADB-FONTS-802 (Enterprise Font Sync Revoked Before Print Export)": {
        "ticket_id": "ADB-FONTS-802",
        "app": "InDesign CC / Adobe Express",
        "user_tier": "Creative Cloud for Teams",
        "error_code": "FONT_SYNC_REVOKED_403",
        "asset_urn": "urn:aaid:sc:EU:9912bc44-5501-4473-b312-cda411890223",
        "details": "Brand typography 'Acumin Pro Variable' missing on packaged document export. Adobe Fonts shows font active, but local CoreSync agent threw HTTP 403."
    },
    "ADB-CLOUD-803 (Photoshop Cloud Document Version Merge Conflict)": {
        "ticket_id": "ADB-CLOUD-803",
        "app": "Adobe Photoshop Cloud (.psdc)",
        "user_tier": "Creative Cloud Individual Pro",
        "error_code": "CLOUD_DOC_CONFLICT_409",
        "asset_urn": "urn:aaid:sc:US:6371cb11-ee89-4921-9876-0012fabc8899",
        "details": "Creative director worked offline on laptop; upon reconnection, cloud document threw version conflict 409 and locked artboard saves to prevent desync."
    },
    "ADB-PERF-804 (Photoshop Scratch Disk Volume Depleted)": {
        "ticket_id": "ADB-PERF-804",
        "app": "Adobe Photoshop Desktop 2026",
        "user_tier": "Creative Cloud All Apps",
        "error_code": "SCRATCH_DISK_ALLOCATION_FAIL",
        "asset_urn": "urn:aaid:sc:AP:0092fa88-3312-4890-a771-449901eedcba",
        "details": "User attempting 16-bit multi-layered poster export; application crashed with 'Could not complete your request because the scratch disks are full'."
    },
    "ADB-STOCK-805 (Commercial Packaging Extended License Lock)": {
        "ticket_id": "ADB-STOCK-805",
        "app": "Adobe Illustrator / Adobe Stock",
        "user_tier": "Creative Cloud Enterprise VIP",
        "error_code": "STOCK_COMMERCIAL_RESTRICTED_401",
        "asset_urn": "urn:aaid:sc:US:1189ef33-9021-4223-8811-9821fab44100",
        "details": "Retail merchandise team blocked from exporting packaging artwork. Stock asset #88910243 licensed under Standard License, requiring Extended License upgrade."
    },
    "ADB-COLOR-806 (CMYK Gamut Clipping on Brand Packaging PDF/X-4)": {
        "ticket_id": "ADB-COLOR-806",
        "app": "Adobe InDesign 2026",
        "user_tier": "Creative Cloud for Teams",
        "error_code": "COLOR_GAMUT_CLIPPING_WARN",
        "asset_urn": "urn:aaid:sc:EU:7721ab88-4422-4910-bc21-6655fa990012",
        "details": "Print shop rejected packaging preflight. Vivid electric-blue RGB hero element clipped during automated SWOP CMYK conversion, dropping brand delta-E out of tolerance."
    },
    "ADB-PREM-807 (Premiere Pro Mercury GPU Engine Crash on 4K Export)": {
        "ticket_id": "ADB-PREM-807",
        "app": "Adobe Premiere Pro 2026",
        "user_tier": "Creative Cloud for Teams",
        "error_code": "VIDEO_GPU_PIPELINE_DROP",
        "asset_urn": "urn:aaid:sc:US:8899aa12-7711-4091-a123-bc9988220011",
        "details": "Video editing team encountering frame render drops on timeline export at 84%. Mercury Playback CUDA buffer crashed due to memory exhaustion."
    },
    "ADB-EXPR-808 (Adobe Express Locked Brand Kit Policy Violation)": {
        "ticket_id": "ADB-EXPR-808",
        "app": "Adobe Express Enterprise",
        "user_tier": "Creative Cloud Enterprise VIP",
        "error_code": "EXPRESS_BRAND_POLICY_LOCK",
        "asset_urn": "urn:aaid:sc:US:3311bb44-8822-4411-9900-a1b2c3d4e5f6",
        "details": "Marketing manager blocked from downloading campaign banner because layout used custom unapproved hex colors and locked corporate logo spacing."
    }
}

# ==============================================================================
# 4. AUTONOMOUS REACT DIAGNOSTIC & REMEDIATION TOOLS
# ==============================================================================
def tool_inspect_asset_manifest(asset_urn, app_name):
    """Simulates Adobe Content Platform (ACP) metadata inspection."""
    if "f892a01b" in asset_urn:
        return {
            "urn": asset_urn,
            "layers": 34,
            "embedded_generative_elements": 18,
            "color_profile": "Adobe RGB (1998)",
            "file_size_mb": 420.5,
            "sync_lock_status": "UNLOCKED",
            "last_cloud_snapshot": "2026-09-26T09:12:00Z"
        }
    elif "9912bc44" in asset_urn:
        return {
            "urn": asset_urn,
            "layers": 12,
            "fonts_detected": ["Acumin Pro Variable", "Adobe Garamond Pro"],
            "missing_postscript_fonts": ["AcuminPro-Bold"],
            "sync_lock_status": "TOKEN_INVALIDATED",
            "last_cloud_snapshot": "2026-09-26T11:45:00Z"
        }
    elif "6371cb11" in asset_urn:
        return {
            "urn": asset_urn,
            "layers": 78,
            "sync_lock_status": "CONCURRENT_CONFLICT_LOCK",
            "master_hash": "sha256:4a88b1...99f",
            "local_branch_hash": "sha256:7c11a2...00d",
            "conflict_type": "FORKED_OFFLINE_SAVE"
        }
    elif "1189ef33" in asset_urn:
        return {
            "urn": asset_urn,
            "stock_asset_id": "88910243",
            "license_type": "Standard",
            "commercial_resale_allowed": False,
            "enterprise_pool_available": True
        }
    elif "8899aa12" in asset_urn:
        return {
            "urn": asset_urn,
            "video_tracks": 6,
            "resolution": "3840x2160 (4K UHD)",
            "codec": "ProRes 422 HQ",
            "gpu_render_state": "CUDA_OUT_OF_MEMORY",
            "cache_fragmentation": "HIGH"
        }
    elif "3311bb44" in asset_urn:
        return {
            "urn": asset_urn,
            "brand_kit_id": "BK-CORP-GLOBAL-2026",
            "violations": ["UNAPPROVED_HEX_#FF0055", "RESIZED_LOCKED_LOGO_MARK"],
            "governance_mode": "STRICT_ENFORCEMENT"
        }
    else:
        return {
            "urn": asset_urn,
            "app": app_name,
            "sync_lock_status": "NORMAL",
            "icc_profile": "SWOP CMYK v2 (Uncalibrated Gamut Shift Detected)",
            "file_size_mb": 185.0
        }

def tool_audit_generative_credits(user_tier, error_code):
    """Simulates Firefly Credit Ledger audit."""
    if error_code == "ERR_FIREFLY_CREDIT_CAP" or "credit" in error_code.lower():
        return {
            "monthly_quota": 1000,
            "credits_remaining": 0,
            "queue_state": "THROTTLED_HIGH_LATENCY",
            "eligible_for_burst_concession": True,
            "policy_max_burst": 50,
            "commercial_safety_indemnification": "ACTIVE_COVERED"
        }
    return {
        "monthly_quota": 500,
        "credits_remaining": 340,
        "queue_state": "STANDARD_PRIORITY",
        "eligible_for_burst_concession": False
    }

def tool_verify_font_and_stock_licensing(user_tier, error_code):
    """Simulates Adobe Fonts Entitlement & Stock Ledger checks."""
    if error_code == "FONT_SYNC_REVOKED_403":
        return {
            "license_status": "ACTIVE_SEAT_ENTITLED",
            "admin_console_state": "VALID",
            "core_sync_token_expired": True,
            "action_required": "REMOTE_TOKEN_FLUSH"
        }
    elif error_code == "STOCK_COMMERCIAL_RESTRICTED_401":
        return {
            "current_license": "Standard (500k impressions, non-resale)",
            "required_license": "Extended Commercial Resale",
            "org_stock_credit_pool": 14,
            "can_auto_upgrade": True
        }
    return {"license_status": "VALID", "restrictions": "NONE"}

def tool_execute_adobe_remediation(action_type, asset_urn):
    """Simulates backend API remediation actions."""
    if action_type == "GRANT_FIREFLY_BURST_CREDITS":
        return {
            "status": "SUCCESS",
            "action": "Issued 50-Credit Emergency Firefly Burst",
            "validity": "48 Hours",
            "ticket_ref": "ADB-BURST-GENAI-48H",
            "unthrottled": True
        }
    elif action_type == "REFRESH_FONT_SYNC_TOKEN":
        return {
            "status": "SUCCESS",
            "action": "CoreSync Security Token Invalidated & Re-issued",
            "local_cache_flushed": True,
            "postscript_binding": "RESTORED"
        }
    elif action_type == "FORK_AND_RESTORE_CLOUD_VERSION":
        return {
            "status": "SUCCESS",
            "action": "Restored Remote Master to Hash N-1; Local Branch Forked to 'Recovery_Artboard_2026'",
            "data_loss_prevented": True
        }
    elif action_type == "UPGRADE_STOCK_LICENSE":
        return {
            "status": "SUCCESS",
            "action": "Debited 1 Enterprise Stock Credit; Asset Upgraded to Extended Commercial License",
            "invoice_cleared": True
        }
    elif action_type == "CONFIGURE_SECONDARY_SCRATCH":
        return {
            "status": "SUCCESS",
            "action": "Dispatched In-App Diagnostic Config to Reassign Secondary NVMe Scratch Volume",
            "purge_cache_command": "DISPATCHED"
        }
    elif action_type == "SWITCH_VIDEO_PROXIES_AND_FLUSH":
        return {
            "status": "SUCCESS",
            "action": "Flushed Corrupted Media Cache & Generated 1080p ProRes 422 Proxy Timeline",
            "playback_restored": True
        }
    elif action_type == "CONFORM_EXPRESS_BRAND_KIT":
        return {
            "status": "SUCCESS",
            "action": "Auto-mapped Non-Compliant Colors to Official Primary Hex Palette; Unlocked Export",
            "governance_approved": True
        }
    else:
        return {
            "status": "SUCCESS",
            "action": "Injected PDF/X-4 GRACoL2006 Color Management Preset into User Document Stream"
        }

# ==============================================================================
# 5. AGENTIC ORCHESTRATION ENGINE (PERCEPTION -> RAG -> TOOLS -> MINTO)
# ==============================================================================
def run_adobe_copilot(scenario_choice, custom_claim, tier_override, specialist_action_override):
    trace_steps = []
    
    # Step 1: Perception
    if custom_claim.strip():
        user_text = custom_claim.strip()
        scenario_data = {
            "ticket_id": "ADB-CUSTOM-INQUIRY",
            "app": "Creative Cloud Diagnostic Engine",
            "user_tier": tier_override if tier_override != "Default from Scenario" else "Creative Cloud Enterprise VIP",
            "error_code": "ERR_CUSTOM_WORKFLOW",
            "asset_urn": "urn:aaid:sc:CUSTOM:0192aacc-4411-9988-1234-abcd00112233",
            "details": user_text
        }
        trace_steps.append(f"[PERCEPTION] Custom User Query Received:\n'{user_text}'")
    else:
        scenario_data = SCENARIOS.get(scenario_choice, SCENARIOS["ADB-FIREFLY-801 (Firefly Credit Cap Reached in Deadline Batch)"])
        if tier_override != "Default from Scenario":
            scenario_data["user_tier"] = tier_override
        user_text = f"{scenario_data['app']} - {scenario_data['error_code']}: {scenario_data['details']}"
        trace_steps.append(
            f"[PERCEPTION] Ticket Ingested: {scenario_data['ticket_id']}\n"
            f"• App: {scenario_data['app']}\n"
            f"• Tier: {scenario_data['user_tier']}\n"
            f"• Error Signature: {scenario_data['error_code']}\n"
            f"• Asset URN: {scenario_data['asset_urn']}"
        )

    # Step 2: Vector RAG Grounding
    rag_results = rag_engine.search(user_text, top_k=2)
    top_doc, score = rag_results[0]
    trace_steps.append(
        f"[DOMAIN RAG RETRIEVAL] Cosine Score: {score:.3f}\n"
        f"• Retained Knowledge: {top_doc['doc_id']} ('{top_doc['title']}')\n"
        f"• Grounded Policy Excerpt: \"{top_doc['content'][:180]}...\""
    )

    # Step 3: Tool Execution (ReAct Loop)
    asset_manifest = tool_inspect_asset_manifest(scenario_data["asset_urn"], scenario_data["app"])
    trace_steps.append(f"[TOOL ACTION: tool_inspect_asset_manifest] Inspected ACP Asset Manifest:\n{asset_manifest}")

    credit_audit = tool_audit_generative_credits(scenario_data["user_tier"], scenario_data["error_code"])
    trace_steps.append(f"[TOOL ACTION: tool_audit_generative_credits] Ledger Status:\n{credit_audit}")

    licensing_audit = tool_verify_font_and_stock_licensing(scenario_data["user_tier"], scenario_data["error_code"])
    trace_steps.append(f"[TOOL ACTION: tool_verify_font_and_stock_licensing] Licensing State:\n{licensing_audit}")

    # Determine Remediation Action (respecting manual override if specified)
    if specialist_action_override != "Auto-Detect Best Remediation":
        remediation_action = specialist_action_override
    else:
        remediation_action = "INJECT_COLOR_PRESET"
        if "credit" in user_text.lower() or scenario_data["error_code"] == "ERR_FIREFLY_CREDIT_CAP":
            remediation_action = "GRANT_FIREFLY_BURST_CREDITS"
        elif "font" in user_text.lower() or scenario_data["error_code"] == "FONT_SYNC_REVOKED_403":
            remediation_action = "REFRESH_FONT_SYNC_TOKEN"
        elif "conflict" in user_text.lower() or scenario_data["error_code"] == "CLOUD_DOC_CONFLICT_409":
            remediation_action = "FORK_AND_RESTORE_CLOUD_VERSION"
        elif "stock" in user_text.lower() or scenario_data["error_code"] == "STOCK_COMMERCIAL_RESTRICTED_401":
            remediation_action = "UPGRADE_STOCK_LICENSE"
        elif "scratch" in user_text.lower() or scenario_data["error_code"] == "SCRATCH_DISK_ALLOCATION_FAIL":
            remediation_action = "CONFIGURE_SECONDARY_SCRATCH"
        elif "gpu" in user_text.lower() or "premiere" in user_text.lower() or scenario_data["error_code"] == "VIDEO_GPU_PIPELINE_DROP":
            remediation_action = "SWITCH_VIDEO_PROXIES_AND_FLUSH"
        elif "brand" in user_text.lower() or "express" in user_text.lower() or scenario_data["error_code"] == "EXPRESS_BRAND_POLICY_LOCK":
            remediation_action = "CONFORM_EXPRESS_BRAND_KIT"

    remediation_result = tool_execute_adobe_remediation(remediation_action, scenario_data["asset_urn"])
    trace_steps.append(f"[AUTONOMOUS REMEDIATION: tool_execute_adobe_remediation] Action '{remediation_action}':\n{remediation_result}")

    # Step 4: Synthesize Minto Work Order & Customer-Ready Output
    minto_work_order = f"""### 🛠️ ADOBE CARE SPECIALIST MINTO WORK ORDER
**TICKET ID:** {scenario_data['ticket_id']} | **PRIORITY:** High (Production Deadline)
**APPLICATION / STACK:** {scenario_data['app']}
**ENTITLEMENT TIER:** {scenario_data['user_tier']}

---

#### 1. CORE RECOMMENDATION (Answer-First)
* **Root Cause:** {scenario_data['error_code']} triggered by operational constraint on asset `{scenario_data['asset_urn'][:36]}...`.
* **Autonomous Resolution:** Programmatically executed `{remediation_action}` ({remediation_result['action']}).
* **Action Required by Specialist:** Inform customer of live automated remediation; verify local sync state.

#### 2. TELEMETRY & DIAGNOSTIC FINDINGS
* **Asset Manifest Status:** {asset_manifest.get('sync_lock_status', asset_manifest.get('gpu_render_state', 'HEALTHY'))}
* **Generative Credit Ledger:** {credit_audit.get('credits_remaining', 'N/A')} credits left | Queue: {credit_audit.get('queue_state', 'NORMAL')}
* **Licensing Verification:** {licensing_audit.get('license_status', licensing_audit.get('current_license', 'NORMAL'))}

#### 3. POLICY & COMPLIANCE GROUNDING ({top_doc['doc_id']})
* **Standard Operating Procedure:** {top_doc['title']}
* **Compliance Assurance:** Action strictly complies with Adobe Commercial Safety Indemnification & Enterprise Licensing Terms. Zero manual credit leakage.
"""

    customer_chat = f"""Hello! This is Adobe Creative Cloud Automated Care.

We detected an issue affecting your creative workflow ({scenario_data['error_code']}):
👉 **What Happened:** {scenario_data['details']}
⚡ **Automated Action Taken:** {remediation_result['action']}

**Next Steps for You:**
1. Please refresh your Creative Cloud Desktop client or restart your active editing session.
2. Your asset and workspace have been unlocked for export/rendering.
3. If you experience further latency or missing components, reply directly to this message to connect with a Senior Adobe Care Specialist.

*Reference Case ID: {scenario_data['ticket_id']}*"""

    rag_grounding_text = f"""### 📚 Retained Knowledge Base Document: {top_doc['doc_id']}
**Title:** {top_doc['title']}
**Relevance Score:** {score:.4f}

**Official Adobe Policy Excerpt:**
{top_doc['content']}
"""

    return minto_work_order, "\n\n".join(trace_steps), rag_grounding_text, customer_chat

# ==============================================================================
# 6. GRADIO OPERATIONAL COCKPIT UI WITH EXAMPLES & FEATURES
# ==============================================================================
def create_ui():
    custom_css = """
    .gradio-container { font-family: 'Segoe UI', -apple-system, Roboto, Helvetica, Arial, sans-serif; }
    .header-box { background: linear-gradient(135deg, #FF0000 0%, #8A0000 100%); color: white; padding: 22px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    """
    with gr.Blocks(title="Adobe Creative Cloud & Firefly Agentic Copilot", css=custom_css) as demo:
        gr.HTML("""
        <div class="header-box">
            <h1 style="margin:0; font-size:26px;">🔴 Adobe Creative Cloud & Firefly Operations Agentic Copilot</h1>
            <p style="margin:5px 0 0 0; opacity:0.95;">Autonomous Enterprise Triage & Diagnostic Copilot for Photoshop, InDesign, Illustrator, Premiere Pro, Express & Firefly GenAI</p>
        </div>
        """)

        with gr.Row():
            with gr.Column(scale=4):
                scenario_dropdown = gr.Dropdown(
                    label="1. Select Inbound Creative Cloud Incident Scenario",
                    choices=list(SCENARIOS.keys()),
                    value=list(SCENARIOS.keys())[0]
                )

                with gr.Accordion("⚙️ Advanced Operational Controls & Overrides", open=False):
                    tier_selector = gr.Radio(
                        label="Override Account Entitlement Tier",
                        choices=["Default from Scenario", "Creative Cloud Individual Pro", "Creative Cloud for Teams", "Creative Cloud Enterprise VIP", "Higher Education Student"],
                        value="Default from Scenario"
                    )
                    action_override = gr.Dropdown(
                        label="Support Specialist Action Override",
                        choices=[
                            "Auto-Detect Best Remediation",
                            "GRANT_FIREFLY_BURST_CREDITS",
                            "REFRESH_FONT_SYNC_TOKEN",
                            "FORK_AND_RESTORE_CLOUD_VERSION",
                            "UPGRADE_STOCK_LICENSE",
                            "CONFIGURE_SECONDARY_SCRATCH",
                            "SWITCH_VIDEO_PROXIES_AND_FLUSH",
                            "CONFORM_EXPRESS_BRAND_KIT"
                        ],
                        value="Auto-Detect Best Remediation"
                    )

                custom_input = gr.Textbox(
                    label="2. Free-Form Customer Inquiry / Custom Error Telemetry",
                    placeholder="e.g., My Photoshop generative fill is throwing a credit limit error during our magazine print deadline...",
                    lines=3
                )
                
                triage_btn = gr.Button("🚀 Run Autonomous Agentic Triage", variant="primary")

                gr.Markdown("### 💡 Quick-Fill Example Inquiries (Click to Load)")
                gr.Examples(
                    examples=[
                        ["", "We are blocked from packaging our client catalog because Acumin Pro Bold is throwing HTTP 403 in CoreSync."],
                        ["", "Our Premiere Pro timeline keeps crashing on export at 84% due to CUDA GPU buffer overflow."],
                        ["", "My colleague and I both edited the Photoshop cloud document while offline and now saves are locked with conflict 409."],
                        ["", "Our retail apparel mockups in Illustrator are blocked from commercial export because of Adobe Stock standard license limits."],
                        ["", "Photoshop tells me scratch disks are full even though my Mac still has 15 GB free on the startup disk."]
                    ],
                    inputs=[scenario_dropdown, custom_input],
                    label="Sample Production Scenarios"
                )

                gr.Markdown("""
                #### 📌 Verified SLA & Diagnostic Scope
                * **Firefly GenAI:** Credit caps, commercial safety indemnification, throttled queues.
                * **Adobe Fonts:** PostScript mismatches, CoreSync HTTP 403 lockfiles.
                * **Cloud Documents:** Non-destructive `.psdc`/`.aic` merge conflict rollbacks.
                * **Hardware & Video:** Scratch disk allocation, Premiere CUDA/Metal buffer drops.
                * **Express Governance:** Brand Kit locking, unapproved color palette auto-conformance.
                """)

            with gr.Column(scale=6):
                with gr.Tabs():
                    with gr.TabItem("📋 Minto Work Order"):
                        minto_out = gr.Markdown(label="Specialist Work Order")
                    with gr.TabItem("🧠 ReAct Reasoning Trace"):
                        trace_out = gr.Code(label="Real-Time Agent Execution Log", language="markdown", lines=17)
                    with gr.TabItem("📖 Domain Vector RAG"):
                        rag_out = gr.Markdown(label="Retrieved Adobe SOP Grounding")
                    with gr.TabItem("💬 In-App Customer Response"):
                        customer_out = gr.Textbox(label="Ready-to-Send In-App Communication", lines=10)

        triage_btn.click(
            fn=run_adobe_copilot,
            inputs=[scenario_dropdown, custom_input, tier_selector, action_override],
            outputs=[minto_out, trace_out, rag_out, customer_out]
        )
        
        # Prepopulate demo on launch
        demo.load(
            fn=run_adobe_copilot,
            inputs=[scenario_dropdown, custom_input, tier_selector, action_override],
            outputs=[minto_out, trace_out, rag_out, customer_out]
        )

    return demo

# ==============================================================================
# 7. EXECUTION & AUTO-BROWSER LAUNCH
# ==============================================================================
if __name__ == "__main__":
    assigned_port = find_available_port(7860)
    print(f"🚀 Initializing Adobe Agentic Service Copilot on http://127.0.0.1:{assigned_port}")
    
    app = create_ui()
    
    # Auto-open browser in local desktop environments
    threading.Timer(1.5, lambda: webbrowser.open(f"http://127.0.0.1:{assigned_port}")).start()
    
    app.launch(
        server_name="127.0.0.1",
        server_port=assigned_port,
        share=False
    )
