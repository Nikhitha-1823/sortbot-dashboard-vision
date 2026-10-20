function updateClock() {
  const now = new Date();
  const clock = document.getElementById("clock");
  if (clock) clock.textContent = now.toLocaleTimeString();
}


async function refreshStatus() {
    try {
        const [statusResponse, healthResponse] = await Promise.all([
            fetch("/api/status", { cache: "no-store" }),
            fetch("/api/health", { cache: "no-store" })
        ]);

        if (!statusResponse.ok || !healthResponse.ok) {
            throw new Error("API unavailable");
        }

        const data = await statusResponse.json();
        const health = await healthResponse.json();

        // Vision pipeline label
        const visionStatus = document.getElementById("vision-status");
        if (visionStatus) {
            visionStatus.textContent = health.python_vision || "Not started";
        }

        // Camera status label
        const cameraStatus = document.getElementById("camera-status");
        if (cameraStatus) {
            cameraStatus.textContent = health.camera || "Not connected";
        }

        // System Health rows — updated if these IDs exist in index.html
        const dashboardHealth = document.getElementById("dashboard-health");
        if (dashboardHealth) dashboardHealth.textContent = health.dashboard;

        const pythonHealth = document.getElementById("python-vision-health");
        if (pythonHealth) pythonHealth.textContent = health.python_vision;

        const cameraHealth = document.getElementById("camera-health");
        if (cameraHealth) cameraHealth.textContent = health.camera;

        const esp32Health = document.getElementById("esp32-health");
        if (esp32Health) esp32Health.textContent = health.esp32;
        
        const activityList = document.getElementById("activity-list");
        if (activityList) {
            activityList.replaceChildren();

            (data.activity || []).forEach(item => {
                const row = document.createElement("div");
                row.className = "activity-item";

                const title = document.createElement("strong");
                title.textContent = item.message || "Object detected";

                const detail = document.createElement("div");
                detail.textContent = item.detail || "";

                row.append(title, detail);
                activityList.appendChild(row);
            });

        if (!data.activity || data.activity.length === 0) {
            activityList.textContent = "No live detection events yet.";
        }
    }

        const counts = data.counts || {};
        for (const color of ["red", "green", "blue", "yellow"]) {
            const element = document.getElementById(`${color}-count`);
            if (element) {
                element.textContent = counts[color.toUpperCase()] ?? 0;
            } 
        }

        const totalElement = document.getElementById("total");
        if (totalElement) totalElement.textContent = data.total ?? 0;

        const updated = document.getElementById("updated");
        if (updated) {
            updated.textContent = "API sync " + new Date().toLocaleTimeString();
        }
    } catch (err) {
        const updated = document.getElementById("updated");
        if (updated) updated.textContent = "API disconnected";
    }
}


// SORTBOT: update the dashboard from Flask's /api/status endpoint
async function updateSortbotDashboard() {
  try {
    const response = await fetch("/api/status", { cache: "no-store" });

    if (!response.ok) {
      throw new Error(`API returned ${response.status}`);
    }

    const data = await response.json();
    window.latestCounts = data.counts || {};
    // Read the API values safely
    const camera = data.camera || "Unknown";
    const vision = data.vision || "Unknown";
    const counts = data.counts || {};

    // Color counters
    document.getElementById("red-count").textContent = counts.RED ?? 0;
    document.getElementById("green-count").textContent = counts.GREEN ?? 0;
    document.getElementById("blue-count").textContent = counts.BLUE ?? 0;
    document.getElementById("yellow-count").textContent = counts.YELLOW ?? 0;

    // Total detected objects (use API total if provided)
    const total = data.total ??
      (Number(counts.RED || 0) +
       Number(counts.GREEN || 0) +
       Number(counts.BLUE || 0) +
       Number(counts.YELLOW || 0));

    document.getElementById("total").textContent = total;

    // Camera status label
    const cameraStatus = document.getElementById("camera_status");
    if (cameraStatus) {
      const cameraIsConnected =
        String(camera).toLowerCase().includes("connected") &&
        !String(camera).toLowerCase().includes("not connected");

      cameraStatus.innerHTML = cameraIsConnected
        ? '<i class="dot green"></i>CONNECTED'
        : '<i class="dot amber"></i>NOT CONNECTED';
    }

    // Vision pipeline
    document.getElementById("vision-status").textContent =
      String(vision).toUpperCase();

    document.getElementById("overlay-status").textContent =
      String(vision).toLowerCase() === "running" ? "ON" : "OFF";

    // System health rows
    const visionHealth = document.getElementById("python-vision-health");
    visionHealth.innerHTML =
      String(vision).toLowerCase() === "running"
        ? 'Running <b>✓</b>'
        : 'Not running <b>!</b>';
    visionHealth.className =
      String(vision).toLowerCase() === "running" ? "good" : "pending";

    const cameraHealth = document.getElementById("camera-health");
    cameraHealth.innerHTML =
      String(camera).toLowerCase().includes("connected") &&
      !String(camera).toLowerCase().includes("not connected")
        ? 'Connected <b>✓</b>'
        : 'Not connected <b>!</b>';
    cameraHealth.className =
      cameraHealth.textContent.toLowerCase().includes("connected") &&
      !cameraHealth.textContent.toLowerCase().includes("not connected")
        ? "good"
        : "pending";

    const esp32Health = document.getElementById("esp32-health");
    if (esp32Health && data.esp32) {
      esp32Health.textContent = data.esp32;
      esp32Health.className =
        String(data.esp32).toLowerCase().includes("connected")
          ? "good"
          : "pending";
    }

    // API update timestamp
    const updated = document.getElementById("updated");
    if (updated) {
      updated.textContent = new Date().toLocaleTimeString();
    }

    // Recent activity, if the API provides it
    const activityList = document.getElementById("activity-list");
    if (activityList && Array.isArray(data.activity)) {
      activityList.replaceChildren();

      data.activity.slice(0, 6).forEach((item) => {
        const row = document.createElement("div");
        row.className = "activity-item";

        // Supports either plain-text activity entries or objects
        const message =
          typeof item === "string"
            ? item
            : item.message || item.text || item.event || JSON.stringify(item);

        row.textContent = message;
        activityList.appendChild(row);
      });
    }
  } catch (error) {
    console.error("SORTBOT dashboard API update failed:", error);

    const updated = document.getElementById("updated");
    if (updated) updated.textContent = "API unavailable";
  }
}

// Update once immediately, then poll the backend every second
updateSortbotDashboard();
setInterval(updateSortbotDashboard, 1000);
function updateProcessStatus() {
  const steps = document.querySelectorAll(".process-step");
  if (!steps.length) return;

  const hasObject = Object.values(
    window.latestCounts || {}
  ).some(count => Number(count) > 0);

  if (hasObject) {
    if (!window.sortbotStageStart) {
      window.sortbotStageStart = Date.now();
    }

    const stage = Math.min(
      3,
      Math.floor((Date.now() - window.sortbotStageStart) / 1000)
    );

    steps.forEach((step, index) => {
      step.classList.toggle("active", index === stage);
      step.classList.toggle("completed", index < stage);
    });
  } else {
    window.sortbotStageStart = null;
    steps.forEach((step, index) => {
      step.classList.toggle("active", index === 0);
      step.classList.remove("completed");
    });
  }
}

setInterval(updateProcessStatus, 500);