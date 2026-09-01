"""
app.py
------
Detectra AI - Offline Intelligent Network Diagnostic Assistant
Modern cyber-network dashboard with interactive 3D topology.
"""

from datetime import datetime
from textwrap import dedent
import html

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

import config
import database
import diagnosis
import ml_model
import network_monitor
import troubleshooting


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# GLOBAL CYBER UI
# ============================================================

st.markdown(
    """
<style>

/* ==========================================================
   Detectra AI - DARK CYBER NETWORK THEME
   ========================================================== */

html,
body,
[class*="css"] {
    font-family: "Segoe UI", sans-serif;
}

/* STREAMLIT TOP HEADER */

[data-testid="stHeader"] {
    background: #031B29 !important;
}

[data-testid="stToolbar"] {
    background: #031B29 !important;
}

[data-testid="stDecoration"] {
    background: #031B29 !important;
}

header[data-testid="stHeader"] {
    background-color: #031B29 !important;
}
/* MAIN APP */

.stApp {
    background:
        radial-gradient(
            circle at 55% -15%,
            rgba(0, 185, 255, 0.11),
            transparent 35%
        ),
        radial-gradient(
            circle at 85% 30%,
            rgba(0, 255, 180, 0.035),
            transparent 25%
        ),
        linear-gradient(
            135deg,
            #020812 0%,
            #04101d 45%,
            #061827 100%
        );

    color: #e9f7ff;
}


.block-container {
    max-width: 1650px;
    padding-top: 1.1rem;
    padding-bottom: 3rem;
}


/* ==========================================================
   SIDEBAR
   ========================================================== */

[data-testid="stSidebar"] {

    background:
        linear-gradient(
            180deg,
            #020a13 0%,
            #03111e 55%,
            #020a13 100%
        );

    border-right:
        1px solid rgba(0, 205, 255, 0.16);
}


[data-testid="stSidebar"] * {
    color: #cceafa;
}


[data-testid="stSidebar"] hr {
    border-color:
        rgba(0, 205, 255, 0.12) !important;
}


/* Navigation */

[data-testid="stSidebar"]
[role="radiogroup"] label {

    padding: 8px 9px;
    margin: 2px 0;

    border-radius: 9px;

    transition:
        background 0.2s ease,
        transform 0.2s ease;
}


[data-testid="stSidebar"]
[role="radiogroup"] label:hover {

    background:
        rgba(0, 190, 255, 0.08);

    transform:
        translateX(3px);
}


/* ==========================================================
   METRIC CARDS
   ========================================================== */

[data-testid="stMetric"] {

    min-height: 126px;

    padding: 17px 18px;

    border-radius: 15px;

    background:
        linear-gradient(
            145deg,
            rgba(6, 27, 47, 0.98),
            rgba(3, 16, 29, 0.98)
        );

    border:
        1px solid rgba(0, 198, 255, 0.31);

    box-shadow:
        0 9px 26px rgba(0, 0, 0, 0.27),
        inset 0 0 22px rgba(0, 170, 255, 0.025);

    transition:
        transform 0.22s ease,
        border-color 0.22s ease,
        box-shadow 0.22s ease;

    transform-style:
        preserve-3d;
}


[data-testid="stMetric"]:hover {

    transform:
        perspective(700px)
        translateY(-5px)
        rotateX(3deg)
        rotateY(-2deg);

    border-color:
        rgba(0, 225, 255, 0.7);

    box-shadow:
        0 15px 34px rgba(0, 0, 0, 0.42),
        0 0 22px rgba(0, 190, 255, 0.08);
}


[data-testid="stMetricLabel"] {
    color: #9fc5d8;
}


[data-testid="stMetricValue"] {
    color: #f4fbff;
}


/* ==========================================================
   BUTTONS
   ========================================================== */

.stButton > button {

    min-height: 45px;
    width: 100%;

    border-radius: 10px;

    color: white;

    font-weight: 600;

    border:
        1px solid rgba(0, 205, 255, 0.50);

    background:
        linear-gradient(
            135deg,
            rgba(0, 164, 214, 0.29),
            rgba(0, 82, 140, 0.24)
        );

    box-shadow:
        inset 0 0 15px
        rgba(0, 190, 255, 0.04);

    transition:
        0.22s ease;
}


.stButton > button:hover {

    border-color: #15dcff;

    transform:
        translateY(-2px);

    box-shadow:
        0 0 20px
        rgba(0, 195, 255, 0.17);
}


/* ==========================================================
   INPUT
   ========================================================== */

.stTextInput input {

    background:
        #061827;

    color:
        #ffffff;

    border:
        1px solid
        rgba(0, 200, 255, 0.28);

    border-radius:
        10px;
}


/* ==========================================================
   GENERAL
   ========================================================== */

h1,
h2,
h3,
h4 {
    color: #eefaff;
}


hr {
    border-color:
        rgba(0, 200, 255, 0.10) !important;
}


[data-testid="stDataFrame"] {

    border:
        1px solid
        rgba(0, 200, 255, 0.18);

    border-radius:
        12px;

    overflow:
        hidden;
}


/* ==========================================================
   CUSTOM PANELS
   ========================================================== */

.net-panel {

    padding:
        17px 19px;

    margin-bottom:
        13px;

    border-radius:
        14px;

    background:
        linear-gradient(
            145deg,
            rgba(5, 26, 45, 0.97),
            rgba(3, 15, 28, 0.97)
        );

    border:
        1px solid
        rgba(0, 202, 255, 0.27);

    box-shadow:
        0 8px 24px
        rgba(0, 0, 0, 0.27);
}


.net-title {

    color:
        #17dfff;

    font-size:
        12px;

    font-weight:
        700;

    letter-spacing:
        0.8px;

    margin-bottom:
        9px;
}


.net-subtitle {

    color:
        #86aabd;

    font-size:
        14px;
}


.net-green {
    color: #24e990;
}


.net-yellow {
    color: #ffcf43;
}


.net-red {
    color: #ff5c6d;
}


/* ==========================================================
   DASHBOARD HEADER
   ========================================================== */

.netguard-main-title {

    font-size:
        34px;

    font-weight:
        700;

    color:
        #f3fbff;

    margin:
        0;
}


.netguard-subtitle {

    margin-top:
        1px;

    margin-bottom:
        15px;

    color:
        #8eafc1;

    font-size:
        14px;
}


/* ==========================================================
   STATUS PILLS
   ========================================================== */

.status-online {

    display:
        inline-block;

    color:
        #26ea91;

    padding:
        6px 12px;

    border-radius:
        20px;

    border:
        1px solid
        rgba(30, 230, 145, 0.23);

    background:
        rgba(30, 230, 145, 0.06);
}


.status-offline {

    display:
        inline-block;

    color:
        #ff5c6d;

    padding:
        6px 12px;

    border-radius:
        20px;

    border:
        1px solid
        rgba(255, 92, 109, 0.25);

    background:
        rgba(255, 92, 109, 0.06);
}


/* ==========================================================
   TOOL CARDS
   ========================================================== */

.tool-card {

    min-height:
        91px;

    padding:
        15px;

    border-radius:
        12px;

    background:
        linear-gradient(
            145deg,
            rgba(5, 26, 45, 0.96),
            rgba(3, 15, 28, 0.96)
        );

    border:
        1px solid
        rgba(0, 202, 255, 0.22);

    transition:
        0.2s ease;
}


.tool-card:hover {

    transform:
        translateY(-3px);

    border-color:
        rgba(0, 225, 255, 0.6);
}


/* ==========================================================
   PROGRESS
   ========================================================== */

.net-progress {

    width:
        100%;

    height:
        7px;

    background:
        #10293c;

    border-radius:
        20px;

    overflow:
        hidden;

    margin:
        8px 0;
}


.net-progress-fill {

    height:
        100%;

    border-radius:
        20px;

    background:
        linear-gradient(
            90deg,
            #12dfff,
            #20e98d
        );
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# STARTUP
# ============================================================

@st.cache_resource(show_spinner=False)
def _startup():

    db_ok = database.init_db()

    model = ml_model.get_model()

    return db_ok, model


db_ready, ml_model_instance = _startup()


# ============================================================
# SESSION STATE
# ============================================================

if "last_metrics" not in st.session_state:

    st.session_state.last_metrics = None


if "last_diagnosis" not in st.session_state:

    st.session_state.last_diagnosis = None


if "is_demo" not in st.session_state:

    st.session_state.is_demo = False


if "demo_scenario" not in st.session_state:

    st.session_state.demo_scenario = "Normal Network"


# ============================================================
# CORE DIAGNOSTIC ACTIONS
# ============================================================

def run_real_diagnostic():

    metrics = network_monitor.collect_metrics()

    result = diagnosis.run_diagnosis(
        metrics,
        model=ml_model_instance
    )

    database.insert_record(
        metrics,
        result
    )

    st.session_state.last_metrics = metrics

    st.session_state.last_diagnosis = result

    st.session_state.is_demo = False


def run_demo_diagnostic(scenario_name: str):

    sc = dict(
        config.DEMO_SCENARIOS[
            scenario_name
        ]
    )

    metrics = {

        "timestamp":
            datetime.now().isoformat(
                timespec="seconds"
            ),

        "source":
            "demo",

        "latency":
            float(
                sc.get(
                    "latency",
                    0
                )
            ),

        "packet_loss":
            float(
                sc.get(
                    "packet_loss",
                    0
                )
            ),

        "jitter":
            float(
                sc.get(
                    "jitter",
                    5
                )
            ),

        "network_usage":
            float(
                sc.get(
                    "network_usage",
                    0
                )
            ),

        "bytes_sent_rate":
            float(
                sc.get(
                    "bytes_sent_rate",
                    0
                )
            ),

        "bytes_recv_rate":
            float(
                sc.get(
                    "bytes_recv_rate",
                    0
                )
            ),

        "active_connections":
            int(
                sc.get(
                    "active_connections",
                    0
                )
            ),

        "cpu_usage":
            float(
                sc.get(
                    "cpu_usage",
                    0
                )
            ),

        "network_errors":
            int(
                sc.get(
                    "network_errors",
                    0
                )
            ),

        "connectivity_ok":
            bool(
                sc.get(
                    "connectivity_ok",
                    True
                )
            ),
    }


    result = diagnosis.run_diagnosis(
        metrics,
        model=ml_model_instance
    )


    database.insert_record(
        metrics,
        result
    )


    st.session_state.last_metrics = metrics

    st.session_state.last_diagnosis = result

    st.session_state.is_demo = True

    st.session_state.demo_scenario = scenario_name


# ============================================================
# SEVERITY
# ============================================================

SEVERITY_COLOR = {

    "Normal":
        "#22c55e",

    "Warning":
        "#eab308",

    "High":
        "#f97316",

    "Critical":
        "#ef4444",
}


def severity_badge(severity: str) -> str:

    color = SEVERITY_COLOR.get(
        severity,
        "#64748b"
    )

    return (
        f'<span style="'
        f'background-color:{color}22;'
        f'color:{color};'
        f'padding:4px 12px;'
        f'border-radius:12px;'
        f'font-weight:600;'
        f'border:1px solid {color}55;'
        f'">'
        f'{html.escape(str(severity))}'
        f'</span>'
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        f"## 🔍 {config.APP_TITLE}"
    )

    st.caption(
        config.APP_SUBTITLE
    )

    st.divider()


    page = st.radio(
        "Navigation",
        config.NAV_PAGES,
        label_visibility="collapsed"
    )


    st.divider()


    st.markdown(
        "### ⚙️ Data Source"
    )


    demo_on = st.toggle(
        "Demo Mode",
        value=
            st.session_state.is_demo,

        help=
            "Use realistic simulated scenarios instead of real local measurements."
    )


    if demo_on:

        scenarios = list(
            config.DEMO_SCENARIOS.keys()
        )


        current_demo = (
            st.session_state.demo_scenario
            if st.session_state.demo_scenario
            in scenarios
            else scenarios[0]
        )


        scenario = st.selectbox(
            "Scenario",
            scenarios,
            index=scenarios.index(
                current_demo
            )
        )


        if st.button(
            "▶ Run Demo Diagnostic",
            width="stretch",
            type="primary"
        ):

            with st.spinner(
                "Running ML anomaly detection and diagnostic rules..."
            ):

                run_demo_diagnostic(
                    scenario
                )

            st.rerun()


    else:

        if st.button(
            "▶ Run Real Diagnostic",
            width="stretch",
            type="primary"
        ):

            with st.spinner(
                "Collecting live network metrics..."
            ):

                run_real_diagnostic()

            st.rerun()


    st.divider()


    st.caption(
        f"Records stored: "
        f"{database.count_records()}"
    )


    st.caption(
        "🔒 100% offline — no cloud AI API."
    )


# ============================================================
# DEMO BANNER
# ============================================================

def demo_banner():

    if st.session_state.is_demo:

        st.warning(
            f"🎭 **DEMO / SIMULATED DATA** — "
            f"scenario: "
            f"*{st.session_state.demo_scenario}*. "
            f"Values pass through the real ML "
            f"+ diagnostic rules pipeline."
        )


# ============================================================
# 3D NETWORK TOPOLOGY
# IMPORTANT: THIS FUNCTION IS BEFORE page_dashboard()
# ============================================================

def render_network_topology(metrics, result):

    latency = float(metrics.get("latency", 0))
    health = float(result.get("health_score", 0))
    connected = bool(metrics.get("connectivity_ok", True))
    problem = str(result.get("diagnosis", "Unknown"))

    if connected:
        line_color = "#20e99b"
        status_text = (
            "ALL SYSTEMS NORMAL"
            if problem == "Network Healthy"
            else "ISSUE DETECTED"
        )
        status_color = (
            "#20e99b"
            if problem == "Network Healthy"
            else "#ffc83d"
        )
    else:
        line_color = "#ff5268"
        status_text = "CONNECTION FAILURE"
        status_color = "#ff5268"

    topology_html = """
    <div id="netguard-scene">

        <div class="scene-title">
            <span>NETWORK TOPOLOGY</span>

            <span
                class="scene-status"
                style="
                    color:__STATUS_COLOR__;
                    border-color:__STATUS_COLOR__55;
                "
            >
                ● __STATUS_TEXT__
            </span>
        </div>

        <div id="topology-layer" class="topology-layer">

            <div class="cyber-grid"></div>

            <svg
                class="network-lines"
                viewBox="0 0 900 390"
                preserveAspectRatio="none"
            >
                <line x1="450" y1="90" x2="195" y2="220" />
                <line x1="450" y1="90" x2="705" y2="220" />
                <line x1="195" y1="220" x2="450" y2="320" />
                <line x1="705" y1="220" x2="450" y2="320" />
                <line x1="450" y1="90" x2="450" y2="320" />
            </svg>

            <div class="node internet">
                <div class="orb">🌐</div>
                <strong>INTERNET</strong>
                <small>__LATENCY__ ms</small>
            </div>

            <div class="node router">
                <div class="orb">📡</div>
                <strong>ROUTER</strong>
                <small>Gateway</small>
            </div>

            <div class="node dns">
                <div class="orb">🗄️</div>
                <strong>DNS SERVER</strong>
                <small>Resolver</small>
            </div>

            <div class="node device">
                <div class="orb">💻</div>
                <strong>YOUR DEVICE</strong>
                <small>Health __HEALTH__/100</small>
            </div>

        </div>
    </div>

    <style>

    * {
        box-sizing: border-box;
    }

    html,
    body {
        margin: 0;
        padding: 0;
        overflow: hidden;
        background: transparent;
        font-family: "Segoe UI", sans-serif;
    }

    #netguard-scene {
        height: 400px;
        position: relative;
        overflow: hidden;
        border-radius: 15px;

        border:
            1px solid rgba(0, 205, 255, 0.33);

        background:
            radial-gradient(
                circle at 50% 43%,
                rgba(0, 160, 255, 0.16),
                transparent 28%
            ),
            radial-gradient(
                circle at 50% 100%,
                rgba(0, 220, 180, 0.055),
                transparent 35%
            ),
            linear-gradient(
                160deg,
                #041726,
                #020a13 72%
            );

        perspective: 900px;
    }

    .scene-title {
        position: absolute;
        z-index: 20;
        top: 14px;
        left: 17px;
        right: 17px;

        display: flex;
        align-items: center;
        justify-content: space-between;

        color: #18dcff;
        font-weight: 700;
        font-size: 12px;
        letter-spacing: 0.7px;
    }

    .scene-status {
        padding: 5px 9px;
        border: 1px solid;
        border-radius: 8px;
        background: rgba(0, 8, 16, 0.68);
        font-size: 10px;
    }

    .topology-layer {
        width: 100%;
        height: 100%;
        position: relative;
        transform-style: preserve-3d;
        transition: transform 0.13s ease-out;
    }

    .cyber-grid {
        position: absolute;
        width: 125%;
        height: 85%;
        left: -12.5%;
        top: 46%;
        opacity: 0.60;

        background-image:
            linear-gradient(
                rgba(0, 165, 255, 0.10) 1px,
                transparent 1px
            ),
            linear-gradient(
                90deg,
                rgba(0, 165, 255, 0.10) 1px,
                transparent 1px
            );

        background-size: 35px 35px;

        transform:
            perspective(300px)
            rotateX(64deg);

        transform-origin: center top;
    }

    .network-lines {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        z-index: 3;
    }

    .network-lines line {
        stroke: __LINE_COLOR__;
        stroke-width: 2;
        stroke-linecap: round;
        stroke-dasharray: 8 8;

        filter:
            drop-shadow(
                0 0 6px
                __LINE_COLOR__
            );

        animation:
            packet-flow
            1.1s
            linear
            infinite;
    }

    @keyframes packet-flow {
        from {
            stroke-dashoffset: 0;
        }

        to {
            stroke-dashoffset: -32;
        }
    }

    .node {
        position: absolute;
        width: 145px;
        z-index: 6;
        text-align: center;
        color: #e9faff;
        transform-style: preserve-3d;
    }

    .node strong {
        display: block;
        margin-top: 7px;
        color: #22dcff;
        font-size: 13px;
        font-weight: 700;

        text-shadow:
            0 0 8px
            rgba(0, 205, 255, 0.25);
    }

    .node small {
        display: block;
        margin-top: 2px;
        color: #8ebed2;
        font-size: 11px;
    }

    .orb {
        width: 68px;
        height: 68px;
        margin: auto;

        display: flex;
        align-items: center;
        justify-content: center;

        border-radius: 50%;
        font-size: 33px;

        background:
            radial-gradient(
                circle,
                rgba(0, 205, 255, 0.27),
                rgba(0, 55, 95, 0.11)
            );

        border:
            1px solid rgba(20, 220, 255, 0.65);

        box-shadow:
            0 0 12px rgba(0, 200, 255, 0.66),
            0 0 34px rgba(0, 120, 255, 0.22);

        animation:
            node-float
            3s
            ease-in-out
            infinite;
    }

    @keyframes node-float {
        0%,
        100% {
            transform: translateY(0);
        }

        50% {
            transform: translateY(-7px);
        }
    }

    .internet {
        left: calc(50% - 72px);
        top: 55px;
    }

    .router {
        left: 9%;
        top: 190px;
    }

    .dns {
        right: 9%;
        top: 190px;
    }

    .device {
        left: calc(50% - 72px);
        top: 275px;
    }

    @media (max-width: 650px) {

        .router {
            left: 1%;
        }

        .dns {
            right: 1%;
        }

        .node {
            width: 110px;
        }

        .orb {
            width: 58px;
            height: 58px;
            font-size: 28px;
        }
    }

    </style>

    <script>

    const scene =
        document.getElementById("netguard-scene");

    const layer =
        document.getElementById("topology-layer");

    if (scene && layer) {

        scene.addEventListener(
            "mousemove",
            function(event) {

                const rect =
                    scene.getBoundingClientRect();

                const x =
                    (
                        event.clientX -
                        rect.left
                    )
                    /
                    rect.width
                    -
                    0.5;

                const y =
                    (
                        event.clientY -
                        rect.top
                    )
                    /
                    rect.height
                    -
                    0.5;

                layer.style.transform =
                    "rotateY("
                    +
                    (x * 8)
                    +
                    "deg) rotateX("
                    +
                    (-y * 5)
                    +
                    "deg)";
            }
        );

        scene.addEventListener(
            "mouseleave",
            function() {

                layer.style.transform =
                    "rotateX(0deg) rotateY(0deg)";
            }
        );
    }

    </script>
    """

    topology_html = (
        topology_html
        .replace(
            "__STATUS_COLOR__",
            status_color
        )
        .replace(
            "__STATUS_TEXT__",
            status_text
        )
        .replace(
            "__LINE_COLOR__",
            line_color
        )
        .replace(
            "__LATENCY__",
            f"{latency:.0f}"
        )
        .replace(
            "__HEALTH__",
            f"{health:.0f}"
        )
    )

    components.html(
        topology_html,
        height=410,
        scrolling=False
    )


# ============================================================
# DASHBOARD
# ============================================================

def page_dashboard():

    metrics = st.session_state.last_metrics
    result = st.session_state.last_diagnosis

    # ========================================================
    # HEADER
    # ========================================================

    st.title("🔍 Detectra AI Dashboard")
    st.caption("Real-time intelligent network monitoring and diagnosis")

    demo_banner()

    if metrics is None or result is None:

        st.info(
            "👈 Run a Real Diagnostic or Demo Diagnostic "
            "from the sidebar to start monitoring."
        )

        return

    # ========================================================
    # VALUES
    # ========================================================

    latency = float(metrics.get("latency", 0))
    packet_loss = float(metrics.get("packet_loss", 0))
    usage = float(metrics.get("network_usage", 0))
    jitter = float(metrics.get("jitter", 0))
    health = float(result.get("health_score", 0))

    connected = bool(
        metrics.get("connectivity_ok", True)
    )

    diagnosis_name = result.get(
        "diagnosis",
        "Unknown"
    )

    severity = result.get(
        "severity",
        "Normal"
    )

    confidence = float(
        result.get("confidence", 0)
    )

    anomaly_strength = float(
        result.get("anomaly_strength", 0)
    )

    # ========================================================
    # CONNECTION STATUS
    # ========================================================

    status_col1, status_col2 = st.columns(
        [4, 1]
    )

    with status_col1:

        st.subheader(
            "Network Command Center"
        )

    with status_col2:

        if connected:
            st.success("● Connected")
        else:
            st.error("● Offline")

    # ========================================================
    # TOP METRICS
    # ========================================================

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric(
            "〰 Latency",
            f"{latency:.0f} ms"
        )

    with c2:
        st.metric(
            "◉ Packet Loss",
            f"{packet_loss:.1f}%"
        )

    with c3:
        st.metric(
            "◔ Network Usage",
            f"{usage:.0f}%"
        )

    with c4:
        st.metric(
            "〰 Jitter",
            f"{jitter:.0f} ms"
        )

    with c5:
        st.metric(
            "🛡 Health",
            f"{health:.0f}"
        )
        st.caption("/ 100")

    st.write("")

    # ========================================================
    # NETWORK TOPOLOGY + AI DIAGNOSIS
    # ========================================================

    topology_col, diagnosis_col = st.columns(
        [2.2, 1]
    )

    # -------------------------
    # 3D NETWORK TOPOLOGY
    # -------------------------

    with topology_col:

        render_network_topology(
            metrics,
            result
        )

    # -------------------------
    # AI DIAGNOSIS
    # -------------------------

    with diagnosis_col:

        st.subheader(
            "🤖 AI Diagnosis"
        )

        if diagnosis_name == "Network Healthy":

            st.success(
                f"✅ {diagnosis_name}"
            )

        elif severity == "Critical":

            st.error(
                f"🚨 {diagnosis_name}"
            )

        else:

            st.warning(
                f"⚠️ {diagnosis_name}"
            )

        d1, d2 = st.columns(2)

        with d1:

            st.metric(
                "Severity",
                severity
            )

        with d2:

            st.metric(
                "Confidence",
                f"{confidence:.1f}%"
            )

        st.caption(
            "Diagnosis Confidence"
        )

        st.progress(
            min(
                max(
                    confidence / 100,
                    0
                ),
                1
            )
        )

        st.metric(
            "ML Anomaly Strength",
            f"{anomaly_strength:.0f} / 100"
        )

        ml_signal = (
            "Unusual Pattern"
            if result.get(
                "is_anomaly",
                False
            )
            else
            "Normal Pattern"
        )

        st.metric(
            "ML Signal",
            ml_signal
        )

    # ========================================================
    # LIVE PERFORMANCE
    # ========================================================

    st.subheader(
        "📈 Live Network Performance"
    )

    history = database.fetch_history(
        limit=30
    )

    if not history.empty:

        history = history.sort_values(
            "timestamp"
        )

        live_fig = go.Figure()

        live_fig.add_trace(
            go.Scatter(
                x=history["timestamp"],
                y=history["latency"],
                mode="lines+markers",
                name="Latency",
                line=dict(
                    width=3
                ),
                marker=dict(
                    size=6
                )
            )
        )

        live_fig.update_layout(
            height=330,
            margin=dict(
                l=20,
                r=20,
                t=35,
                b=20
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(2,15,27,0.55)",
            font=dict(
                color="#b7d5e4"
            ),
            xaxis=dict(
                title="Time",
                gridcolor="rgba(100,180,220,0.10)"
            ),
            yaxis=dict(
                title="Latency (ms)",
                gridcolor="rgba(100,180,220,0.10)",
                rangemode="tozero"
            ),
            hovermode="x unified"
        )

        st.plotly_chart(
            live_fig,
            width="stretch",
            config={
                "displayModeBar": False
            }
        )

    else:

        st.info(
            "Run diagnostics to generate network history."
        )

    # ========================================================
    # ALERTS + EVIDENCE
    # ========================================================

    alert_col, evidence_col = st.columns(
        [1, 1.6]
    )

    with alert_col:

        st.subheader(
            "🔔 Active Alerts"
        )

        if diagnosis_name == "Network Healthy":

            st.success(
                "No active network alerts."
            )

            st.caption(
                "Your current network metrics "
                "are within normal fault thresholds."
            )

        else:

            st.warning(
                diagnosis_name
            )

            st.caption(
                f"Severity: {severity}"
            )

    with evidence_col:

        st.subheader(
            "🔍 Explainable Evidence"
        )

        evidence = result.get(
            "evidence",
            []
        )

        if evidence:

            for item in evidence[:6]:

                st.markdown(
                    f"✅ {item}"
                )

        else:

            st.info(
                "No abnormal evidence detected."
            )

    # ========================================================
    # SYSTEM INFORMATION
    # ========================================================

    st.subheader(
        "🖥 Network System Information"
    )

    s1, s2, s3, s4 = st.columns(4)

    with s1:

        st.metric(
            "Active Connections",
            metrics.get(
                "active_connections",
                0
            )
        )

    with s2:

        st.metric(
            "CPU Usage",
            f"{float(metrics.get('cpu_usage', 0)):.0f}%"
        )

    with s3:

        st.metric(
            "Network Errors",
            metrics.get(
                "network_errors",
                0
            )
        )

    with s4:

        source = metrics.get(
            "source",
            "real"
        )

        st.metric(
            "Data Source",
            str(source).title()
        )

    # ========================================================
    # NETWORK TOOLS
    # ========================================================

    st.subheader(
        "🧰 Network Tools"
    )

    t1, t2, t3, t4, t5 = st.columns(5)

    with t1:

        if st.button(
            "⚡ Speed Test",
            width="stretch",
            key="speed_test_dashboard"
        ):

            st.info(
                "Speed Test feature will be connected next."
            )

    with t2:

        if st.button(
            "🛡 Port Scanner",
            width="stretch",
            key="port_scanner_dashboard"
        ):

            st.info(
                "Port Scanner feature will be connected next."
            )

    with t3:

        if st.button(
            "📡 Ping Test",
            width="stretch",
            key="ping_test_dashboard"
        ):

            st.info(
                "Ping Test feature will be connected next."
            )

    with t4:

        if st.button(
            "🖥 System Info",
            width="stretch",
            key="system_info_dashboard"
        ):

            st.info(
                "System Information feature will be connected next."
            )

    with t5:

        if st.button(
            "⬇ Export Report",
            width="stretch",
            key="export_report_dashboard"
        ):

            st.info(
                "PDF diagnostic report will be connected next."
            )


# ============================================================
# AI DIAGNOSIS PAGE
# ============================================================

def page_ai_diagnosis():

    st.title(
        "🤖 AI Diagnosis"
    )


    demo_banner()


    result = (
        st.session_state.last_diagnosis
    )


    metrics = (
        st.session_state.last_metrics
    )


    if (
        result is None
        or metrics is None
    ):

        st.info(
            "👈 Run a diagnostic from the sidebar first."
        )

        return


    st.markdown(
        f"## "
        f"{result['diagnosis']} "
        f"— "
        f"{result['confidence']:.1f}% "
        f"confidence"
    )


    st.markdown(
        severity_badge(
            result[
                "severity"
            ]
        ),
        unsafe_allow_html=True
    )


    st.write("")


    c1, c2, c3 = (
        st.columns(3)
    )


    c1.metric(
        "Isolation Forest raw score",
        f"{result['raw_anomaly_score']:.4f}"
    )


    c2.metric(
        "Anomaly strength",
        f"{result['anomaly_strength']:.1f} / 100"
    )


    c3.metric(
        "ML Signal",
        (
            "Unusual Pattern"
            if result[
                "is_anomaly"
            ]
            else
            "Normal Pattern"
        )
    )


    st.divider()


    st.markdown(
        "### 🔍 Why was this detected?"
    )


    for evidence in (
        result[
            "evidence"
        ]
    ):

        st.markdown(
            f"- {evidence}"
        )


    with st.expander(
        "How is confidence calculated?"
    ):

        st.markdown(
            """
