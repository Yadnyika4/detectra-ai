"""
troubleshooting.py
-------------------
Local, offline knowledge base of network problems + a small keyword-matching
"offline assistant" that answers common questions using the knowledge base
and the current diagnosis. This is explicitly NOT a generative language
model - it is a transparent, rule-based lookup system, which is exactly
what makes it trustworthy to run fully offline.
"""

KNOWLEDGE_BASE = {
    "Network Healthy": {
        "description": "All monitored metrics (latency, packet loss, usage, errors) are within normal ranges and the Isolation Forest model did not flag the current sample as anomalous.",
        "causes": [
            "Normal, well-provisioned network conditions",
            "Low contention on the local link",
            "No active large downloads/uploads",
        ],
        "actions": [
            "No action needed",
            "Continue periodic monitoring",
            "Use this baseline to compare against future readings",
        ],
    },
    "High Latency": {
        "description": "Round-trip time to a reference host is significantly higher than normal, which can make interactive apps (calls, gaming, remote desktops) feel sluggish.",
        "causes": [
            "Distant or congested routing path to the destination",
            "Wi-Fi interference or weak signal",
            "ISP-side congestion or throttling",
            "VPN overhead",
            "Background devices saturating the link",
        ],
        "actions": [
            "Move closer to the Wi-Fi router or switch to a wired connection",
            "Restart the router/modem",
            "Disable unused VPNs",
            "Run a traceroute to identify where delay is introduced",
            "Pause large downloads on other devices and re-test",
        ],
    },
    "High Packet Loss": {
        "description": "A significant percentage of packets sent to the reference host are not receiving a reply, which shows up as choppy calls, dropped connections, or retried downloads.",
        "causes": [
            "Network congestion",
            "Weak Wi-Fi signal",
            "Faulty network interface or cable",
            "Router overload or outdated firmware",
            "ISP-side packet handling issues",
        ],
        "actions": [
            "Check Wi-Fi signal strength",
            "Check current bandwidth usage on the network",
            "Verify cabling (swap/reseat Ethernet cables if wired)",
            "Restart network equipment if appropriate",
            "Run repeated ping tests to confirm the pattern",
        ],
    },
    "Network Congestion": {
        "description": "Link utilization is very high at the same time latency and/or packet loss are degraded, indicating the network is carrying more traffic than it can comfortably handle.",
        "causes": [
            "Multiple devices streaming/downloading simultaneously",
            "Bandwidth-heavy background processes (updates, backups, torrents)",
            "Insufficient plan bandwidth for current demand",
            "Too many active connections on one link",
        ],
        "actions": [
            "Identify and pause bandwidth-heavy applications/devices",
            "Prioritize traffic with QoS settings on the router, if available",
            "Upgrade your internet plan if congestion is a recurring pattern",
            "Reduce number of simultaneous connections",
            "Re-test after closing background downloads",
        ],
    },
    "Connection Failure": {
        "description": "The device could not reliably reach the reference host at all - effectively no usable connectivity was detected.",
        "causes": [
            "Router/modem is offline or rebooting",
            "ISP outage",
            "Local network adapter disabled or misconfigured",
            "Firewall/security software blocking traffic",
            "Physical cable disconnection",
        ],
        "actions": [
            "Check that Wi-Fi/Ethernet is physically connected and enabled",
            "Restart the router and modem",
            "Check for an ISP outage in your area",
            "Temporarily disable third-party firewall software to test",
            "Try connecting a different device to confirm scope of the outage",
        ],
    },
    "Unstable Network": {
        "description": "Latency is fluctuating significantly between measurements (high jitter), even if average values look acceptable, which causes intermittent lag and dropped packets.",
        "causes": [
            "Intermittent Wi-Fi interference (microwaves, neighboring networks, walls)",
            "Loose or degraded cabling",
            "Router overheating or needing a reboot",
            "ISP-side intermittent issues",
            "Device roaming between Wi-Fi access points",
        ],
        "actions": [
            "Move to a fixed position closer to the router, or switch to wired",
            "Change Wi-Fi channel to avoid interference",
            "Reboot router/modem and check for overheating",
            "Inspect and reseat/replace cabling",
            "Monitor over a longer window to confirm the pattern before contacting your ISP",
        ],
    },
}


