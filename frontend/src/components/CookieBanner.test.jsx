import "@testing-library/jest-dom";
import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import CookieBanner from "./CookieBanner";
import { resetConsent, saveConsent } from "../lib/privacy";

beforeEach(() => localStorage.clear());

test("requires an explicit cookie choice and stores rejection", async () => {
  const user = userEvent.setup();
  render(<CookieBanner />);
  expect(screen.getByRole("dialog", { name: /preferenze cookie/i })).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: /rifiuta non essenziali/i }));
  expect(screen.queryByRole("dialog", { name: /preferenze cookie/i })).not.toBeInTheDocument();
  expect(localStorage.getItem("lp_cookie_consent")).toBe("rejected");
});

test("reopens when persistent preferences are reset", async () => {
  saveConsent("accepted");
  render(<CookieBanner />);
  expect(screen.queryByRole("dialog", { name: /preferenze cookie/i })).not.toBeInTheDocument();
  act(() => resetConsent());
  expect(await screen.findByRole("dialog", { name: /preferenze cookie/i })).toBeInTheDocument();
});
