"""
diagnosis.py
------------
Combines the Isolation Forest anomaly result with explainable,
threshold-based network diagnostic rules to produce:

* A single diagnosis label
* A severity level
* A 0-100 network health score
* A confidence percentage
* Plain-English evidence explaining the diagnosis

The diagnosis is based on the network metrics actually displayed
to the user. Isolation Forest provides additional anomaly evidence.
"""

import config
import ml_model


# ---------------------------------------------------------------------------
# Rule evaluation
# ---------------------------------------------------------------------------

def _classify_metric(value, warn, high, crit, higher_is_worse=True):
    """
    Return one of:
    Normal / Warning / High / Critical
    for a single network metric.
    """

    if value is None:
        return "Normal"

    if higher_is_worse:
        if value >= crit:
            return "Critical"

        if value >= high:
            return "High"

        if value >= warn:
            return "Warning"

        return "Normal"

    return "Normal"


# Severity ranking
_SEVERITY_RANK = {
    "Normal": 0,
    "Warning": 1,
    "High": 2,
    "Critical": 3,
}


def _worst(*levels):
    """
    Return the worst severity from the supplied severity levels.
    """
    return max(levels, key=lambda level: _SEVERITY_RANK[level])


def evaluate_rules(metrics: dict) -> dict:
    """
    Apply explainable network diagnostic rules.

    Returns severity classifications for individual metrics
    and an evidence-strength score between 0 and 1.
    """

    th = config.THRESHOLDS

    latency = metrics.get("latency", 0.0) or 0.0
    packet_loss = metrics.get("packet_loss", 0.0) or 0.0
    network_usage = metrics.get("network_usage", 0.0) or 0.0
    network_errors = metrics.get("network_errors", 0) or 0
    jitter = metrics.get("jitter", 0.0) or 0.0
    connectivity_ok = metrics.get("connectivity_ok", True)

    latency_sev = _classify_metric(
        latency,
        th["latency_warning_ms"],
        th["latency_high_ms"],
        th["latency_critical_ms"],
    )

    loss_sev = _classify_metric(
        packet_loss,
        th["packet_loss_warning_pct"],
        th["packet_loss_high_pct"],
        th["packet_loss_critical_pct"],
    )

    usage_sev = _classify_metric(
        network_usage,
        th["network_usage_warning_pct"],
        th["network_usage_high_pct"],
        th["network_usage_critical_pct"],
    )

    errors_sev = _classify_metric(
        network_errors,
        th["errors_warning"],
        th["errors_high"],
        th["errors_critical"],
    )

    # Large jitter means network stability is poor.
    unstable = jitter >= th["jitter_unstable_ms"]

    # Detect complete or near-complete connection failure.
    connection_failure = (
        (not connectivity_ok)
        or packet_loss >= 95
        or latency >= 900
    )

    overall_rule_severity = _worst(
        latency_sev,
        loss_sev,
        usage_sev,
        errors_sev,
    )

    if connection_failure:
        overall_rule_severity = "Critical"

    # Evidence strength represents how strongly the network metrics
    # support an abnormal diagnosis.
    weights = {
        "Normal": 0.0,
        "Warning": 0.4,
        "High": 0.7,
        "Critical": 1.0,
    }

    evidence_strength = max(
        weights[latency_sev],
        weights[loss_sev],
        weights[usage_sev],
        weights[errors_sev],
    )

    if connection_failure:
        evidence_strength = 1.0

    return {
        "latency_sev": latency_sev,
        "loss_sev": loss_sev,
        "usage_sev": usage_sev,
        "errors_sev": errors_sev,
        "unstable": unstable,
        "connection_failure": connection_failure,
        "overall_rule_severity": overall_rule_severity,
        "evidence_strength": evidence_strength,
    }


# ---------------------------------------------------------------------------
# Diagnosis label selection
# ---------------------------------------------------------------------------

def determine_diagnosis(metrics: dict, rules: dict) -> str:
    """
    Pick exactly one network diagnosis.

    Priority:
    1. Connection Failure
    2. Unstable Network
    3. Network Congestion
    4. High Packet Loss
    5. High Latency
    6. Network Healthy
    """

    if rules["connection_failure"]:
        return "Connection Failure"

    if (
        rules["unstable"]
        and rules["overall_rule_severity"] in ("High", "Critical")
    ):
        return "Unstable Network"

    # Congestion requires high network usage together with
    # latency or packet-loss degradation.
    if rules["usage_sev"] in ("High", "Critical") and (
        rules["latency_sev"] in ("Warning", "High", "Critical")
        or rules["loss_sev"] in ("Warning", "High", "Critical")
    ):
        return "Network Congestion"

    if rules["loss_sev"] in ("High", "Critical"):
        return "High Packet Loss"

    if rules["latency_sev"] in ("High", "Critical"):
        return "High Latency"

    if rules["overall_rule_severity"] == "Normal":
        return "Network Healthy"

    # Handle Warning-level problems.
    if rules["loss_sev"] != "Normal":
        return "High Packet Loss"

    if rules["latency_sev"] != "Normal":
        return "High Latency"

    if rules["usage_sev"] != "Normal":
        return "Network Congestion"

    return "Network Healthy"


