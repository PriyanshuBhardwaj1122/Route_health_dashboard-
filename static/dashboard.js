/* Admin dashboard — route rankings, charts, heatmap */

let categoryChart = null;
let severityChart = null;

document.addEventListener("DOMContentLoaded", async () => {
    await Promise.all([
        loadRankings(),
        loadHeatmap(),
    ]);
});

// ─── Helpers ────────────────────────────────────────────

function ratingBadge(rating) {
    let cls = "badge-success";
    if (rating < 2.5) cls = "badge-danger";
    else if (rating < 3.5) cls = "badge-warning";
    return `<span class="badge ${cls}">${rating.toFixed(1)}/5</span>`;
}

// ─── Rankings Table ─────────────────────────────────────

async function loadRankings() {
    const tbody = document.getElementById("rankings-body");
    try {
        const res = await fetch("/analytics/rankings");
        const rankings = await res.json();

        tbody.innerHTML = "";
        rankings.forEach(r => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>Route ${r.route_number}</strong></td>
                <td>${ratingBadge(r.overall_rating)}</td>
                <td>${r.total_feedback.toLocaleString()}</td>
                <td>${r.complaints_this_month.toLocaleString()}</td>
                <td>${r.top_issue}</td>
                <td>${r.worst_period}</td>
            `;
            tr.addEventListener("click", () => showRouteDetail(r));
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Failed to load rankings:", err);
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--danger);">Failed to load data</td></tr>`;
    }
}

// ─── Route Detail ───────────────────────────────────────

async function showRouteDetail(data) {
    const panel = document.getElementById("route-detail");
    const summary = document.getElementById("route-summary");
    const title = document.getElementById("detail-title");

    document.querySelectorAll("#rankings-body tr").forEach(tr => tr.classList.remove("selected"));
    if (event && event.currentTarget) event.currentTarget.classList.add("selected");

    title.textContent = `Route ${data.route_number} — Detail`;

    summary.innerHTML = `
<span class="label">Route:</span> <span class="val">${data.route_number}</span>
<span class="label">Overall Rating:</span> <span class="val">${data.overall_rating}/5</span>
<span class="label">Top Issue:</span> <span class="warn">${data.top_issue}</span>
<span class="label">Second Issue:</span> <span class="warn">${data.second_issue}</span>
<span class="label">Worst Period:</span> <span class="val">${data.worst_period}</span>
<span class="label">Feedback this month:</span> <span class="val">${data.complaints_this_month.toLocaleString()}</span>
<span class="label">Total feedback:</span> <span class="val">${data.total_feedback.toLocaleString()}</span>
    `.trim();

    panel.classList.add("show");

    await Promise.all([
        loadSubRatings(data.route_id),
        loadSeverityChart(data.route_id),
        loadTrends(data.route_id, data.route_number),
    ]);

    panel.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function loadSubRatings(routeId) {
    try {
        // We'll fetch the feedback and compute sub-rating averages client-side
        const res = await fetch(`/feedback?route_id=${routeId}&limit=500`);
        const feedbacks = await res.json();

        if (feedbacks.length === 0) return;

        const avgs = {
            "Overall": 0, "Punctuality": 0, "Cleanliness": 0,
            "Crowding": 0, "Driver Behaviour": 0,
        };
        feedbacks.forEach(f => {
            avgs["Overall"] += f.rating_overall;
            avgs["Punctuality"] += f.rating_punctuality;
            avgs["Cleanliness"] += f.rating_cleanliness;
            avgs["Crowding"] += f.rating_crowding;
            avgs["Driver Behaviour"] += f.rating_driver_behaviour;
        });
        const n = feedbacks.length;
        Object.keys(avgs).forEach(k => avgs[k] = +(avgs[k] / n).toFixed(2));

        const ctx = document.getElementById("category-chart").getContext("2d");
        if (categoryChart) categoryChart.destroy();

        const labels = Object.keys(avgs);
        const values = Object.values(avgs);
        const colors = values.map(v => v < 2.5 ? "#ef4444" : v < 3.5 ? "#f59e0b" : "#10b981");

        categoryChart = new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Avg Rating",
                    data: values,
                    backgroundColor: colors,
                    borderRadius: 4,
                    maxBarThickness: 50,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: "y",
                plugins: { legend: { display: false } },
                scales: { x: { beginAtZero: true, max: 5 } },
            }
        });
    } catch (err) {
        console.error("Failed to load sub-ratings:", err);
    }
}

