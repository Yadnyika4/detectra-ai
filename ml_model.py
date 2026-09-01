"""
ml_model.py
-----------
Isolation Forest based anomaly detector for network telemetry.

Responsibilities:
  * Generate realistic synthetic "normal network" training data so the
    project works immediately on a fresh clone (no external dataset needed).
  * Train a scikit-learn IsolationForest + StandardScaler pipeline.
  * Persist both with joblib and reload them on subsequent runs.
  * Score new feature vectors -> (is_anomaly, raw_score, anomaly_strength_0_100)

No randomness is used at *inference* time - predictions are a deterministic
function of the trained model and the input features. Randomness is only
used once, offline, to build the synthetic training set.
"""

import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

import config


# ---------------------------------------------------------------------------
# Synthetic training data generation
# ---------------------------------------------------------------------------
def generate_synthetic_training_data(n_samples: int = None, save: bool = True) -> pd.DataFrame:
    """Create a realistic synthetic dataset of *mostly normal* home/office
    network behaviour, with a small fraction of mild outliers, so the
    Isolation Forest has a sensible notion of "normal" to compare against.

    Feature ranges are based on typical broadband/Wi-Fi conditions:
      latency: 5-60ms typical, occasional spikes
      packet_loss: usually 0-1%, rare spikes
      network_usage: 5-40% typical utilization
      active_connections: 5-60 typical
      cpu_usage: 5-40% typical
      network_errors: usually 0, rare small counts
    """
    n_samples = n_samples or config.N_SYNTHETIC_SAMPLES
    rng = np.random.default_rng(config.RANDOM_STATE)

    n_normal = int(n_samples * (1 - config.CONTAMINATION))
    n_outliers = n_samples - n_normal

    # --- normal traffic ---
    latency = np.clip(rng.normal(25, 10, n_normal), 2, 90)
    packet_loss = np.clip(rng.exponential(0.4, n_normal), 0, 5)
    network_usage = np.clip(rng.normal(22, 12, n_normal), 0, 65)
    active_connections = np.clip(rng.normal(28, 12, n_normal), 1, 90).round()
    cpu_usage = np.clip(rng.normal(20, 10, n_normal), 1, 70)
    network_errors = rng.poisson(0.3, n_normal)

    normal_df = pd.DataFrame({
        "latency": latency,
        "packet_loss": packet_loss,
        "network_usage": network_usage,
        "active_connections": active_connections,
        "cpu_usage": cpu_usage,
        "network_errors": network_errors,
    })

    # --- mild/extreme outliers: congestion, latency spikes, packet loss,
    #     connection failures, error bursts - so the forest has *some*
    #     exposure to abnormal shapes during training (small fraction only) ---
    outlier_rows = []
    for _ in range(n_outliers):
        kind = rng.choice(["latency", "loss", "congestion", "failure", "errors"])
        if kind == "latency":
            row = dict(latency=rng.uniform(180, 400), packet_loss=rng.uniform(0, 3),
                       network_usage=rng.uniform(10, 40), active_connections=rng.uniform(10, 50),
                       cpu_usage=rng.uniform(10, 40), network_errors=rng.poisson(1))
        elif kind == "loss":
            row = dict(latency=rng.uniform(30, 100), packet_loss=rng.uniform(8, 30),
                       network_usage=rng.uniform(10, 40), active_connections=rng.uniform(10, 50),
                       cpu_usage=rng.uniform(10, 40), network_errors=rng.poisson(4))
        elif kind == "congestion":
            row = dict(latency=rng.uniform(120, 260), packet_loss=rng.uniform(3, 10),
                       network_usage=rng.uniform(85, 100), active_connections=rng.uniform(100, 200),
                       cpu_usage=rng.uniform(40, 80), network_errors=rng.poisson(2))
        elif kind == "failure":
            row = dict(latency=rng.uniform(500, 1000), packet_loss=rng.uniform(60, 100),
                       network_usage=rng.uniform(0, 5), active_connections=rng.uniform(0, 5),
                       cpu_usage=rng.uniform(5, 30), network_errors=rng.poisson(20))
        else:  # errors
            row = dict(latency=rng.uniform(20, 80), packet_loss=rng.uniform(1, 6),
                       network_usage=rng.uniform(10, 50), active_connections=rng.uniform(10, 60),
                       cpu_usage=rng.uniform(10, 50), network_errors=rng.poisson(25))
        outlier_rows.append(row)

    outlier_df = pd.DataFrame(outlier_rows)

    full_df = pd.concat([normal_df, outlier_df], ignore_index=True)
    full_df = full_df.sample(frac=1.0, random_state=config.RANDOM_STATE).reset_index(drop=True)
    full_df = full_df[config.FEATURE_COLUMNS]

    if save:
        full_df.to_csv(config.TRAINING_DATA_PATH, index=False)

    return full_df


