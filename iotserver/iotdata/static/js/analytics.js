gsap.registerPlugin(ScrollTrigger);

const plotDefs = [
    { id: "ir-comparison", title: "IR Sensors Comparison" },
    { id: "speed-plot", title: "Vehicle Speed Over Time" },
    { id: "piezo-plot", title: "Piezo Vibration Level" },
    { id: "relay-states", title: "Relay States" },
    { id: "latency-plot", title: "Latency Difference" },
    { id: "speed-gauge", title: "Real-Time Speed Gauge" }
];

function createSkeletonPlots() {
    const container = document.getElementById("plots");
    container.innerHTML = "";

    plotDefs.forEach(p => {
        const div = document.createElement("div");
        div.className = "plot-container";
        div.innerHTML = `
            <div class="plot-title">${p.title}</div>
            <div id="${p.id}" style="height:500px;"></div>
        `;
        container.appendChild(div);

        Plotly.newPlot(p.id, [], {
            title: "Waiting for data...",
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#94a3b8' }
        });
    });

    gsap.utils.toArray(".plot-container").forEach(el => {
        gsap.from(el, {
            y: 100,
            opacity: 0,
            duration: 1.2,
            scrollTrigger: {
                trigger: el,
                start: "top 85%"
            }
        });
    });
}

function loadAllData() {
    const minutes = document.getElementById("timeRange").value;
    fetch(`/api/recent/?minutes=${minutes}`)
        .then(r => r.json())
        .then(updatePlots)
        .catch(() => console.warn("No data"));
}

function updatePlots(data) {
    if (!data || !data.table_rows || data.table_rows.length === 0) return;

    const rows = data.table_rows;
    const arduino = rows.filter(r => r.source === "arduino");
    const nodemcu = rows.filter(r => r.source === "nodemcu");

    Plotly.react("speed-plot", [{
        x: arduino.map(d => new Date(d.timestamp)),
        y: arduino.map(d => d.speed),
        mode: "lines+markers",
        line: { color: "#00ff9d", width: 4 }
    }], { paper_bgcolor: 'rgba(0,0,0,0)', font: { color: "#e2e8f0" } });

    const latest = arduino[arduino.length - 1] || { speed: 0 };

    Plotly.react("speed-gauge", [{
        type: "indicator",
        mode: "gauge+number",
        value: latest.speed,
        gauge: { axis: { range: [0, 200] } }
    }], { paper_bgcolor: 'rgba(0,0,0,0)' });
}

createSkeletonPlots();
loadAllData();
setInterval(loadAllData, 15000);
