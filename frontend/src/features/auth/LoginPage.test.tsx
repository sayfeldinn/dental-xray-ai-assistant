import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../../test/render";
import { LoginPage } from "./LoginPage";

const auth = { signIn: vi.fn(), signUp: vi.fn(), sendReset: vi.fn() };
vi.mock("./AuthProvider", () => ({ useAuth: () => auth }));
vi.mock("../../lib/supabase", () => ({ authConfigured: true }));

beforeEach(() => Object.values(auth).forEach((f) => f.mockReset()));

test("signs in with email and password", async () => {
  auth.signIn.mockResolvedValue(undefined);
  renderWithProviders(<LoginPage />);
  await userEvent.type(screen.getByLabelText("Email"), "dr@clinic.eg");
  await userEvent.type(screen.getByLabelText("Password"), "secret-pass");
  await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
  await waitFor(() => expect(auth.signIn).toHaveBeenCalledWith("dr@clinic.eg", "secret-pass"));
});

test("shows the auth error", async () => {
  auth.signIn.mockRejectedValue(new Error("Invalid login credentials"));
  renderWithProviders(<LoginPage />);
  await userEvent.type(screen.getByLabelText("Email"), "dr@clinic.eg");
  await userEvent.type(screen.getByLabelText("Password"), "wrong");
  await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Invalid login credentials");
});

test("sign-up asks to confirm the email when the project requires it", async () => {
  auth.signUp.mockResolvedValue({ needsConfirmation: true });
  renderWithProviders(<LoginPage />);
  await userEvent.click(screen.getByRole("button", { name: "Create an account" }));
  await userEvent.type(screen.getByLabelText("Full name"), "Dr Sara");
  await userEvent.type(screen.getByLabelText("Email"), "sara@clinic.eg");
  await userEvent.type(screen.getByLabelText("Password"), "long-enough");
  await userEvent.click(screen.getByRole("button", { name: "Create a dentist account" }));
  expect(await screen.findByText(/Check your email/)).toBeInTheDocument();
  expect(auth.signUp).toHaveBeenCalledWith("sara@clinic.eg", "long-enough", "Dr Sara");
});
