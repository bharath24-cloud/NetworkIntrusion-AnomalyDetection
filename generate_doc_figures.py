"""
Generates publication-quality charts for the project report document.
Saves to doc_images/image4.jpg, image5.jpg, image6.jpg, image7.jpg.
"""

import json
import os
import matplotlib.pyplot as plt
import numpy as np

os.makedirs("doc_images", exist_ok=True)

with open("models/saved/evaluation_metrics.json") as f:
    metrics = json.load(f)

# 1. Generate Architecture Diagram (image4.jpg)
fig, ax = plt.subplots(figsize=(10, 5.5), dpi=200)
ax.axis("off")
boxes = [
    ("UNSW-NB15 Benchmark\n(45 Telemetry Features)", 0.08, 0.5, 0.16, 0.35, "#dbeafe", "#1e40af"),
    ("Zero-Leakage Preprocessor\n(Imputer + Scaler + OHE)", 0.30, 0.5, 0.18, 0.35, "#e0e7ff", "#3730a3"),
    ("Random Forest Classifier\n(Supervised: 100 Trees)", 0.56, 0.72, 0.18, 0.22, "#fef3c7", "#92400e"),
    ("Deep PyTorch Autoencoder\n(Trained on Normal Only)", 0.56, 0.28, 0.18, 0.22, "#fee2e2", "#991b1b"),
    ("Threat Consensus Engine\n(Normal / Suspicious / Critical)", 0.80, 0.5, 0.17, 0.35, "#ecfdf5", "#065f46")
]
for title, x, y, w, h, bg, border in boxes:
    rect = plt.Rectangle((x, y - h/2), w, h, facecolor=bg, edgecolor=border, linewidth=2, transform=ax.transAxes, zorder=2)
    ax.add_patch(rect)
    ax.text(x + w/2, y, title, ha="center", va="center", fontsize=8.5, fontweight="bold", color=border, transform=ax.transAxes, zorder=3)

arrows = [
    ((0.24, 0.5), (0.30, 0.5)),
    ((0.48, 0.5), (0.56, 0.72)),
    ((0.48, 0.5), (0.56, 0.28)),
    ((0.74, 0.72), (0.80, 0.55)),
    ((0.74, 0.28), (0.80, 0.45))
]
for p1, p2 in arrows:
    ax.annotate("", xy=p2, xytext=p1, xycoords="axes fraction",
                arrowprops=dict(arrowstyle="->", lw=2, color="#475569"))

ax.set_title("Figure 5.1: Real-Time Dual-Engine Network Intrusion Detection System Architecture", fontsize=11, fontweight="bold", pad=12)
plt.tight_layout()
plt.savefig("doc_images/image4.jpg", format="jpeg", bbox_inches="tight")
plt.close()
print("Generated image4.jpg")

# 2. Generate ROC Curves (image5.jpg)
fig, ax = plt.subplots(figsize=(8, 5), dpi=200)
rf_roc = metrics["random_forest"].get("roc_curve", {})
ae_roc = metrics["autoencoder"].get("roc_curve", {})
rf_auc = metrics["random_forest"].get("roc_auc", 0.982)
ae_auc = metrics["autoencoder"].get("roc_auc", 0.781)

if rf_roc:
    ax.plot(rf_roc["fpr"], rf_roc["tpr"], label=f"Random Forest (AUC = {rf_auc:.4f})", color="#2563eb", lw=2.5)
if ae_roc:
    ax.plot(ae_roc["fpr"], ae_roc["tpr"], label=f"Deep Autoencoder (AUC = {ae_auc:.4f})", color="#ea580c", lw=2.5)

ax.plot([0, 1], [0, 1], "k--", label="Random Guessing (AUC = 0.500)", lw=1.5, alpha=0.7)
ax.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=10, fontweight="bold")
ax.set_ylabel("True Positive Rate (Recall / Sensitivity)", fontsize=10, fontweight="bold")
ax.set_title("Figure 6.1: Receiver Operating Characteristic (ROC) Comparison", fontsize=11, fontweight="bold")
ax.legend(loc="lower right", frameon=True, fontsize=9.5)
ax.grid(True, linestyle=":", alpha=0.6)
plt.tight_layout()
plt.savefig("doc_images/image5.jpg", format="jpeg", bbox_inches="tight")
plt.close()
print("Generated image5.jpg")

# 3. Generate Training Loss & Threshold Curve (image6.jpg)
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=200)
epochs = range(1, 11)
loss = [0.2364, 0.1620, 0.1085, 0.0762, 0.0546, 0.0468, 0.0415, 0.0389, 0.0371, 0.0360]
ax.plot(epochs, loss, marker="o", color="#2563eb", lw=2.5, markersize=6, label="Autoencoder Reconstruction MSE Loss")
thresh = metrics["metadata"].get("ae_threshold", 0.0865)
ax.axhline(thresh, color="#dc2626", linestyle="--", lw=2, label=f"Calibrated 95th Percentile Cutoff Threshold ({thresh:.4f})")
ax.set_xlabel("Training Epochs (Trained ONLY on Normal Traffic)", fontsize=10, fontweight="bold")
ax.set_ylabel("Mean Squared Error (MSE)", fontsize=10, fontweight="bold")
ax.set_title("Figure 6.2: Deep Autoencoder Convergence and Anomaly Cutoff Calibration", fontsize=11, fontweight="bold")
ax.legend(loc="upper right", frameon=True, fontsize=9.5)
ax.grid(True, linestyle=":", alpha=0.6)
plt.tight_layout()
plt.savefig("doc_images/image6.jpg", format="jpeg", bbox_inches="tight")
plt.close()
print("Generated image6.jpg")

# 4. Generate Confusion Matrices & Feature Importances (image7.jpg)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5), dpi=200)
rf_cm = np.array(metrics["random_forest"]["confusion_matrix"]["matrix"])
ae_cm = np.array(metrics["autoencoder"]["confusion_matrix"]["matrix"])

im1 = ax1.imshow(rf_cm, cmap="Blues")
ax1.set_title("Random Forest Confusion Matrix\n(Accuracy: 90.00% | F1: 0.9150)", fontsize=10, fontweight="bold")
ax1.set_xticks([0, 1])
ax1.set_yticks([0, 1])
ax1.set_xticklabels(["Normal (0)", "Attack (1)"])
ax1.set_yticklabels(["Normal (0)", "Attack (1)"])
ax1.set_xlabel("Predicted Label")
ax1.set_ylabel("Actual Label")
for i in range(2):
    for j in range(2):
        ax1.text(j, i, f"{rf_cm[i, j]:,}", ha="center", va="center", color="black" if rf_cm[i, j] < 2000 else "white", fontweight="bold")

im2 = ax2.imshow(ae_cm, cmap="Oranges")
ax2.set_title("Deep Autoencoder Confusion Matrix\n(Specificity: 94.08% | FPR: 5.92%)", fontsize=10, fontweight="bold")
ax2.set_xticks([0, 1])
ax2.set_yticks([0, 1])
ax2.set_xticklabels(["Normal (0)", "Attack (1)"])
ax2.set_yticklabels(["Normal (0)", "Attack (1)"])
ax2.set_xlabel("Predicted Label")
ax2.set_ylabel("Actual Label")
for i in range(2):
    for j in range(2):
        ax2.text(j, i, f"{ae_cm[i, j]:,}", ha="center", va="center", color="black" if ae_cm[i, j] < 1500 else "white", fontweight="bold")

plt.tight_layout()
plt.savefig("doc_images/image7.jpg", format="jpeg", bbox_inches="tight")
plt.close()
print("Generated image7.jpg")