NetGuard combines two deterministic signals:

1. **Rule evidence strength — 60%**
2. **Isolation Forest ML agreement — 40%**

The score is capped at 99% so the system does not claim absolute certainty.
            """
        )


    st.divider()


    st.markdown(
        "### 📥 Raw feature vector fed to the model"
    )


    feat = {

        column:
            metrics.get(
                column
            )

        for column
        in config.FEATURE_COLUMNS
    }


    st.json(
        feat
    )


# ============================================================
# ANALYTICS
# ============================================================

def page_analytics():

    st.title(
        "📈 Network Analytics"
    )

    st.caption(
        "Visual analysis of recent network diagnostics"
    )

    df = database.fetch_history(
        limit=500
    )

    if df.empty:

        st.info(
            "No network history is available yet. "
            "Run some diagnostics first."
        )

        return

    # ========================================================
    # PREPARE DATA
    # ========================================================

    df = df.sort_values(
        "timestamp"
    )

    # Use recent diagnostics by default so old demo
    # spikes do not flatten the complete graph.
    recent_df = df.tail(40).copy()

    # ========================================================
    # SUMMARY
    # ========================================================

    a1, a2, a3, a4 = st.columns(4)

    with a1:

        st.metric(
            "Diagnostics",
            len(df)
        )

    with a2:

        st.metric(
            "Latest Latency",
            f"{float(recent_df.iloc[-1]['latency']):.0f} ms"
        )

    with a3:

        st.metric(
            "Latest Packet Loss",
            f"{float(recent_df.iloc[-1]['packet_loss']):.1f}%"
        )

    with a4:

        st.metric(
            "Latest Health Score",
            f"{float(recent_df.iloc[-1]['health_score']):.0f}/100"
        )

    st.divider()

    # ========================================================
    # ANALYTICS TABS
    # ========================================================

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "⚡ Latency",
            "📦 Packet Loss",
            "🌐 Network Usage",
            "🛡 Health Score"
        ]
    )

    # ========================================================
    # LATENCY
    # ========================================================

    with tab1:

        st.subheader(
            "Latency Trend"
        )

        fig_latency = go.Figure()

        fig_latency.add_trace(
            go.Scatter(
                x=recent_df["timestamp"],
                y=recent_df["latency"],
                mode="lines+markers",
                name="Latency",
                line=dict(
                    width=3
                ),
                marker=dict(
                    size=7
                ),
                fill="tozeroy",
                fillcolor="rgba(70,180,255,0.08)"
            )
        )

        fig_latency.add_hline(
            y=100,
            line_dash="dash",
            annotation_text="Warning 100 ms"
        )

        fig_latency.add_hline(
            y=200,
            line_dash="dash",
            annotation_text="High 200 ms"
        )

        fig_latency.update_layout(
            height=430,
            margin=dict(
                l=30,
                r=30,
                t=30,
                b=30
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(3,17,30,0.65)",
            font=dict(
                color="#c7deea"
            ),
            xaxis=dict(
                title="Diagnostic Time",
                gridcolor="rgba(120,180,210,0.10)"
            ),
            yaxis=dict(
                title="Latency (ms)",
                gridcolor="rgba(120,180,210,0.10)",
                rangemode="tozero"
            ),
            hovermode="x unified"
        )

        st.plotly_chart(
            fig_latency,
            width="stretch",
            config={
                "displayModeBar": False
            }
        )

    # ========================================================
    # PACKET LOSS
    # ========================================================

    with tab2:

        st.subheader(
            "Packet Loss Trend"
        )

        fig_loss = go.Figure()

        fig_loss.add_trace(
            go.Scatter(
                x=recent_df["timestamp"],
                y=recent_df["packet_loss"],
                mode="lines+markers",
                name="Packet Loss",
                line=dict(
                    width=3
                ),
                marker=dict(
                    size=7
                ),
                fill="tozeroy",
                fillcolor="rgba(255,120,100,0.08)"
            )
        )

        fig_loss.add_hline(
            y=5,
            line_dash="dash",
            annotation_text="Warning 5%"
        )

        fig_loss.add_hline(
            y=10,
            line_dash="dash",
            annotation_text="High 10%"
        )

        fig_loss.update_layout(
            height=430,
            margin=dict(
                l=30,
                r=30,
                t=30,
                b=30
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(3,17,30,0.65)",
            font=dict(
                color="#c7deea"
            ),
            xaxis=dict(
                title="Diagnostic Time",
                gridcolor="rgba(120,180,210,0.10)"
            ),
            yaxis=dict(
                title="Packet Loss (%)",
                gridcolor="rgba(120,180,210,0.10)",
                rangemode="tozero"
            ),
            hovermode="x unified"
        )

        st.plotly_chart(
            fig_loss,
            width="stretch",
            config={
                "displayModeBar": False
            }
        )

    # ========================================================
    # NETWORK USAGE
    # ========================================================

    with tab3:

        st.subheader(
            "Network Usage Trend"
        )

        fig_usage = go.Figure()

        fig_usage.add_trace(
            go.Scatter(
                x=recent_df["timestamp"],
                y=recent_df["network_usage"],
                mode="lines+markers",
                name="Network Usage",
                line=dict(
                    width=3
                ),
                marker=dict(
                    size=7
                ),
                fill="tozeroy",
                fillcolor="rgba(80,230,180,0.08)"
            )
        )

        fig_usage.update_layout(
            height=430,
            margin=dict(
                l=30,
                r=30,
                t=30,
                b=30
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(3,17,30,0.65)",
            font=dict(
                color="#c7deea"
            ),
            xaxis=dict(
                title="Diagnostic Time",
                gridcolor="rgba(120,180,210,0.10)"
            ),
            yaxis=dict(
                title="Network Usage (%)",
                range=[0, 100],
                gridcolor="rgba(120,180,210,0.10)"
            ),
            hovermode="x unified"
        )

        st.plotly_chart(
            fig_usage,
            width="stretch",
            config={
                "displayModeBar": False
            }
        )

    # ========================================================
    # HEALTH SCORE
    # ========================================================

    with tab4:

        st.subheader(
            "Network Health Score"
        )

        fig_health = go.Figure()

        fig_health.add_trace(
            go.Scatter(
                x=recent_df["timestamp"],
                y=recent_df["health_score"],
                mode="lines+markers",
                name="Health Score",
                line=dict(
                    width=3
                ),
                marker=dict(
                    size=7
                ),
                fill="tozeroy",
                fillcolor="rgba(60,240,160,0.08)"
            )
        )

        fig_health.update_layout(
            height=430,
            margin=dict(
                l=30,
                r=30,
                t=30,
                b=30
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(3,17,30,0.65)",
            font=dict(
                color="#c7deea"
            ),
            xaxis=dict(
                title="Diagnostic Time",
                gridcolor="rgba(120,180,210,0.10)"
            ),
            yaxis=dict(
                title="Health Score",
                range=[0, 100],
                gridcolor="rgba(120,180,210,0.10)"
            ),
            hovermode="x unified"
        )

        st.plotly_chart(
            fig_health,
            width="stretch",
            config={
                "displayModeBar": False
            }
        )

    # ========================================================
    # DIAGNOSIS DISTRIBUTION
    # ========================================================

    st.divider()

    st.subheader(
        "🧠 Detected Network Problems"
    )

    if "problem" in df.columns:

        problem_counts = (
            df["problem"]
            .value_counts()
            .reset_index()
        )

        problem_counts.columns = [
            "Problem",
            "Count"
        ]

        fig_problem = go.Figure(
            data=[
                go.Bar(
                    x=problem_counts["Problem"],
                    y=problem_counts["Count"]
                )
            ]
        )

        fig_problem.update_layout(
            height=380,
            margin=dict(
                l=30,
                r=30,
                t=25,
                b=30
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(3,17,30,0.65)",
            font=dict(
                color="#c7deea"
            ),
            xaxis=dict(
                title="Diagnosis"
            ),
            yaxis=dict(
                title="Number of Detections",
                rangemode="tozero"
            )
        )

        st.plotly_chart(
            fig_problem,
            width="stretch",
            config={
                "displayModeBar": False
            }
        )
# ============================================================
# TROUBLESHOOTING
# ============================================================

def page_troubleshooting():

    st.title(
        "🛠️ Troubleshooting"
    )


    st.caption(
        troubleshooting.DISCLAIMER
    )


    tab1, tab2 = (
        st.tabs(
            [
                "📚 Knowledge Base",
                "💬 Ask the Offline Assistant"
            ]
        )
    )


    with tab1:

        for (
            name,
            entry
        ) in (
            troubleshooting
            .KNOWLEDGE_BASE
            .items()
        ):

            with st.expander(
                f"**{name}**"
            ):

                st.markdown(
                    entry[
                        "description"
                    ]
                )


                st.markdown(
                    "**Possible causes:**"
                )


                for cause in (
                    entry[
                        "causes"
                    ]
                ):

                    st.markdown(
                        f"- {cause}"
                    )


                st.markdown(
                    "**Recommended actions:**"
                )


                for action in (
                    entry[
                        "actions"
                    ]
                ):

                    st.markdown(
                        f"- {action}"
                    )


    with tab2:

        st.markdown(
            """
