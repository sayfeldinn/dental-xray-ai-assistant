import { Link } from "react-router-dom";
import { Logo } from "../../components/brand/Logo";
import { ArchIllustration } from "./ArchIllustration";

const STEPS = [
  ["Upload the X-ray", "Add a panoramic radiograph to the patient's record, straight from your imaging export."],
  ["The model marks findings", "Caries, deep caries, periapical lesions and impacted teeth, each tied to an FDI tooth number."],
  ["You review every finding", "Confirm, reject or relabel. Nothing the model says counts until you do."],
  ["A plan with safety checks", "Treatments and drugs are proposed from your findings and checked against allergies, medications, age and weight."],
  ["You decide each prescription", "Warnings need your acknowledgement. Contraindicated drugs need a written reason."],
  ["Your corrections improve the model", "Every rejection and relabel is logged and sent back for retraining."],
];

const STATS = [
  ["97.5%", "of disease labels correct on held-out test images*"],
  ["4", "conditions detected, each mapped to a tooth"],
  ["26", "published drug-safety rules checked before any prescription"],
  ["0", "decisions made without the treating dentist"],
];

export function LandingPage() {
  return (
    <div className="bg-white">
      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-br from-brand-500 via-brand-600 to-brand-700 text-white">
        <div className="mx-auto max-w-7xl px-4 pb-14 pt-5 sm:px-6">
          <nav className="flex items-center gap-6">
            <Logo tone="white" />
            <div className="ml-auto hidden items-center gap-6 text-sm text-white/85 md:flex">
              <a href="#how" className="hover:text-white">How it works</a>
              <a href="#safety" className="hover:text-white">Safety</a>
              <a href="#evidence" className="hover:text-white">Evidence</a>
            </div>
            <Link to="/login" className="ml-auto rounded-full bg-white px-4 py-2 text-sm font-semibold text-brand-700 hover:bg-brand-50 md:ml-0">Sign in</Link>
          </nav>

          <div className="mt-10 grid items-end gap-10 lg:grid-cols-12">
            <div className="order-2 lg:order-1 lg:col-span-5">
              <h1 className="display text-[2.5rem] sm:text-6xl lg:text-[3.7rem]">A second reader for every <span className="whitespace-nowrap">dental X-ray</span></h1>
              <p className="mt-6 max-w-md text-base text-white/90">
                DentalAI marks possible findings on panoramic radiographs, tooth by tooth, and checks every proposed drug
                against the patient's history. You stay the one who decides.
              </p>
              <div className="mt-7 flex flex-wrap gap-3">
                <Link to="/login" className="rounded-full bg-white px-5 py-2.5 text-sm font-semibold text-brand-700 hover:bg-brand-50">Sign in</Link>
                <Link to="/login?mode=signup" className="rounded-full px-5 py-2.5 text-sm font-semibold ring-1 ring-white/70 hover:bg-white/10">Create a dentist account</Link>
              </div>
            </div>
            <div className="order-1 lg:order-2 lg:col-span-7">
              <div className="rounded-[2rem] bg-white/10 p-3 ring-1 ring-white/20 backdrop-blur-sm">
                <ArchIllustration />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Evidence strip */}
      <section id="evidence" className="border-b border-brand-100">
        <div className="mx-auto grid max-w-7xl gap-8 px-4 py-12 sm:grid-cols-2 sm:px-6 lg:grid-cols-4">
          {STATS.map(([n, label]) => (
            <div key={label}>
              <p className="display text-5xl text-brand-600">{n}</p>
              <p className="mt-2 max-w-[16rem] text-sm text-ink/70">{label}</p>
            </div>
          ))}
        </div>
        <p className="mx-auto max-w-7xl px-4 pb-6 text-xs text-ink/50 sm:px-6">
          *23 held-out images, 122 detections. A research prototype: the clinical rules come from ADA, AHA and AAPD guidance and have not yet been reviewed by a clinician.
        </p>
      </section>

      {/* How it works: a real sequence, so it is numbered */}
      <section id="how" className="mx-auto max-w-7xl px-4 py-20 sm:px-6">
        <h2 className="display max-w-2xl text-4xl sm:text-5xl">From X-ray to signed-off plan</h2>
        <ol className="mt-12 grid gap-x-10 gap-y-12 sm:grid-cols-2 lg:grid-cols-3">
          {STEPS.map(([title, body], i) => (
            <li key={title} className="border-t-2 border-brand-600 pt-5">
              <span className="display text-3xl text-brand-200">{i + 1}</span>
              <h3 className="title mt-3 text-lg">{title}</h3>
              <p className="mt-2 max-w-sm text-sm leading-relaxed text-ink/70">{body}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* Safety */}
      <section id="safety" className="bg-brand-50">
        <div className="mx-auto grid max-w-7xl items-center gap-12 px-4 py-20 sm:px-6 lg:grid-cols-2">
          <div className="rounded-[2rem] bg-gradient-to-br from-brand-500 to-brand-700 p-6 sm:p-10">
            <div className="rounded-2xl bg-white p-5 shadow-xl shadow-brand-900/20">
              <div className="flex items-center justify-between gap-3">
                <p className="title">Clindamycin</p>
                <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-800">Warning</span>
              </div>
              <p className="mt-1 text-sm text-ink/70">300 mg every 6 hours for 3 to 7 days</p>
              <p className="mt-4 rounded-xl bg-brand-50 p-3 text-sm text-ink/80">
                Amoxicillin was not proposed: penicillin allergy on record. Clindamycin is the ADA alternative.
              </p>
              <label className="mt-4 flex items-start gap-2 text-sm text-ink/80">
                <input type="checkbox" disabled className="mt-0.5" /> I have reviewed the warnings for this patient
              </label>
              <span className="mt-4 inline-block rounded-full bg-emerald-600/40 px-4 py-1.5 text-sm font-semibold text-white">Accept</span>
            </div>
          </div>
          <div>
            <h2 className="display text-4xl lg:text-[2.9rem]">We care about the prescription, not just the picture</h2>
            <p className="mt-6 max-w-lg leading-relaxed text-ink/75">
              Every proposed drug is checked against the patient's allergies, current medications, conditions, age and weight,
              using rules taken from ADA, AHA and AAPD guidance. A flagged drug can't be accepted by accident: a warning needs
              your acknowledgement, and a contraindication needs a written clinical reason that is kept on record.
            </p>
            <Link to="/login" className="mt-8 inline-block rounded-full bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-700">Open DentalAI</Link>
          </div>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}

export function SiteFooter() {
  return (
    <footer className="bg-ink text-white/70">
      <div className="mx-auto grid max-w-7xl gap-8 px-4 py-12 text-sm sm:px-6 md:grid-cols-3">
        <div>
          <Logo tone="white" />
          <p className="mt-4 max-w-xs">An assistive second-opinion tool for licensed dentists. It does not diagnose or prescribe on its own.</p>
        </div>
        <div>
          <p className="title text-white">Product</p>
          <ul className="mt-3 space-y-2">
            <li><a href="#how" className="hover:text-white">How it works</a></li>
            <li><a href="#safety" className="hover:text-white">Drug safety</a></li>
            <li><Link to="/login" className="hover:text-white">Sign in</Link></li>
          </ul>
        </div>
        <div>
          <p className="title text-white">Project</p>
          <p className="mt-3">IEEE IC-FTAI student project. Research prototype; not a medical device.</p>
        </div>
      </div>
    </footer>
  );
}