# ---------------------------------------------------------------------------
# Model wrapper
# ---------------------------------------------------------------------------
class detectraMLModel:
    """Wraps a StandardScaler + IsolationForest pair with train/save/load/predict."""

    def __init__(self):
        self.scaler: StandardScaler | None = None
        self.model: IsolationForest | None = None
        self._score_min = None
        self._score_max = None

    # -- training ------------------------------------------------------
    def train(self, df: pd.DataFrame = None):
        if df is None:
            if os.path.exists(config.TRAINING_DATA_PATH):
                df = pd.read_csv(config.TRAINING_DATA_PATH)
            else:
                df = generate_synthetic_training_data()

        X = df[config.FEATURE_COLUMNS].values

        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        self.model = IsolationForest(
            n_estimators=config.N_ESTIMATORS,
            contamination=config.CONTAMINATION,
            random_state=config.RANDOM_STATE,
        )
        self.model.fit(X_scaled)

        # Cache the training score distribution so we can normalize any
        # future decision_function() score into a stable 0-100 range.
        raw_scores = self.model.decision_function(X_scaled)
        self._score_min = float(np.percentile(raw_scores, 1))
        self._score_max = float(np.percentile(raw_scores, 99))

        return self

    # -- persistence -----------------------------------------------------
    def save(self):
        joblib.dump(self.model, config.MODEL_PATH)
        joblib.dump(
            {"scaler": self.scaler, "score_min": self._score_min, "score_max": self._score_max},
            config.SCALER_PATH,
        )

    def load(self) -> bool:
        """Load a previously trained model. Returns True on success, False
        if no saved model exists or loading fails (caller should retrain)."""
        try:
            if not (os.path.exists(config.MODEL_PATH) and os.path.exists(config.SCALER_PATH)):
                return False
            self.model = joblib.load(config.MODEL_PATH)
            meta = joblib.load(config.SCALER_PATH)
            self.scaler = meta["scaler"]
            self._score_min = meta["score_min"]
            self._score_max = meta["score_max"]
            return True
        except Exception:
            self.model = None
            self.scaler = None
            return False

    def load_or_train(self):
        """Convenience: load if possible, otherwise generate data, train and save."""
        if not self.load():
            df = generate_synthetic_training_data()
            self.train(df)
            self.save()
        return self

    # -- inference ---------------------------------------------------------
    def predict(self, features: dict) -> dict:
        """features: dict with keys matching config.FEATURE_COLUMNS (missing
        keys default to 0). Returns is_anomaly, raw_score, anomaly_strength."""
        if self.model is None or self.scaler is None:
            # Model unavailable for any reason -> fail safe, do not crash the
            # dashboard. Caller/diagnosis layer will rely on rules alone.
            return {
                "is_anomaly": False,
                "raw_score": 0.0,
                "anomaly_strength": 0.0,
                "model_available": False,
            }

        vector = np.array([[float(features.get(col, 0.0)) for col in config.FEATURE_COLUMNS]])
        vector_scaled = self.scaler.transform(vector)

        raw_score = float(self.model.decision_function(vector_scaled)[0])
        prediction = int(self.model.predict(vector_scaled)[0])  # 1 = normal, -1 = anomaly
        is_anomaly = prediction == -1

        # Normalize: lower decision_function => more anomalous. Map the
        # cached [score_min, score_max] training range onto [100, 0].
        if self._score_max is not None and self._score_min is not None and self._score_max > self._score_min:
            normalized = (raw_score - self._score_min) / (self._score_max - self._score_min)
            normalized = min(max(normalized, 0.0), 1.0)
            anomaly_strength = round((1.0 - normalized) * 100, 1)
        else:
            anomaly_strength = 100.0 if is_anomaly else 0.0

        return {
            "is_anomaly": is_anomaly,
            "raw_score": round(raw_score, 4),
            "anomaly_strength": anomaly_strength,
            "model_available": True,
        }


# ---------------------------------------------------------------------------
# Module-level convenience singleton (lazy)
# ---------------------------------------------------------------------------
_singleton_model = None


def get_model() -> detectraMLModel:
    """Return a process-wide cached, trained/loaded model instance."""
    global _singleton_model
    if _singleton_model is None:
        _singleton_model = detectraMLModel()
        _singleton_model.load_or_train()
    return _singleton_model