# ---------------------------------------------------------------------------
# Severity
# ---------------------------------------------------------------------------

def determine_severity(rules: dict) -> str:
    """
    Return overall rule-based severity.
    """
    return rules["overall_rule_severity"]


# ---------------------------------------------------------------------------
# Network health score
# ---------------------------------------------------------------------------

def compute_health_score(metrics: dict) -> float:
    """
    Calculate a deterministic network health score from 0 to 100.

    Higher score = healthier network.
    Lower score = poorer network.
    """

    th = config.THRESHOLDS

    latency = metrics.get("latency", 0.0) or 0.0
    packet_loss = metrics.get("packet_loss", 0.0) or 0.0
    network_usage = metrics.get("network_usage", 0.0) or 0.0
    network_errors = metrics.get("network_errors", 0) or 0
    connectivity_ok = metrics.get("connectivity_ok", True)

    def penalty(value, warn, crit, max_penalty):

        if value <= warn:
            return 0.0

        if value >= crit:
            return max_penalty

        fraction = (value - warn) / max(
            crit - warn,
            1e-6,
        )

        return max_penalty * fraction

    latency_penalty = penalty(
        latency,
        th["latency_warning_ms"],
        th["latency_critical_ms"],
        30,
    )

    loss_penalty = penalty(
        packet_loss,
        th["packet_loss_warning_pct"],
        th["packet_loss_critical_pct"],
        30,
    )

    usage_penalty = penalty(
        network_usage,
        th["network_usage_warning_pct"],
        th["network_usage_critical_pct"],
        20,
    )

    errors_penalty = penalty(
        network_errors,
        th["errors_warning"],
        th["errors_critical"],
        20,
    )

    score = 100 - (
        latency_penalty
        + loss_penalty
        + usage_penalty
        + errors_penalty
    )

    # If connectivity completely fails, health cannot exceed 5.
    if not connectivity_ok:
        score = min(score, 5)

    return round(
        max(
            0.0,
            min(100.0, score),
        ),
        1,
    )


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------

def compute_confidence(
    diagnosis: str,
    rules: dict,
    ml_result: dict,
) -> float:
    """
    Calculate diagnosis confidence.

    Confidence combines:

    60% rule-based evidence
    40% Isolation Forest anomaly evidence

    The value is deterministic and not random.
    """

    evidence_strength = rules["evidence_strength"]

    ml_strength = (
        ml_result.get("anomaly_strength", 0.0) or 0.0
    ) / 100.0

    ml_is_anomaly = ml_result.get(
        "is_anomaly",
        False,
    )

    rules_say_abnormal = (
        diagnosis != "Network Healthy"
    )

    # Check whether ML and rule-based diagnosis agree.
    if ml_is_anomaly == rules_say_abnormal:
        ml_agreement = ml_strength
    else:
        # Reduce ML contribution if it disagrees with the rules.
        ml_agreement = ml_strength * 0.3

    w_rules = 0.6
    w_ml = 0.4

    raw_confidence = (
        w_rules * evidence_strength
        + w_ml * ml_agreement
    )

    # If the network is healthy AND the ML model agrees,
    # give the healthy diagnosis strong confidence.
    if diagnosis == "Network Healthy" and not ml_is_anomaly:
        raw_confidence = max(
            raw_confidence,
            0.85,
        )

    confidence_pct = round(
        min(raw_confidence, 0.99) * 100,
        1,
    )

    # If there is any abnormal signal, avoid showing
    # an extremely low confidence value.
    if rules_say_abnormal or ml_is_anomaly:
        confidence_pct = max(
            confidence_pct,
            40.0,
        )

    return min(
        confidence_pct,
        99.0,
    )


# ---------------------------------------------------------------------------
# Explainability
# ---------------------------------------------------------------------------