Try asking:

*"What is wrong with my network?"*

*"Why is my network slow?"*

*"How can I reduce packet loss?"*

*"What does high latency mean?"*

*"How do I fix this problem?"*
            """
        )


        question = (
            st.text_input(
                "Ask a question"
            )
        )


        if st.button(
            "Ask",
            key="offline_assistant_ask"
        ):

            answer = (
                troubleshooting
                .answer_question(

                    question,

                    st.session_state
                    .last_diagnosis
                )
            )


            st.markdown(
                answer
            )


# ============================================================
# HISTORY
# ============================================================

def page_history():

    st.title(
        "🕓 History"
    )


    df = (
        database.fetch_history(
            limit=500
        )
    )


    if df.empty:

        st.info(
            "No diagnostic history yet."
        )

        return


    available_columns = [

        "timestamp",

        "source",

        "latency",

        "packet_loss",

        "network_usage",

        "active_connections",

        "cpu_usage",

        "network_errors",

        "problem",

        "severity",

        "confidence",

        "health_score",

        "is_anomaly"
    ]


    available_columns = [

        column

        for column
        in available_columns

        if column
        in df.columns
    ]


    st.dataframe(

        df[
            available_columns
        ].sort_values(

            "timestamp",

            ascending=False
        ),

        width="stretch",

        height=500
    )


    left, right = (
        st.columns(
            [
                1,
                4
            ]
        )
    )


    with left:

        if st.button(
            "🗑️ Clear History"
        ):

            database.clear_history()

            st.rerun()


# ============================================================
# ABOUT
# ============================================================

def page_about():

    st.title(
        "ℹ️ About & Privacy"
    )


    st.markdown(
        f"### "
        f"{config.APP_TITLE} "
        f"— "
        f"{config.APP_SUBTITLE}"
    )


    st.markdown(
        f"""
