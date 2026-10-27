/**
 * Dataset Replay Simulation Controller
 * Orchestrates batched stream replay requests to the Flask backend with configurable delay.
 * Replays UNSW-NB15 holdout test records to simulate a real-time SOC intrusion monitor.
 */

class DatasetReplayManager {
    constructor() {
        this.currentIndex = 0;
        this.batchSize = 1;
        this.delayMs = 500;
        this.isRunning = false;
        this.timer = null;
        
        // Counters
        this.totalProcessed = 0;
        this.normalCount = 0;
        this.attackCount = 0;
        this.criticalCount = 0;
        
        // History buffer for timeline chart
        this.chartHistory = [];
        this.maxChartPoints = 40;
        this.timelineChart = null;

        // Autoencoder cutoff threshold (injected from template or default)
        this.aeThreshold = window.AE_THRESHOLD || 0.0865;

        this.initElements();
        this.initEvents();
        this.initChart();
    }

    initElements() {
        this.btnStart = document.getElementById("btn-start-replay");
        this.btnPause = document.getElementById("btn-pause-replay");
        this.btnReset = document.getElementById("btn-reset-replay");
        this.btnStep = document.getElementById("btn-step-replay");
        
        this.sliderDelay = document.getElementById("slider-delay");
        this.valDelay = document.getElementById("val-delay");
        this.selectBatch = document.getElementById("select-batch-size");
        
        this.lblProcessed = document.getElementById("lbl-processed");
        this.lblNormal = document.getElementById("lbl-normal");
        this.lblAttack = document.getElementById("lbl-attack");
        this.lblCritical = document.getElementById("lbl-critical");
        this.lblRate = document.getElementById("lbl-rate");
        
        this.tableBody = document.getElementById("replay-feed-body");
        this.statusIndicator = document.getElementById("status-indicator");
        this.statusText = document.getElementById("status-text");
    }

    initEvents() {
        if (!this.btnStart) return;

        this.btnStart.addEventListener("click", () => this.start());
        this.btnPause.addEventListener("click", () => this.pause());
        this.btnReset.addEventListener("click", () => this.reset());
        this.btnStep.addEventListener("click", () => this.step());

        this.sliderDelay.addEventListener("input", (e) => {
            this.delayMs = parseInt(e.target.value);
            this.valDelay.textContent = `${this.delayMs} ms`;
            if (this.isRunning) {
                // Restart timer with new delay
                clearInterval(this.timer);
                this.timer = setInterval(() => this.step(), this.delayMs);
            }
        });

        this.selectBatch.addEventListener("change", (e) => {
            this.batchSize = parseInt(e.target.value);
        });
    }

    initChart() {
        const ctx = document.getElementById("timelineChart");
        if (!ctx) return;

        this.timelineChart = new Chart(ctx, {
            type: "line",
            data: {
                labels: [],
                datasets: [
                    {
                        label: "Autoencoder Reconstruction MSE",
                        data: [],
                        borderColor: "#2563eb",
                        backgroundColor: "rgba(37, 99, 235, 0.1)",
                        borderWidth: 2,
                        tension: 0.2,
                        pointRadius: 3,
                        pointBackgroundColor: "#2563eb",
                        fill: true
                    },
                    {
                        label: `Anomaly Cutoff (${this.aeThreshold.toFixed(4)})`,
                        data: [],
                        borderColor: "#ef4444",
                        borderDash: [5, 5],
                        borderWidth: 2,
                        pointRadius: 0,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: { display: true, text: "Packet / Flow Sequence #" },
                        grid: { display: false }
                    },
                    y: {
                        title: { display: true, text: "Reconstruction Error (MSE)" },
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: { position: "top" }
                }
            }
        });
    }

    start() {
        if (this.isRunning) return;
        this.isRunning = true;
        this.updateStatus(true);
        this.timer = setInterval(() => this.step(), this.delayMs);
    }

    pause() {
        if (!this.isRunning) return;
        this.isRunning = false;
        clearInterval(this.timer);
        this.updateStatus(false);
    }

    reset() {
        this.pause();
        this.currentIndex = 0;
        this.totalProcessed = 0;
        this.normalCount = 0;
        this.attackCount = 0;
        this.criticalCount = 0;
        this.chartHistory = [];

        this.updateKPIs();
        if (this.tableBody) this.tableBody.innerHTML = "";
        if (this.timelineChart) {
            this.timelineChart.data.labels = [];
            this.timelineChart.data.datasets[0].data = [];
            this.timelineChart.data.datasets[1].data = [];
            this.timelineChart.update();
        }
        this.updateStatus(false, "Replay Reset to Beginning");
    }

    updateStatus(running, text = null) {
        if (!this.statusIndicator) return;
        if (running) {
            this.statusIndicator.className = "pulse-dot";
            this.statusText.textContent = text || `Streaming replay active (${this.delayMs}ms delay)...`;
            this.btnStart.disabled = true;
            this.btnPause.disabled = false;
        } else {
            this.statusIndicator.className = "pulse-dot paused";
            this.statusText.textContent = text || "Replay paused";
            this.btnStart.disabled = false;
            this.btnPause.disabled = true;
        }
    }

    async step() {
        try {
            const resp = await fetch("/api/replay/next", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    current_index: this.currentIndex,
                    batch_size: this.batchSize
                })
            });

