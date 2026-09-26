# Creates Week 1 labels, issues, and the project board for DentalAI.
# Idempotent-ish: labels are upserted; issues are skipped if an identical title exists.
# Usage: .\scripts\setup-week1-board.ps1

$ErrorActionPreference = "Stop"

$repo = "sayfeldinn/dental-xray-ai-assistant"

$roleLabels = @(
    @{ name = "ml";       color = "d73a4a"; desc = "Person A — ML Engineer" },
    @{ name = "backend";  color = "0075ca"; desc = "Person B — Backend Engineer" },
    @{ name = "frontend"; color = "a2eeef"; desc = "Person C — Frontend Engineer" },
    @{ name = "qa";       color = "0e8a16"; desc = "Person D — Integration/QA Engineer" },
    @{ name = "lead";     color = "fbca04"; desc = "Person E — Team Lead / Clinical Liaison" },
    @{ name = "team";     color = "5319e7"; desc = "Whole team" }
)
$dayLabels = 1..5 | ForEach-Object { @{ name = "day-$_"; color = "c5def5"; desc = "Day $_ of Week 1" } }
$depLabel = @{ name = "blocked"; color = "b60205"; desc = "Has an upstream dependency" }

Write-Host "== Creating labels =="
foreach ($l in ($roleLabels + $dayLabels + $depLabel)) {
    gh label create $l.name --repo $repo --color $l.color --description $l.desc --force | Out-Null
}

$issues = @(
    # ---- Day 1 ----
    @{ day = 1; role = "lead"; title = "[Lead] Confirm dentist meeting date and send question list"
       body = "Make the dentist meeting the #1 priority today.`n`n- Confirm a date (target Day 2 or 3)`n- Send the prepared question list (imaging equipment, diagnosis-to-treatment mapping, drug/dosage practice, patient history habits, awareness of Diagnocat/Pearl/Atomica/DentalRx)`n- Confirm who from the team attends`n`n**Why it matters:** Backend and ML work from Day 2 onward depends on the answers (Week1_Execution_Plan.md §5)." },
    @{ day = 1; role = "ml"; title = "[ML] Confirm DENTEX access, clone official repo, read preprocessing code"
       body = "- Confirm Hugging Face access to the full DENTEX dataset (train/validation/test)`n- Clone https://github.com/ibrahimethemhamamci/dentex`n- Read the winning-participant preprocessing / format-conversion code (COCO + YOLO)`n`n**Verify dataset access today** — it is on the Week 1 risk list even though the dataset is known to be public." },
    @{ day = 1; role = "backend"; title = "[Backend] Set up repo structure, lock stack, draft patient record schema v1"
       body = "- Set up the backend/repo directory structure`n- Lock the stack: FastAPI + Supabase (no mid-week revisiting)`n- Draft patient record schema v1: patient, scan, finding, confirmation, recommended vs. confirmed treatment`n`nStack locked in README.md." },
    @{ day = 1; role = "frontend"; title = "[Frontend] Set up React project, component library, review-screen wireframe"
       body = "- Set up the React project and component library`n- Sketch the review-screen wireframe: scan + bounding-box overlay + confirm/reject controls`n- Reuse existing open-source canvas/annotation components — no custom annotation tool (§8)" },
    @{ day = 1; role = "qa"; title = "[QA] Set up shared repo, branching strategy, and project board"
       body = "- Branching strategy documented (CONTRIBUTING.md)`n- Repo README with locked stack`n- GitHub Projects board with every task in Week1_Execution_Plan.md §4 as a ticket`n- All 5 teammates have write access`n`n**This ticket tracks the setup itself.**" },

    # ---- Day 2 ----
    @{ day = 2; role = "lead"; title = "[Lead] Run dentist meeting, record table and drug-list corrections"
       body = "- Run the meeting using the prepared question list`n- Detailed notes on the finding-to-treatment table and the six-drug list`n- Capture the hand-curated contraindication/interaction list for those drugs (this replaces any external interaction API)`n`n**Required output:** corrected finding-to-treatment table, corrected drug list, curated contraindications." },
    @{ day = 2; role = "ml"; title = "[ML] Convert DENTEX to YOLO format; download Tufts and Roboflow sets"
       body = "- Convert DENTEX to YOLO using the official winning-solution scripts`n- Download Tufts Dental Database and the selected Roboflow dental sets`n`nDepends on Day 1 DENTEX access." },
    @{ day = 2; role = "backend"; title = "[Backend] Refine patient record schema; start recommendation engine skeleton"
       body = "- Add fields surfaced by the dentist meeting: allergies, current medications, conditions`n- Start the recommendation engine skeleton`n`nIf the meeting has slipped, proceed with the draft table clearly marked UNVALIDATED (§5)." },
    @{ day = 2; role = "frontend"; title = "[Frontend] Confirmation-screen wireframe; continue review wireframe"
       body = "- Continue the review-screen wireframe`n- Sketch the confirmation-screen wireframe: where treatment recommendations and warnings appear" },
    @{ day = 2; role = "qa"; title = "[QA] Draft first set of synthetic patient profiles (≥5)"
       body = "- At least 5 synthetic profiles covering different ages, allergies, and current medications`n- Must cover all three demo branches: no-drug, drug-no-conflict, drug-with-conflict (≥2 conflict cases)`n- Deliverable: docs/qa/synthetic-patient-profiles.md`n- Synthetic/anonymized data only — no real patient data (§5)" },

    # ---- Day 3 ----
    @{ day = 3; role = "lead"; title = "[Lead] Finalize validated finding-to-treatment table and drug list"
       body = "- Document validated outputs from the dentist meeting`n- Update Project_Context.md / project documentation`n- Hand the validated table to Backend and QA`n`nDay 3 is the backup dentist-meeting day — if the meeting slipped, mark the table UNVALIDATED and keep the team moving (§5)." },
    @{ day = 3; role = "ml"; title = "[ML] Merge datasets in Roboflow; start first YOLO fine-tuning run"
       body = "- Merge DENTEX + Tufts + Roboflow in Roboflow`n- Kick off the first YOLO fine-tuning run; it runs unattended over the following days`n- Accuracy is not expected yet — it only needs to exist (§1)" },
    @{ day = 3; role = "backend"; title = "[Backend] Implement recommendation engine rules + contraindication-check skeleton"
       body = "- Code the rules from the validated finding-to-treatment table`n- Build the contraindication-check logic skeleton`n- Target format for QA's test cases (docs/qa/contraindication-test-cases.md) lands end of Day 3" },
    @{ day = 3; role = "frontend"; title = "[Frontend] Review-screen UI shell with mock bounding boxes"
       body = "- Build the review-screen UI shell`n- Mock bounding boxes standing in for real model output" },
    @{ day = 3; role = "qa"; title = "[QA] Write contraindication test cases for Backend"
       body = "- Categories: known allergy, known drug-drug interaction, age/weight extremes, plus negative controls that must NOT warn`n- Table format: ID | Profile | Input | Expected result | Rationale | Source`n- Deliverable: docs/qa/contraindication-test-cases.md`n- **Hand off to Backend by end of day — their Day 4 depends on it**`n- If the dentist meeting has slipped: mark the whole set UNVALIDATED rather than blocking" },

    # ---- Day 4 ----
    @{ day = 4; role = "ml"; title = "[ML] Check training run; adjust hyperparameters or augmentation"
       body = "- Review early results of the fine-tuning run`n- Adjust hyperparameters / augmentation only if results look off" },
    @{ day = 4; role = "backend"; title = "[Backend] Connect engine to Supabase; run QA test cases and fix failures"
       body = "- Connect the recommendation engine to the Supabase patient record`n- Run it against docs/qa/contraindication-test-cases.md and fix what fails" },
    @{ day = 4; role = "frontend"; title = "[Frontend] Confirmation-screen UI shell wired to mock recommendations"
       body = "- Build the confirmation-screen shell`n- Wire to mock recommendation output: proposed drug, dosage, warning" },
    @{ day = 4; role = "qa"; title = "[QA] Demo script outline + manual test of synthetic profiles"
       body = "- Draft the demo script outline covering the three branches: no-drug, drug-no-conflict, drug-with-conflict`n- Manually test synthetic profiles against the current recommendation logic`n- Deliverables: docs/qa/demo-script-outline.md, docs/qa/manual-test-log.md`n- File issues for every failure found" },
    @{ day = 4; role = "lead"; title = "[Lead] Individual syncs, update risk log, prepare Week 2 handoff"
       body = "- Sync with everyone individually`n- Update the risk log (Week1_Execution_Plan.md §7)`n- Prepare the Week 2 handoff" },

    # ---- Day 5 ----
    @{ day = 5; role = "team"; title = "[Team] End-of-week checkpoint demo"
       body = "- Show the model running inference on one sample scan`n- Show backend rules running against one synthetic profile`n- Show the UI shells — unpolished is fine" },
    @{ day = 5; role = "lead"; title = "[Lead] Record checklist status and confirm Week 2 plan"
       body = "- Record what was and wasn't finished against Week1_Execution_Plan.md §6`n- Confirm the Week 2 plan with the team" },
    @{ day = 5; role = "qa"; title = "[QA] Verify §6 deliverables checklist and log blockers"
       body = "- QA sign-off: verify each End-of-Week 1 checklist item in Week1_Execution_Plan.md §6`n - Shared repo, branching strategy, board in active use`n- Synthetic profiles cover all three demo branches`n- Log open blockers so Monday starts immediately" },
    @{ day = 5; role = "team"; title = "[Team] Log open blockers before the weekend"
       body = "Everyone logs open blockers before the weekend — no re-discovery on Monday. Weekend is an optional buffer only." }
)

