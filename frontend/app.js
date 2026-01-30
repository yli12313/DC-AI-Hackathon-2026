(function () {
  const GOALS = [
    "Predict the World Cup 2026 winner",
    "Predict Golden Ball winner",
    "Predict Golden Boot winner",
    "Predict Golden Glove winner",
    "Predict Young Player Award winner",
  ];

  let selectedGoal = GOALS[0];

  const selectedGoalEl = document.getElementById("selectedGoal");
  const runBtn = document.getElementById("runWorkflow");
  const stepsSection = document.getElementById("stepsSection");
  const currentStepEl = document.getElementById("currentStep");
  const totalStepsEl = document.getElementById("totalSteps");
  const stepActionEl = document.getElementById("stepAction");
  const stepResultEl = document.getElementById("stepResult");
  const stepsLogEl = document.getElementById("stepsLog");
  const resultsSection = document.getElementById("resultsSection");
  const resultsContent = document.getElementById("resultsContent");
  const factorsList = document.getElementById("factorsList");
  const reportLinkEl = document.getElementById("reportLink");
  const errorSection = document.getElementById("errorSection");
  const errorMessageEl = document.getElementById("errorMessage");

  document.querySelectorAll(".goal-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      selectedGoal = this.getAttribute("data-goal");
      selectedGoalEl.textContent = selectedGoal;
      document.querySelectorAll(".goal-btn").forEach(function (b) { b.classList.remove("active"); });
      this.classList.add("active");
    });
  });
  document.querySelector(".goal-btn").classList.add("active");

  function showError(msg) {
    errorMessageEl.textContent = msg;
    errorSection.hidden = false;
  }
  function hideError() {
    errorSection.hidden = true;
  }

  function showStepProgress(num, total, action, result) {
    currentStepEl.textContent = num;
    totalStepsEl.textContent = total;
    stepActionEl.textContent = action || "";
    stepResultEl.textContent = result || "";
  }

  function appendStepLog(num, action, result) {
    const div = document.createElement("div");
    div.className = "step-log-item";
    div.innerHTML = "<span class=\"num\">Step " + num + "/10</span> " + escapeHtml(action) + " <span class=\"res\">" + escapeHtml(result || "") + "</span>";
    stepsLogEl.appendChild(div);
    stepsLogEl.scrollTop = stepsLogEl.scrollHeight;
  }

  function escapeHtml(s) {
    if (s == null) return "";
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  function renderFinalResults(output) {
    const top5 = output.top5 || [];
    const predictions = output.predictions || output.data || {};
    const factors = output.key_factors || [
      "FIFA ranking (25%)",
      "Historical performance (20%)",
      "Recent form (25%)",
      "Squad strength (20%)",
      "Home advantage (10%)",
    ];
    const list = Array.isArray(top5) ? top5 : Object.values(predictions).slice(0, 5);

    let html = "<div class=\"results-grid\">";
    list.forEach(function (item, i) {
      /* Player awards have name + team; team winner has team only. Show name first when present. */
      const primary = item.name || item.team || "—";
      const secondary = item.name && item.team ? " (" + item.team + ")" : "";
      const prob = item.probability != null ? item.probability + "%" : (item.score != null ? item.score : "—");
      const crest = item.crest || "";
      html += "<div class=\"result-row\">";
      html += "<span class=\"rank\">" + (i + 1) + "</span>";
      if (crest) html += "<img src=\"" + escapeHtml(crest) + "\" alt=\"\" referrerpolicy=\"no-referrer\" loading=\"lazy\">";
      html += "<span class=\"name\">" + escapeHtml(primary) + escapeHtml(secondary) + "</span>";
      html += "<span class=\"prob\">" + escapeHtml(String(prob)) + "</span>";
      html += "</div>";
    });
    html += "</div>";
    resultsContent.innerHTML = html;

    factorsList.innerHTML = factors.map(function (f) { return "<li>" + escapeHtml(f) + "</li>"; }).join("");
    reportLinkEl.innerHTML = "Detailed report: <a href=\"/api/report/world_cup_winner.json\" target=\"_blank\">world_cup_winner.json</a> | <a href=\"/api/report/player_predictions.json\" target=\"_blank\">player_predictions.json</a>";
  }

  function animateSteps(log, total, onDone) {
    let i = 0;
    function next() {
      if (i >= log.length) {
        onDone();
        return;
      }
      const entry = log[i];
      showStepProgress(entry.step, total, entry.action, entry.result);
      appendStepLog(entry.step, entry.action, entry.result);
      i += 1;
      setTimeout(next, 600);
    }
    next();
  }

  runBtn.addEventListener("click", async function () {
    hideError();
    stepsSection.hidden = false;
    resultsSection.hidden = true;
    stepsLogEl.innerHTML = "";
    showStepProgress(0, 10, "Preparing...", "");
    runBtn.disabled = true;

    try {
      const res = await fetch("/api/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ goal: selectedGoal }),
      });
      const data = await res.json().catch(function () { return {}; });
      if (!res.ok) {
        showError(data.detail || data.error || "Execution failed");
        runBtn.disabled = false;
        return;
      }
      const memory = data.memory || {};
      const log = memory.execution_log || [];
      const total = log.length || 10;
      animateSteps(log, total, function () {
        showStepProgress(total, total, "Complete", "Results ready for display");
        const output = data.output || memory.final_output || {};
        renderFinalResults(output);
        resultsSection.hidden = false;
        runBtn.disabled = false;
      });
    } catch (e) {
      showError("Request failed: " + (e.message || e));
      runBtn.disabled = false;
    }
  });
})();
