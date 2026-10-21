import { Link, NavLink, Navigate, Route, Routes } from "react-router-dom";
import { PendingBanner } from "./components/common/PendingBanner";
import { Logo } from "./components/brand/Logo";
import { PatientsPage } from "./features/patients/PatientsPage";
import { PatientPage } from "./features/patients/PatientPage";
import { ScanPage } from "./features/scan-review/ScanPage";
import { LoginPage } from "./features/auth/LoginPage";
import { NewPasswordPage } from "./features/auth/NewPasswordPage";
import { LandingPage } from "./features/landing/LandingPage";
import { useAuth } from "./features/auth/AuthProvider";
import { Empty, Spinner } from "./components/common/ui";

export function App() {
  const { session, loading, recovering, signOut } = useAuth();

  if (loading) return <Spinner label="Checking your session…" />;
  if (recovering) return <AuthLayout><NewPasswordPage /></AuthLayout>;
  if (!session) {
    return (
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<AuthLayout><LoginPage /></AuthLayout>} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  const name = (session.user.user_metadata?.full_name as string | undefined) ?? session.user.email;
  return (
    <div className="flex min-h-full flex-col">
      <header className="sticky top-0 z-10 border-b border-brand-100 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3 sm:px-6">
          <Link to="/" aria-label="DentalAI home"><Logo /></Link>
          <nav className="text-sm">
            <NavLink to="/" end className={({ isActive }) => `rounded-full px-3 py-1.5 font-medium ${isActive ? "bg-brand-50 text-brand-700" : "text-ink/70 hover:text-ink"}`}>Patients</NavLink>
          </nav>
          <span className="ml-auto flex items-center gap-3 text-sm">
            <span className="hidden text-ink/70 sm:inline" title={session.user.email}>{name}</span>
            <button onClick={() => void signOut()} className="rounded-full bg-brand-600 px-4 py-1.5 font-semibold text-white hover:bg-brand-700">Sign out</button>
          </span>
        </div>
        <PendingBanner />
      </header>
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6">
        <Routes>
          <Route path="/" element={<PatientsPage />} />
          <Route path="/login" element={<Navigate to="/" replace />} />
          <Route path="/patients/:patientId" element={<PatientPage />} />
          <Route path="/scans/:scanId" element={<ScanPage />} />
          <Route path="*" element={<Empty>Page not found.</Empty>} />
        </Routes>
      </main>
    </div>
  );
}

/** Split screen for sign-in screens: rose brand panel beside the form, as on the landing hero. */
function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid min-h-full lg:grid-cols-2">
      <aside className="hidden flex-col justify-between bg-gradient-to-br from-brand-500 via-brand-600 to-brand-700 p-10 text-white lg:flex">
        <Link to="/"><Logo tone="white" /></Link>
        <div>
          <h2 className="display text-5xl">The system proposes. The dentist decides.</h2>
          <p className="mt-5 max-w-md text-white/85">Sign in to review AI findings on your patients' X-rays and sign off every treatment and prescription.</p>
        </div>
        <p className="text-xs text-white/70">Research prototype · not a medical device</p>
      </aside>
      <div className="flex flex-col bg-petal">
        <div className="p-5 lg:hidden"><Link to="/"><Logo /></Link></div>
        <div className="flex flex-1 items-center justify-center px-4 py-10">{children}</div>
      </div>
    </div>
  );
}