$assignees = @{
    ml       = "abdullahtarek4"
    backend  = "Seif-shawky"
    frontend = "Seif-shawky"
}

Write-Host "== Creating issues =="
$existing = gh issue list --repo $repo --state all --limit 200 --json number,title | ConvertFrom-Json
$created = @()
foreach ($i in $issues) {
    if ($existing.title -contains $i.title) {
        Write-Host "  skip (exists): $($i.title)"
        continue
    }
    $labels = ($i.role + ",day-" + $i.day)
    $body = $i.body -replace '\\n', "`n"
    $args = @("issue", "create", "--repo", $repo, "--title", $i.title, "--body", $body, "--label", $labels)
    $owner = $assignees[$i.role]
    if ($owner) { $args += @("--assignee", $owner) }
    $url = & gh @args
    if ($LASTEXITCODE -ne 0) { throw "issue create failed: $($i.title)" }
    Write-Host "  created: $url"
    $created += $url
}

Write-Host "== Creating project board =="
$projectUrl = gh project create --owner sayfeldinn --title "DentalAI — Week 1" 2>$null
if (-not $projectUrl) { $projectUrl = gh project create --owner @me --title "DentalAI — Week 1" }
Write-Host "  board: $projectUrl"

Write-Host "== Adding issues to board =="
$all = gh issue list --repo $repo --state all --limit 200 --json number,title,url | ConvertFrom-Json
foreach ($i in $issues) {
    $item = $all | Where-Object { $_.title -eq $i.title }
    if ($item) {
        gh project item-add --owner sayfeldinn --project (Split-Path $projectUrl -Leaf) --url $item.url 2>$null | Out-Null
    }
}

Write-Host "Done. Assign owners manually: gh issue edit <n> --repo $repo --add-assignee <username>"
