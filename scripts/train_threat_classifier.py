from __future__ import annotations
import os
import sys
import json
import pickle
sys.path.insert(0, ".")

os.environ.setdefault("DATABASE_URL", "postgresql://cybermind_db_user:rcTm7NNlUz1QT4QQXyMB0PR4Qb5xI0bu@dpg-d79t91ma2pns73ea0m7g-a.oregon-postgres.render.com/cybermind_db")

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.preprocessing import LabelEncoder
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from src.backend.database.db_models import CveDB
from src.backend.database.engine import SessionLocal

print("Loading CVE data from PostgreSQL...")
db = SessionLocal()
cves = db.query(CveDB).filter(CveDB.cvss_severity != None).all()
db.close()
print(f"Loaded {len(cves)} CVEs")

# Build feature matrix
records = []
for cve in cves:
    desc = (cve.description or "").lower()
    records.append({
        "cvss_score": cve.cvss_score or 0.0,
        "risk_score": cve.risk_score or 0.0,
        "has_rce": int("remote code execution" in desc or "rce" in desc),
        "has_sqli": int("sql injection" in desc),
        "has_overflow": int("buffer overflow" in desc or "overflow" in desc),
        "has_privesc": int("privilege escalation" in desc),
        "has_ransomware": int("ransomware" in desc),
        "has_auth_bypass": int("authentication bypass" in desc or "auth bypass" in desc),
        "has_xss": int("cross-site scripting" in desc or "xss" in desc),
        "desc_length": len(desc),
        "num_cwe": len(cve.cwe_ids or []),
        "num_mitre": len(cve.mitre_techniques or []),
        "severity": cve.cvss_severity,
    })

df = pd.DataFrame(records)
# Merge LOW into MEDIUM due to insufficient samples
df['severity'] = df['severity'].replace('LOW', 'MEDIUM')
print(f"Class distribution:\n{df['severity'].value_counts()}")


# Features and target
feature_cols = [c for c in df.columns if c != "severity"]
X = df[feature_cols].values
le = LabelEncoder()
y = le.fit_transform(df["severity"])

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

print("\nTraining Gradient Boosting Classifier...")
clf = GradientBoostingClassifier(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
clf.fit(X_train, y_train)

# Evaluate
y_pred = clf.predict(X_test)
y_prob = clf.predict_proba(X_test)

print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=le.classes_))

# AUC
if len(le.classes_) == 2:
    auc = roc_auc_score(y_test, y_prob[:, 1])
else:
    auc = roc_auc_score(y_test, y_prob, multi_class="ovr", average="weighted")
print(f"AUC (weighted OvR): {auc:.4f}")

# Cross validation
cv_scores = cross_val_score(clf, X, y, cv=5, scoring="f1_weighted")
print(f"5-Fold CV F1: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

# Confusion matrix
os.makedirs("data/gold/models", exist_ok=True)
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=le.classes_, yticklabels=le.classes_)
plt.title("CyberMind Threat Severity Classifier\nConfusion Matrix")
plt.ylabel("Actual")
plt.xlabel("Predicted")
plt.tight_layout()
plt.savefig("data/gold/models/confusion_matrix.png", dpi=150)
print("Confusion matrix saved!")

# Feature importance
fi = pd.DataFrame({"feature": feature_cols, "importance": clf.feature_importances_})
fi = fi.sort_values("importance", ascending=False)
plt.figure(figsize=(10, 6))
sns.barplot(data=fi, x="importance", y="feature", palette="Blues_r")
plt.title("Feature Importance — Threat Severity Classifier")
plt.tight_layout()
plt.savefig("data/gold/models/feature_importance.png", dpi=150)
print("Feature importance saved!")

# Save model
model_data = {
    "model": clf,
    "label_encoder": le,
    "feature_cols": feature_cols,
    "auc": auc,
    "cv_f1_mean": cv_scores.mean(),
    "cv_f1_std": cv_scores.std(),
    "classes": list(le.classes_),
    "num_training_samples": len(X_train),
}
with open("data/gold/models/threat_classifier.pkl", "wb") as f:
    pickle.dump(model_data, f)
print(f"\nModel saved! AUC={auc:.4f}")
print("Done!")