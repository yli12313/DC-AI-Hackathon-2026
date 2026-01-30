(function () {
  const GOALS = [
    "Predict the World Cup 2026 winner",
    "Predict Golden Ball winner",
    "Predict Golden Boot winner",
    "Predict Golden Glove winner",
    "Predict Young Player Award winner",
  ];

  const GOAL_DESCRIPTIONS = {
    "Predict the World Cup 2026 winner":
      "<strong>Where the data comes from</strong><ul>" +
      "<li>Wikipedia: 2026 FIFA World Cup qualification page (qualified teams)</li>" +
      "<li>FIFA Men's World Ranking (current ranks and points)</li>" +
      "<li>Historical World Cup results (2014, 2018, 2022) for form and past performance</li>" +
      "</ul><strong>How the algorithm works</strong><ul>" +
      "<li>FIFA ranking: 25% of the score</li>" +
      "<li>Historical performance (World Cup wins): 20%</li>" +
      "<li>Recent form (last World Cup result): 25%</li>" +
      "<li>Squad strength: 20%</li>" +
      "<li>Home advantage: 10% (USA, Mexico, Canada get a bonus as hosts)</li>" +
      "</ul><strong>How the prediction is made</strong><ul>" +
      "<li>Each team is scored on these five factors; scores are combined and normalized</li>" +
      "<li>Top five teams are ranked and shown with a probability share of the total</li>" +
      "</ul>",
    "Predict Golden Ball winner":
      "<strong>Where the data comes from</strong><ul>" +
      "<li>Wikipedia national team pages: current squad rosters (forwards and midfielders)</li>" +
      "<li>Individual player pages: honours (Ballon d'Or, World Cup Golden Ball, FIFA Best), caps, and goals</li>" +
      "<li>Curated list of elite players when the API returns no data</li>" +
      "</ul><strong>How the algorithm works</strong><ul>" +
      "<li>Honours (e.g. Ballon d'Or winner, World Cup Golden Ball): 50% of the score</li>" +
      "<li>Rating (overall quality): 25%</li>" +
      "<li>Goals and assists: 25%</li>" +
      "<li>Ballon d'Or and World Cup Golden Ball winners get the highest honour scores</li>" +
      "</ul><strong>How the prediction is made</strong><ul>" +
      "<li>Each candidate is scored; top five are ranked and shown with probability percentages</li>" +
      "</ul>",
    "Predict Golden Boot winner":
      "<strong>Where the data comes from</strong><ul>" +
      "<li>Wikipedia national team rosters: forwards only</li>" +
      "<li>International goal totals and ratings from player pages or a curated list of top scorers</li>" +
      "</ul><strong>How the algorithm works</strong><ul>" +
      "<li>International goals: 80% of the score (favours proven scorers)</li>" +
      "<li>Rating: 20%</li>" +
      "</ul><strong>How the prediction is made</strong><ul>" +
      "<li>Each forward is scored; top five are ranked and shown with probability percentages</li>" +
      "</ul>",
    "Predict Golden Glove winner":
      "<strong>Where the data comes from</strong><ul>" +
      "<li>Wikipedia national team rosters: goalkeepers only</li>" +
      "<li>Clean sheets, saves, and ratings from a curated list (Wikipedia and known stats)</li>" +
      "</ul><strong>How the algorithm works</strong><ul>" +
      "<li>Clean sheets: 50% of the score (consistency)</li>" +
      "<li>Rating: 50% (overall quality)</li>" +
      "</ul><strong>How the prediction is made</strong><ul>" +
      "<li>Each goalkeeper is scored; top five are ranked and shown with probability percentages</li>" +
      "</ul>",
    "Predict Young Player Award winner":
      "<strong>Where the data comes from</strong><ul>" +
      "<li>Wikipedia rosters: young players (typically under 21)</li>" +
      "<li>Age, goals, assists, and rating from a curated list of emerging stars</li>" +
      "</ul><strong>How the algorithm works</strong><ul>" +
      "<li>Age bonus: younger players score higher (under-21 focus)</li>" +
      "<li>Rating: 40%</li>" +
      "<li>Goals: 30%</li>" +
      "<li>Assists: 20%</li>" +
      "</ul><strong>How the prediction is made</strong><ul>" +
      "<li>Each young player is scored; top five are ranked and shown with probability percentages</li>" +
      "</ul>",
  };

  let selectedGoal = GOALS[0];

  const selectedGoalEl = document.getElementById("selectedGoal");
  const goalDescriptionEl = document.getElementById("goalDescription");
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

  function updateGoalDescription() {
    if (goalDescriptionEl) {
      goalDescriptionEl.innerHTML = GOAL_DESCRIPTIONS[selectedGoal] || "";
    }
  }

  document.querySelectorAll(".goal-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      selectedGoal = this.getAttribute("data-goal");
      selectedGoalEl.textContent = selectedGoal;
      document.querySelectorAll(".goal-btn").forEach(function (b) { b.classList.remove("active"); });
      this.classList.add("active");
      updateGoalDescription();
    });
  });
  document.querySelector(".goal-btn").classList.add("active");
  updateGoalDescription();

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
      const primary = item.name || item.team || "—";
      const secondary = item.name && item.team ? " (" + item.team + ")" : "";
      const prob = item.probability != null ? item.probability + "%" : (item.score != null ? item.score : "—");
      const crest = (item.crest && String(item.crest).trim()) || "";
      const description = item.description || "";
      const reason = item.reason || "";
      html += "<div class=\"result-card\">";
      html += "<div class=\"result-row\">";
      html += "<span class=\"rank\">" + (i + 1) + "</span>";
      if (crest) html += "<img class=\"result-crest\" src=\"" + escapeHtml(crest) + "\" alt=\"\" referrerpolicy=\"no-referrer\" loading=\"lazy\">";
      html += "<span class=\"name\">" + escapeHtml(primary) + escapeHtml(secondary) + "</span>";
      html += "<span class=\"prob\">" + escapeHtml(String(prob)) + "</span>";
      html += "</div>";
      if (description) html += "<p class=\"result-description\">" + escapeHtml(description) + "</p>";
      if (reason) html += "<p class=\"result-reason\">" + escapeHtml(reason) + "</p>";
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
