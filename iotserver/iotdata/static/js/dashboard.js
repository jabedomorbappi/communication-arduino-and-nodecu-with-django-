const fetchInterval = 800;

// ELEMENTS
const modeToggle = document.getElementById("controlModeToggle");
const commonControls = document.getElementById("common-controls");
const individualControls = document.getElementById("individual-controls");
const commonSwitch = document.getElementById("commonSwitch");
const arduinoSwitch = document.getElementById("arduinoSwitch");
const nodemcuSwitch = document.getElementById("nodemcuSwitch");
const connectionStatusEl = document.getElementById("connection-status");
const ipDisplayEl = document.getElementById("nodemcu-ip-display");
const arduinoIr1El = document.getElementById("arduino_ir1");
const arduinoIr2El = document.getElementById("arduino_ir2");
const nodemcuIr1El = document.getElementById("nodemcu_ir1");
const nodemcuIr2El = document.getElementById("nodemcu_ir2");
const piezoValueEl = document.getElementById("piezo-value");
const speedValueEl = document.getElementById("speed");
const latencyDiffEl = document.getElementById("latency_diff");

// STATE
const commandPending = { common: false, arduino: false, nodemcu: false };
let lastConnectedStatus = false;

// UTILITIES
async function fetchLatestData() {
    try {
        const r = await fetch('/api/latest/');
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return await r.json();
    } catch (e) {
        console.error("Fetch failed:", e);
        return null;
    }
}

function sendRelayCommand(state, type, switchElement) {
    if (commandPending[type]) return;
    commandPending[type] = true;
    switchElement.disabled = true;
    fetch('/api/control/relay/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ state: state, type: type })
    }).then(r => r.json())
    .then(() => {
        commandPending[type] = false;
        switchElement.disabled = false;
    }).catch(err => {
        console.error(`Command failed for ${type}`, err);
        commandPending[type] = false;
        switchElement.disabled = false;
    });
}

// GAUGES
function initGauges() {
    // Vehicle Speed Gauge
    Plotly.newPlot('speed-gauge', [{
        type: "indicator",
        mode: "gauge+number",
        value: 0,
        number: { suffix: " km/h" },
        gauge: {
            axis: { range: [0, 100] },
            bar: { color: "#00ff00" },
            steps: [
                { range: [0, 20], color: "darkgreen" },
                { range: [20, 50], color: "orange" },
                { range: [50, 100], color: "red" }
            ]
        }
    }], { paper_bgcolor: "rgba(0,0,0,0)", font: { color: "#00ffff", family: "Orbitron" }, height: 250 });

    // Piezo Value Gauge (0-1023)
    Plotly.newPlot('piezo-gauge', [{
        type: "indicator",
        mode: "gauge+number",
        value: 0,
        number: { suffix: "" },
        gauge: {
            axis: { range: [0, 1023] },
            bar: { color: "#ffff00" },
            steps: [
                { range: [0, 341], color: "darkblue" },
                { range: [341, 682], color: "orange" },
                { range: [682, 1023], color: "red" }
            ]
        }
    }], { paper_bgcolor: "rgba(0,0,0,0)", font: { color: "#00ffff", family: "Orbitron" }, height: 250 });
}

function updateGauges(speed, piezo) {
    // Update Vehicle Speed
    Plotly.react('speed-gauge', [{
        type: "indicator",
        mode: "gauge+number",
        value: speed,
        number: { suffix: " km/h" },
        gauge: {
            axis: { range: [0, 100] },
            bar: { color: speed < 20 ? "#00ff00" : speed < 50 ? "#ffff00" : "#ff0000" },
            steps: [
                { range: [0, 20], color: "darkgreen" },
                { range: [20, 50], color: "orange" },
                { range: [50, 100], color: "red" }
            ]
        }
    }]);

    // Update Piezo Value (0-1023)
    Plotly.react('piezo-gauge', [{
        type: "indicator",
        mode: "gauge+number",
        value: piezo,
        number: { suffix: "" },
        gauge: {
            axis: { range: [0, 1023] },
            bar: { color: piezo < 341 ? "#00ff00" : piezo < 682 ? "#ffff00" : "#ff0000" },
            steps: [
                { range: [0, 341], color: "darkblue" },
                { range: [341, 682], color: "orange" },
                { range: [682, 1023], color: "red" }
            ]
        }
    }]);

    speedValueEl.textContent = speed.toFixed(1);
    piezoValueEl.textContent = piezo;
}


// POLLING LOOP
setInterval(async () => {
    const data = await fetchLatestData();
    if(data){
        // Connection
        const isConnected = data.is_connected;
        const ip = data.nodemcu_ip;
        if(isConnected!==lastConnectedStatus){
            lastConnectedStatus=isConnected;
            if(isConnected){ connectionStatusEl.textContent="CONNECTED"; connectionStatusEl.className="status-connected"; ipDisplayEl.textContent=`NodeMCU IP: ${ip}`; }
            else { connectionStatusEl.textContent="WAITING..."; connectionStatusEl.className="status-disconnected"; ipDisplayEl.textContent="NodeMCU IP: Searching..."; }
        }

        // IR Sensors
        arduinoIr1El.textContent = data.arduino.ir1 ?? "—";
        arduinoIr2El.textContent = data.arduino.ir2 ?? "—";
        nodemcuIr1El.textContent = data.nodemcu.ir1 ?? "—";
        nodemcuIr2El.textContent = data.nodemcu.ir2 ?? "—";

        // Latency
        latencyDiffEl.textContent = data.latency_diff ?? "—";

        // Gauges
        const speed = data.arduino.speed || 0;
        const piezo = data.arduino.piezo || 0;
        updateGauges(speed, piezo);

        // Lights (sync code same as before)...
    }
}, fetchInterval);

window.onload = function(){
    initGauges();
};