            if (!resp.ok) {
                const err = await resp.json();
                console.error("Replay fetch error:", err);
                this.pause();
                this.updateStatus(false, `Error: ${err.error || "Failed to fetch batch"}`);
                return;
            }

            const data = await resp.json();
            if (data.records && data.records.length > 0) {
                this.processIncomingRecords(data.records);
                this.currentIndex = data.next_index;
            }

            if (data.is_end) {
                this.pause();
                this.updateStatus(false, "Reached End of Holdout Test Dataset");
            }
        } catch (e) {
            console.error("Network error during replay step:", e);
            this.pause();
            this.updateStatus(false, "Network communication error");
        }
    }

    processIncomingRecords(records) {
        records.forEach((record) => {
            this.totalProcessed++;
            if (record.rf_pred === 1) {
                this.attackCount++;
            } else {
                this.normalCount++;
            }

            if (record.rf_pred === 1 && record.ae_pred === 1) {
                this.criticalCount++;
            }

            // Append row to table (newest at top)
            this.appendTableRow(record);

            // Update Chart Data
            this.appendChartPoint(record);
        });

        this.updateKPIs();
        if (this.timelineChart) {
            this.timelineChart.update("none"); // update without sluggish animation
        }
    }

    appendTableRow(r) {
        if (!this.tableBody) return;

        const tr = document.createElement("tr");
        let badgeHtml = "";
        if (r.threat_level === "CRITICAL INTRUSION") {
            badgeHtml = `<span class="badge-threat-critical">🔴 CRITICAL INTRUSION</span>`;
        } else if (r.threat_level === "SUSPICIOUS") {
            badgeHtml = `<span class="badge-threat-suspicious">🟡 SUSPICIOUS</span>`;
        } else {
            badgeHtml = `<span class="badge-threat-normal">🟢 NORMAL</span>`;
        }

        const probPercent = (r.rf_prob * 100).toFixed(1);
        const gtClass = r.ground_truth_label === 1 ? "text-danger fw-semibold" : "text-success";
        const gtText = r.ground_truth_label !== null 
            ? `<span class="${gtClass}">${r.ground_truth_label === 1 ? "Attack" : "Normal"}</span> <small class="text-muted">(${r.ground_truth_cat})</small>`
            : "N/A";

        tr.innerHTML = `
            <td><strong>#${r.packet_id}</strong></td>
            <td><small class="text-muted">${r.timestamp}</small></td>
            <td><span class="badge bg-light text-dark border">${r.proto}</span></td>
            <td>${r.service}</td>
            <td>${r.sbytes.toLocaleString()} B</td>
            <td>
                <span class="badge ${r.rf_pred === 1 ? 'bg-danger' : 'bg-success'}">
                    ${r.rf_pred === 1 ? 'Attack' : 'Normal'}
                </span>
                <small class="text-muted ms-1">${probPercent}%</small>
            </td>
            <td><code>${r.ae_score.toFixed(4)}</code></td>
            <td>${badgeHtml}</td>
            <td>${gtText}</td>
        `;

        // Prepend to show most recent at the top
        this.tableBody.insertBefore(tr, this.tableBody.firstChild);

        // Keep maximum 25 rows in DOM for smooth rendering
        while (this.tableBody.children.length > 25) {
            this.tableBody.removeChild(this.tableBody.lastChild);
        }
    }

    appendChartPoint(r) {
        if (!this.timelineChart) return;

        const labels = this.timelineChart.data.labels;
        const aeData = this.timelineChart.data.datasets[0].data;
        const threshData = this.timelineChart.data.datasets[1].data;

        labels.push(`#${r.packet_id}`);
        aeData.push(r.ae_score);
        threshData.push(this.aeThreshold);

        if (labels.length > this.maxChartPoints) {
            labels.shift();
            aeData.shift();
            threshData.shift();
        }
    }

    updateKPIs() {
        if (this.lblProcessed) this.lblProcessed.textContent = this.totalProcessed.toLocaleString();
        if (this.lblNormal) this.lblNormal.textContent = this.normalCount.toLocaleString();
        if (this.lblAttack) this.lblAttack.textContent = this.attackCount.toLocaleString();
        if (this.lblCritical) this.lblCritical.textContent = this.criticalCount.toLocaleString();
        
        if (this.lblRate) {
            const rate = this.totalProcessed > 0 ? (this.attackCount / this.totalProcessed * 100).toFixed(1) : "0.0";
            this.lblRate.textContent = `${rate}%`;
        }
    }
}

document.addEventListener("DOMContentLoaded", () => {
    window.replayApp = new DatasetReplayManager();
});