Detectra AI is a fully offline intelligent network diagnostic
assistant developed for a college hackathon.

It combines **Isolation Forest anomaly detection** with
**explainable threshold-based diagnostic rules**.

### 🔒 Privacy

- Network metrics are collected locally.
- Isolation Forest runs locally through scikit-learn.
- Diagnostic history is stored in local SQLite.
- No OpenAI, Gemini, or other cloud AI API is required.
- Network telemetry does not need to leave the device.

### 🧠 How Detectra AI Works

1. Collects latency, packet loss, network usage, connections,
   CPU usage, jitter and errors.
2. Isolation Forest checks for unusual metric combinations.
3. Explainable rules determine the probable network problem.
4. The application displays severity, confidence and evidence.
5. The offline knowledge base recommends troubleshooting steps.
6. Diagnostic history is stored and visualized.

### ⚠️ Limitations

- Ping measurements depend on the reference host.
- Network usage is estimated using an assumed bandwidth of
  **{config.ASSUMED_BANDWIDTH_MBPS} Mbps**.
- Isolation Forest currently uses representative synthetic
  normal-network training data.
        """
    )


# ============================================================
# PAGE ROUTER
# ============================================================

PAGES = {

    "Dashboard":
        page_dashboard,

    "AI Diagnosis":
        page_ai_diagnosis,

    "Analytics":
        page_analytics,

    "Troubleshooting":
        page_troubleshooting,

    "History":
        page_history,

    "About":
        page_about,
}


PAGES[page]()