const CONSENT_KEY = "lp_cookie_consent";
const VALID = new Set(["accepted", "rejected"]);

export function readConsent() {
  try {
    const value = localStorage.getItem(CONSENT_KEY);
    return VALID.has(value) ? value : "pending";
  } catch {
    return "pending";
  }
}

export function saveConsent(value) {
  if (!VALID.has(value)) throw new Error("Invalid consent value");
  localStorage.setItem(CONSENT_KEY, value);
  window.dispatchEvent(new CustomEvent("lp:consent", { detail: value }));
}

export function analyticsAllowed() {
  return readConsent() === "accepted";
}

export function resetConsent() {
  localStorage.removeItem(CONSENT_KEY);
  window.dispatchEvent(new CustomEvent("lp:consent", { detail: "pending" }));
}
