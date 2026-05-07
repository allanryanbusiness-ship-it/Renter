(async () => {
  const appBase = "http://127.0.0.1:8000";
  const selectedText = String(window.getSelection ? window.getSelection() : "").trim();
  const pageText = selectedText ? "" : String(document.body?.innerText || "").slice(0, 12000);
  const userNotes = window.prompt("Optional Renter note for this listing:", "") || "";
  const payload = {
    source_url: window.location.href,
    page_title: document.title || "",
    selected_text: selectedText,
    page_text: pageText,
    source_domain: window.location.hostname.replace(/^www\./, ""),
    user_notes: userNotes,
    captured_at: new Date().toISOString(),
  };
  const json = JSON.stringify(payload, null, 2);
  const encodePayload = (value) => {
    const bytes = new TextEncoder().encode(JSON.stringify(value));
    let binary = "";
    bytes.forEach((byte) => {
      binary += String.fromCharCode(byte);
    });
    return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/, "");
  };
  const fallback = async (reason) => {
    try {
      await navigator.clipboard.writeText(json);
    } catch {
      window.prompt("Copy this browser clip JSON and paste it into Renter:", json);
    }
    const clipUrl = `${appBase}/#browser-clip=${encodePayload(payload)}`;
    window.open(clipUrl, "_blank", "noopener,noreferrer") || window.alert(`Clip copied. Open ${appBase} and paste it into Browser Clipper.`);
    if (reason) console.warn("Renter direct clip import failed; fallback payload copied.", reason);
  };

  try {
    const response = await fetch(`${appBase}/api/import/clip`, {
      method: "POST",
      mode: "cors",
      headers: { "Content-Type": "application/json" },
      body: json,
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const result = await response.json();
    window.alert(`Renter captured listing #${result.data.listing_id}. ${result.data.warnings.join(" ")}`);
  } catch (error) {
    await fallback(error.message);
  }
})();
