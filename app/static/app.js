const form = document.getElementById("ticket-form");
const input = document.getElementById("ticket-text");
const button = document.getElementById("submit-button");
const result = document.getElementById("result");
const statusBadge = document.getElementById("api-status");
const charCount = document.getElementById("char-count");

input.addEventListener("input", () => {
  charCount.textContent = `${input.value.length} / 5000`;
});

async function checkHealth() {
  try {
    const response = await fetch("/readyz");
    if (!response.ok) throw new Error("Modelo no disponible");
    statusBadge.textContent = "API y modelo listos";
    statusBadge.className = "status status-ok";
  } catch (_) {
    statusBadge.textContent = "API activa; modelo por verificar";
    statusBadge.className = "status status-bad";
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  result.classList.add("hidden");
  button.disabled = true;
  button.textContent = "Clasificando…";

  try {
    const response = await fetch("/api/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: input.value })
    });
    const payload = await response.json();
    if (!response.ok) {
      const detail = typeof payload.detail === "string" ? payload.detail : "Solicitud no válida.";
      throw new Error(detail);
    }

    document.getElementById("intent-name").textContent = payload.predicted_intent;
    document.getElementById("confidence").textContent = `${(payload.confidence * 100).toFixed(1)}%`;
    document.getElementById("threshold").textContent = `${(payload.confidence_threshold * 100).toFixed(0)}%`;
    document.getElementById("intent-id").textContent = payload.predicted_intent_id;
    document.getElementById("decision-pill").textContent = payload.requires_human_review ? "Revisión humana" : "Sugerencia";
    document.getElementById("decision-pill").className = payload.requires_human_review ? "decision-pill decision-review" : "decision-pill";
    document.getElementById("review-note").textContent = payload.requires_human_review
      ? "La confianza no alcanzó el umbral configurado. El ticket debe revisarse manualmente."
      : "El modelo generó una sugerencia que debe ser confirmada por el agente.";
    document.getElementById("priority-note").textContent = payload.priority_note;
    document.getElementById("disclaimer").textContent = payload.disclaimer;
    result.classList.remove("hidden");
  } catch (error) {
    alert(error.message || "No fue posible conectar con la API.");
  } finally {
    button.disabled = false;
    button.innerHTML = 'Clasificar ticket <span aria-hidden="true">→</span>';
  }
});

checkHealth();