# ---------------------------------------------------------------------------
# Offline "assistant"
# ---------------------------------------------------------------------------
DISCLAIMER = (
    "detectra's assistant is an **offline, rule-based diagnostic helper** - "
    "it looks answers up from a local knowledge base and your current "
    "diagnosis. It is not a cloud generative AI model and has no internet "
    "connection to any external service."
)

_QA_PATTERNS = [
    (["what is wrong", "what's wrong", "whats wrong"], "current_diagnosis"),
    (["why is my network slow", "why slow", "why is it slow"], "why_slow"),
    (["reduce packet loss", "fix packet loss", "packet loss"], "High Packet Loss"),
    (["high latency", "what does high latency mean", "latency mean"], "High Latency"),
    (["how do i fix", "how to fix", "fix this", "fix the problem"], "current_actions"),
    (["congestion"], "Network Congestion"),
    (["connection failure", "no internet", "not connecting"], "Connection Failure"),
    (["unstable", "jitter"], "Unstable Network"),
    (["healthy", "is my network ok", "is my network okay"], "Network Healthy"),
]


def get_entry(diagnosis: str) -> dict:
    return KNOWLEDGE_BASE.get(diagnosis, KNOWLEDGE_BASE["Network Healthy"])


def answer_question(question: str, current_diagnosis: dict | None) -> str:
    """current_diagnosis: the dict returned by diagnosis.run_diagnosis(), or
    None if no diagnostic has been run yet this session."""
    q = (question or "").strip().lower()
    if not q:
        return "Please type a question, e.g. \"Why is my network slow?\""

    diag_label = current_diagnosis["diagnosis"] if current_diagnosis else None

    matched_key = None
    for patterns, key in _QA_PATTERNS:
        if any(p in q for p in patterns):
            matched_key = key
            break

    if matched_key is None:
        # Fall back: try to match a diagnosis name mentioned directly
        for name in KNOWLEDGE_BASE:
            if name.lower() in q:
                matched_key = name
                break

    if matched_key is None:
        return (
            "I couldn't match that to a known topic. Try asking things like "
            "\"What is wrong with my network?\", \"Why is my network slow?\", "
            "\"How can I reduce packet loss?\", or \"How do I fix this problem?\""
        )

    if matched_key == "current_diagnosis":
        if not current_diagnosis:
            return "Run a diagnostic first (Dashboard or AI Diagnosis page) so I have current metrics to explain."
        entry = get_entry(diag_label)
        evidence = "; ".join(current_diagnosis.get("evidence", []))
        return (
            f"Current diagnosis: **{diag_label}** ({current_diagnosis.get('severity')} severity, "
            f"{current_diagnosis.get('confidence')}% confidence).\n\n"
            f"{entry['description']}\n\nEvidence: {evidence}"
        )

    if matched_key == "why_slow":
        if not current_diagnosis:
            return "Run a diagnostic first so I can tell you what's affecting your speed right now."
        if diag_label in ("High Latency", "Network Congestion", "Unstable Network"):
            entry = get_entry(diag_label)
            return f"Your current diagnosis is **{diag_label}**. {entry['description']} Likely causes: " + ", ".join(entry["causes"][:3]) + "."
        return f"Your current diagnosis is **{diag_label}**, which doesn't typically present as 'slow' - see the Troubleshooting page for details."

    if matched_key == "current_actions":
        if not current_diagnosis:
            return "Run a diagnostic first so I know which problem to give you steps for."
        entry = get_entry(diag_label)
        steps = "\n".join(f"- {a}" for a in entry["actions"])
        return f"Recommended actions for **{diag_label}**:\n{steps}"

    # Direct topic lookup
    entry = get_entry(matched_key)
    causes = "\n".join(f"- {c}" for c in entry["causes"])
    actions = "\n".join(f"- {a}" for a in entry["actions"])
    return f"**{matched_key}**\n\n{entry['description']}\n\n**Possible causes:**\n{causes}\n\n**Recommended actions:**\n{actions}"
