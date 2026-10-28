const question = document.querySelector("#question");
const analyzeButton = document.querySelector("#analyze");
const empty = document.querySelector("#empty");
const result = document.querySelector("#result");

document.querySelectorAll("[data-question]").forEach((button) => {
  button.addEventListener("click", () => { question.value = button.dataset.question; question.focus(); });
});
question.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) analyzeButton.click();
});

function renderChart(chart) {
  const max = Math.max(...chart.y.map((value) => Math.abs(value)), 1);
  document.querySelector("#chart-label").textContent = chart.y_label;
  document.querySelector("#chart").innerHTML = chart.y.map((value, index) => {
    const height = Math.max(Math.abs(value) / max * 180, 5);
    return `<div class="bar-wrap"><div class="bar ${value < 0 ? "negative" : ""}" style="height:${height}px" title="${value}"></div><div class="bar-label">${chart.x[index]}</div></div>`;
  }).join("");
}
function renderTable(rows) {
  if (!rows.length) return "";
  const columns = Object.keys(rows[0]);
  return `<table><thead><tr>${columns.map((column) => `<th>${column}</th>`).join("")}</tr></thead><tbody>${rows.map((row) => `<tr>${columns.map((column) => `<td>${typeof row[column] === "number" ? Number(row[column]).toLocaleString(undefined, {maximumFractionDigits: 2}) : row[column]}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
}
analyzeButton.addEventListener("click", async () => {
  const text = question.value.trim();
  if (!text) { question.focus(); return; }
  analyzeButton.disabled = true; analyzeButton.textContent = "Working…";
  try {
    const response = await fetch("/api/analyze", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({question:text})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "The analysis could not be completed.");
    empty.classList.add("hidden"); result.classList.remove("hidden");
    document.querySelector("#trace-id").textContent = data.trace_id.slice(0, 8);
    document.querySelector("#title").textContent = data.title;
    document.querySelector("#summary").textContent = data.summary;
    document.querySelector("#methodology").textContent = data.methodology;
    document.querySelector("#findings").innerHTML = data.findings.map((item) => `<li>${item}</li>`).join("");
    document.querySelector("#caveat").textContent = data.caveats[0];
    document.querySelector("#row-count").textContent = `${data.evidence[0].row_count} rows`;
    document.querySelector("#sql").textContent = data.evidence[0].sql;
    document.querySelector("#evidence-table").innerHTML = renderTable(data.evidence[0].rows);
    document.querySelector("#trace").innerHTML = data.trace.map((step) => `<div class="trace-step"><span class="check">${step.status === "completed" ? "✓" : "!"}</span><span><strong>${step.name.replaceAll("_", " ")}</strong><br>${step.detail}</span></div>`).join("");
    renderChart(data.chart); result.scrollIntoView({behavior:"smooth", block:"start"});
  } catch (error) {
    empty.classList.remove("hidden"); result.classList.add("hidden"); empty.querySelector("h2").textContent = "Analysis could not be completed."; empty.querySelector("p").textContent = error.message;
  } finally { analyzeButton.disabled = false; analyzeButton.innerHTML = 'Run analysis <span>↗</span>'; }
});
