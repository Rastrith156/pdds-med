import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import App from "../App.jsx";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

test("OpenProject navigation shows the backend-provided setup state", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({
      configured: false,
      workspace_url: null,
      setup_instructions: "Set OPENPROJECT_URL, OPENPROJECT_API_KEY, and OPENPROJECT_PROJECT_ID in the backend environment.",
      project: null,
      work_packages: [],
      total_count: 0,
    }),
  }));

  render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);
  fireEvent.click(screen.getByRole("link", { name: "OpenProject" }));

  expect(await screen.findByRole("heading", { name: "OpenProject is not connected" })).toBeTruthy();
  expect(screen.getAllByText("OPENPROJECT_API_KEY").length).toBeGreaterThan(0);
  await waitFor(() => expect(fetch).toHaveBeenCalledWith(
    expect.stringContaining("/api/openproject/"),
    expect.any(Object),
  ));
});