def build_evidence(
    metrics: dict,
    rules: dict,
    diagnosis: str,
    ml_result: dict,
) -> list:
    """
    Generate plain-English explanations for the diagnosis.

    Only actual displayed metric values are used.
    """

    evidence = []

    latency = metrics.get("latency", 0.0) or 0.0
    packet_loss = metrics.get("packet_loss", 0.0) or 0.0
    network_usage = metrics.get("network_usage", 0.0) or 0.0
    network_errors = metrics.get("network_errors", 0) or 0
    jitter = metrics.get("jitter", 0.0) or 0.0
    connectivity_ok = metrics.get("connectivity_ok", True)

    # ---------------------------------------------------------
    # Rule-based evidence
    # ---------------------------------------------------------

    if rules["connection_failure"]:
        evidence.append(
            f"Connectivity check failed "
            f"(packet loss {packet_loss:.0f}%, "
            f"connectivity_ok={connectivity_ok})."
        )

    if rules["latency_sev"] != "Normal":
        evidence.append(
            f"Latency reached {latency:.0f} ms "
            f"({rules['latency_sev']} threshold exceeded)."
        )

    if rules["loss_sev"] != "Normal":
        evidence.append(
            f"Packet loss reached {packet_loss:.1f}% "
            f"({rules['loss_sev']} threshold exceeded)."
        )

    if rules["usage_sev"] != "Normal":
        evidence.append(
            f"Network usage reached {network_usage:.0f}% "
            f"of estimated capacity "
            f"({rules['usage_sev']} threshold exceeded)."
        )

    if rules["errors_sev"] != "Normal":
        evidence.append(
            f"{network_errors} network error(s)/drops observed "
            f"({rules['errors_sev']} threshold exceeded)."
        )

    if rules["unstable"]:
        evidence.append(
            f"Latency jitter reached {jitter:.0f} ms, "
            f"indicating an unstable connection."
        )

    # ---------------------------------------------------------
    # ML evidence
    # ---------------------------------------------------------

    if ml_result.get("model_available", True):

        if ml_result.get("is_anomaly"):

            evidence.append(
                f"Isolation Forest marked the sample as anomalous "
                f"(anomaly strength "
                f"{ml_result.get('anomaly_strength', 0):.0f}/100)."
            )

        else:

            evidence.append(
                f"Isolation Forest marked the sample as within normal range "
                f"(anomaly strength "
                f"{ml_result.get('anomaly_strength', 0):.0f}/100)."
            )

    else:

        evidence.append(
            "ML model unavailable this run - "
            "diagnosis based on rule thresholds only."
        )

    # ---------------------------------------------------------
    # Special handling for Network Healthy
    # ---------------------------------------------------------

    if diagnosis == "Network Healthy":

        # Preserve Isolation Forest explanation if available.
        ml_lines = [
            e
            for e in evidence
            if "Isolation Forest" in e
        ]

        # Always clearly explain why the rule-based diagnosis is healthy.
        evidence = [
            "All monitored network metrics are within normal fault thresholds."
        ]

        # Add ML information.
        if ml_lines:
            evidence.extend(ml_lines)

        # IMPORTANT:
        # ML may detect an unusual combination even though no actual
        # network fault threshold has been exceeded.
        if ml_result.get("is_anomaly"):

            evidence.append(
                "The ML model noticed an unusual combination of metrics, "
                "but no specific network fault threshold was exceeded."
            )

    return evidence


# ---------------------------------------------------------------------------
# Top-level diagnosis pipeline
# ---------------------------------------------------------------------------

def run_diagnosis(
    metrics: dict,
    model=None,
) -> dict:
    """
    Complete NetGuard AI diagnosis pipeline:

    Network metrics
        ↓
    Isolation Forest
        ↓
    Rule evaluation
        ↓
    Diagnosis
        ↓
    Severity
        ↓
    Health score
        ↓
    Confidence
        ↓
    Explainability
    """

    # Load locally trained model if one was not supplied.
    model = model or ml_model.get_model()

    # Create the feature vector expected by Isolation Forest.
    feature_vector = {
        column: metrics.get(column, 0.0)
        for column in config.FEATURE_COLUMNS
    }

    # Run ML anomaly detection.
    ml_result = model.predict(
        feature_vector
    )

    # Run explainable threshold rules.
    rules = evaluate_rules(
        metrics
    )

    # Determine final network problem.
    diagnosis = determine_diagnosis(
        metrics,
        rules,
    )

    # Determine severity.
    severity = determine_severity(
        rules
    )

    # Calculate network health.
    health_score = compute_health_score(
        metrics
    )

    # Calculate confidence.
    confidence = compute_confidence(
        diagnosis,
        rules,
        ml_result,
    )

    # Build human-readable explanation.
    evidence = build_evidence(
        metrics,
        rules,
        diagnosis,
        ml_result,
    )

    # Return everything to app.py.
    return {
        "diagnosis": diagnosis,
        "severity": severity,
        "health_score": health_score,
        "confidence": confidence,
        "evidence": evidence,
        "is_anomaly": ml_result.get(
            "is_anomaly",
            False,
        ),
        "anomaly_strength": ml_result.get(
            "anomaly_strength",
            0.0,
        ),
        "raw_anomaly_score": ml_result.get(
            "raw_score",
            0.0,
        ),
        "model_available": ml_result.get(
            "model_available",
            True,
        ),
    }