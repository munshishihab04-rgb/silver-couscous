import axios from "axios";
import { trackEvent } from "./tracking";
import { saveConsent } from "./privacy";

jest.mock("react-router-dom", () => ({
  useLocation: () => ({ pathname: "/", search: "" }),
}), { virtual: true });

jest.mock("axios", () => ({
  post: jest.fn(() => Promise.resolve({ data: { ok: true } })),
  get: jest.fn(),
}));

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
  axios.post.mockClear();
});

test("does not send analytics before consent", async () => {
  await trackEvent({ event_type: "page_view" });
  expect(axios.post).not.toHaveBeenCalled();
});

test("sends explicit consent flag after acceptance", async () => {
  saveConsent("accepted");
  await trackEvent({ event_type: "page_view" });
  expect(axios.post).toHaveBeenCalledTimes(1);
  expect(axios.post.mock.calls[0][1].analytics_consent).toBe(true);
});