async function loadSeverityChart(routeId) {
    try {
        const res = await fetch(`/analytics/severity-breakdown?route_id=${routeId}`);
        const data = await res.json();

        const ctx = document.getElementById("severity-chart").getContext("2d");
        if (severityChart) severityChart.destroy();

        severityChart = new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: ["Low", "Medium", "High"],
                datasets: [{
                    data: [data.Low, data.Medium, data.High],
                    backgroundColor: ["#10b981", "#f59e0b", "#ef4444"],
                    borderWidth: 0,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: "bottom" } },
            }
        });
    } catch (err) {
        console.error("Failed to load severity chart:", err);
    }
}

async function loadTrends(routeId, routeNumber) {
    const container = document.getElementById("trend-display");
    try {
        const res = await fetch(`/analytics/trends/${routeId}`);
        const data = await res.json();

        let html = '<div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px;">';
        data.trends.forEach(t => {
            let arrow, cls;
            if (t.direction === "improving") {
                arrow = "&#9650;"; cls = "trend-up";
            } else if (t.direction === "declining") {
                arrow = "&#9660;"; cls = "trend-down";
            } else {
                arrow = "&#9644;"; cls = "trend-stable";
            }

            html += `
                <div style="background:var(--bg); padding:12px; border-radius:var(--radius); text-align:center;">
                    <div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:4px;">${t.category}</div>
                    <div style="font-size:1.2rem; font-weight:600;" class="${cls}">${arrow} ${t.delta >= 0 ? "+" : ""}${t.delta.toFixed(2)}</div>
                    <div style="font-size:0.7rem; color:var(--text-muted);">${t.recent_avg.toFixed(1)} vs ${t.prior_avg.toFixed(1)}</div>
                </div>
            `;
        });
        html += '</div>';
        container.innerHTML = html;
    } catch (err) {
        console.error("Failed to load trends:", err);
        container.innerHTML = '<p style="color:var(--danger);">Failed to load trend data.</p>';
    }
}

// ─── Heatmap ────────────────────────────────────────────

async function loadHeatmap() {
    const container = document.getElementById("heatmap-container");
    try {
        const res = await fetch("/analytics/heatmap");
        const cells = await res.json();

        const lookup = {};
        let maxCount = 0;
        cells.forEach(c => {
            lookup[`${c.hour}-${c.day_of_week}`] = c;
            if (c.count > maxCount) maxCount = c.count;
        });

        const dayNames = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
        let html = '<div class="heatmap-header"></div>';
        dayNames.forEach(d => { html += `<div class="heatmap-header">${d}</div>`; });

        for (let h = 0; h <= 23; h++) {
            const label = h === 0 ? "12 AM" : h < 12 ? `${h} AM` : h === 12 ? "12 PM" : `${h-12} PM`;
            html += `<div class="heatmap-label">${label}</div>`;

            for (let d = 0; d < 7; d++) {
                const cell = lookup[`${h}-${d}`];
                if (cell && cell.count > 0) {
                    const intensity = cell.count / maxCount;
                    const bg = ratingToColor(cell.avg_rating);
                    html += `<div class="heatmap-cell" style="background:${bg};" title="Count: ${cell.count}, Avg: ${cell.avg_rating.toFixed(1)}">${cell.count}</div>`;
                } else {
                    html += `<div class="heatmap-cell" style="background:#e2e8f0; color: var(--text-muted);">0</div>`;
                }
            }
        }

        container.innerHTML = html;
    } catch (err) {
        console.error("Failed to load heatmap:", err);
        container.innerHTML = '<p style="color:var(--danger);">Failed to load heatmap data.</p>';
    }
}

function ratingToColor(avg) {
    // Green (good) → Yellow → Red (bad)
    if (avg >= 4.0) return "#10b981";
    if (avg >= 3.5) return "#34d399";
    if (avg >= 3.0) return "#fbbf24";
    if (avg >= 2.5) return "#f97316";
    return "#ef4444";
}
