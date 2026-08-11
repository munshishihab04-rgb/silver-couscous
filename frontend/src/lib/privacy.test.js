import { analyticsAllowed, readConsent, resetConsent, saveConsent } from "./privacy";

beforeEach(() => localStorage.clear());

test("analytics is denied until explicit consent", () => {
  expect(readConsent()).toBe("pending");
  expect(analyticsAllowed()).toBe(false);
});

test("analytics is allowed only after acceptance", () => {
  saveConsent("accepted");
  expect(readConsent()).toBe("accepted");
  expect(analyticsAllowed()).toBe(true);
});

test("rejected consent keeps analytics disabled", () => {
  saveConsent("rejected");
  expect(analyticsAllowed()).toBe(false);
});

test("consent can be reset from persistent preferences", () => {
  saveConsent("accepted");
  resetConsent();
  expect(readConsent()).toBe("pending");
});
