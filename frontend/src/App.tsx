import { Link, Route, Routes } from "react-router-dom";
import { PendingBanner } from "./components/common/PendingBanner";
import { PatientsPage } from "./features/patients/PatientsPage";
import { PatientPage } from "./features/patients/PatientPage";
import { ScanPage } from "./features/scan-review/ScanPage";
import { Empty } from "./components/common/ui";

export function App() {
  return (
    <div className="flex min-h-full flex-col">
      <header className="bg-brand-900 text-white">
        <div className="mx-auto flex max-w-7xl items-center gap-6 px-4 py-3">
          <Link to="/" className="text-lg font-semibold tracking-tight">DentalAI</Link>
          <nav className="text-sm text-brand-100">
            <Link to="/" className="hover:text-white">Patients</Link>
          </nav>
          <span className="ml-auto hidden text-xs text-brand-100 sm:block">The system proposes, the dentist decides</span>
        </div>
      </header>
      <PendingBanner />
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6">
        <Routes>
          <Route path="/" element={<PatientsPage />} />
          <Route path="/patients/:patientId" element={<PatientPage />} />
          <Route path="/scans/:scanId" element={<ScanPage />} />
          <Route path="*" element={<Empty>Page not found.</Empty>} />
        </Routes>
      </main>
    </div>
  );
}
