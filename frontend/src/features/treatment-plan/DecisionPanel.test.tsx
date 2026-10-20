import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DecisionPanel } from "./DecisionPanel";
import { api } from "../../lib/api";
import type { Prescription } from "../../lib/types";
import { renderWithProviders } from "../../test/render";

vi.mock("../../lib/api", async (orig) => {
  const mod = await orig<typeof import("../../lib/api")>();
  return { ...mod, api: { ...mod.api, decidePrescription: vi.fn(), checkPrescription: vi.fn() } };
});
const decide = vi.mocked(api.decidePrescription);
const check = vi.mocked(api.checkPrescription);

const rx = (over: Partial<Prescription> = {}): Prescription => ({
  id: "rx1", treatment_id: "t1", patient_id: "p1", finding_id: "f1", drug_name: "Clindamycin", dosage: "300 mg",
  frequency: "every 6 hours", duration: "5 days", indication_type: "active_infection", instructions: null,
  contraindication_status: "clear", contraindication_warnings: [], dentist_status: "proposed", dentist_override_reason: null, ...over,
});

beforeEach(() => { decide.mockReset().mockResolvedValue(rx({ dentist_status: "accepted" })); check.mockReset(); });

test("a clear prescription can be accepted directly", async () => {
  const onDone = vi.fn();
  renderWithProviders(<DecisionPanel rx={rx()} onDone={onDone} onCancel={() => {}} />);
  await userEvent.click(screen.getByRole("button", { name: "Accept" }));
  await waitFor(() => expect(onDone).toHaveBeenCalled());
  expect(decide).toHaveBeenCalledWith("rx1", { decision: "accepted", acknowledge_warnings: undefined, override_reason: undefined });
});

test("a warning cannot be accepted until the dentist acknowledges it", async () => {
  renderWithProviders(<DecisionPanel rx={rx({ contraindication_status: "warning" })} onDone={() => {}} onCancel={() => {}} />);
  const accept = screen.getByRole("button", { name: "Accept" });
  expect(accept).toBeDisabled();
  await userEvent.click(screen.getByRole("checkbox"));
  expect(accept).toBeEnabled();
  await userEvent.click(accept);
  await waitFor(() => expect(decide).toHaveBeenCalledWith("rx1", expect.objectContaining({ acknowledge_warnings: true })));
});

test("a contraindicated drug needs a written justification to override", async () => {
  renderWithProviders(<DecisionPanel rx={rx({ contraindication_status: "contraindicated" })} onDone={() => {}} onCancel={() => {}} />);
  const button = screen.getByRole("button", { name: "Override and prescribe" });
  expect(button).toBeDisabled();
  await userEvent.type(screen.getByRole("textbox"), "Reaction was a mild rash; tolerated since");
  expect(button).toBeEnabled();
  await userEvent.click(button);
  await waitFor(() => expect(decide).toHaveBeenCalledWith("rx1", expect.objectContaining({ override_reason: "Reaction was a mild rash; tolerated since" })));
});

test("rejection needs nothing", async () => {
  renderWithProviders(<DecisionPanel rx={rx({ contraindication_status: "contraindicated" })} onDone={() => {}} onCancel={() => {}} />);
  await userEvent.click(screen.getByRole("radio", { name: "reject" }));
  await userEvent.click(screen.getByRole("button", { name: "Reject prescription" }));
  await waitFor(() => expect(decide).toHaveBeenCalledWith("rx1", { decision: "rejected" }));
});

test("modify sends only edited fields and gates on the live check", async () => {
  check.mockResolvedValue({ drug_name: "Clindamycin", indication_type: "active_infection", status: "warning",
    warnings: [{ code: "DAILY_DOSE", rule_id: "R-23", severity: "warning", drug: "Clindamycin", message: "High daily dose", source: "AAPD" }] });
  renderWithProviders(<DecisionPanel rx={rx()} onDone={() => {}} onCancel={() => {}} />);
  await userEvent.click(screen.getByRole("radio", { name: "modify" }));
  const dosage = screen.getByLabelText("Dosage");
  await userEvent.clear(dosage);
  await userEvent.type(dosage, "450 mg");
  expect(await screen.findByText("High daily dose", {}, { timeout: 2000 })).toBeInTheDocument();
  const save = screen.getByRole("button", { name: "Save changes" });
  expect(save).toBeDisabled();
  await userEvent.click(screen.getByRole("checkbox"));
  await userEvent.click(save);
  await waitFor(() => expect(decide).toHaveBeenCalledWith("rx1", { decision: "modified", dosage: "450 mg", acknowledge_warnings: true, override_reason: undefined }));
});

test("the backend's refusal is shown to the dentist", async () => {
  const { ApiError } = await import("../../lib/api");
  decide.mockRejectedValue(new ApiError(422, "Clindamycin has safety warnings: set acknowledge_warnings to accept it"));
  renderWithProviders(<DecisionPanel rx={rx()} onDone={() => {}} onCancel={() => {}} />);
  await userEvent.click(screen.getByRole("button", { name: "Accept" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("set acknowledge_warnings");
});
