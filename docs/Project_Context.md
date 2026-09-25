# DentalAI

AI-Assisted Diagnostic & Patient History System for Dental Clinics

Project Documentation — IEEE IC-FTAI Student Project Submission

Prepared for: Development Team

This document defines the current scope, architecture, and open questions for the dental AI project, revised for a clinic-facing (B2B) deployment model rather than a direct-to-patient consumer app.

## 1. Executive Summary

DentalAI is a clinical decision-support system for dentists. A patient's panoramic X-ray, taken on equipment the clinic already owns, is analyzed by an AI model that flags possible cavities and other visible issues for the treating dentist's review. Each scan and the dentist's findings are stored in a per-patient history, alongside prescriptions and past treatments, so the dentist has full longitudinal context at every visit.

The system is sold to dental clinics (per-seat or per-scan licensing), not to individual patients. This removes the imaging-hardware budget problem entirely: the clinic already owns the X-ray machine, and our software becomes a layer on top of an existing clinical workflow.

> **Positioning:** This is an assistive second-opinion tool that flags findings for a licensed dentist to confirm or dismiss. It is not an autonomous diagnostic device, and no language in the product or pitch should imply otherwise.

## 2. Problem Statement

## 3. Target Users & Business Model

### 3.1 Target User

Dental clinics and individual dentists in Egypt — not patients directly. The dentist is the buyer and the primary user of the system.

### 3.2 Business Model

> **Scope note:** Competition entry should demonstrate the core assistive-AI + patient-history loop with 1–2 partner clinics. Broader distribution ("as many doctors as we need") is a post-competition growth goal, not something to build or promise during the prototype phase.

## 4. Core Features

### 4.1 X-ray Ingestion

Panoramic X-ray images are transferred from the clinic's existing imaging equipment into the system for analysis. The exact integration path (direct export, manual upload, or a folder-watch import) depends on what equipment and file formats each partner clinic actually uses — see Section 6, Open Questions, before finalizing this module.

### 4.2 AI-Assisted Finding Detection

### 4.3 Patient History Module

### 4.4 Feedback Loop (Active Learning)

When a dentist accepts, rejects, or corrects an AI flag, that decision is logged and can be used to retrain or fine-tune the model over time. This is a meaningful differentiator: the system improves with every participating clinic, which is a genuine data advantage that a generic public model doesn't have.

## 5. System Architecture (Data Flow)

High-level flow from scan capture to updated patient record:

| Layer | Responsibility |
| --- | --- |
| Ingestion layer | Receive/import X-ray images from clinic equipment or manual upload |
| AI inference layer | Run the trained model on incoming scans; return flagged findings + confidence |
| Review interface | Dentist-facing UI to view flags, confirm/reject, add notes and prescriptions |
| Patient record store | Structured storage of scans, confirmed findings, treatments, prescriptions |
| Feedback/training pipeline | Capture dentist corrections to improve the model over time |

## 6. Open Questions to Resolve Before Finalizing Architecture

> **Action required:** These should be answered by talking to at least one real partner clinic before locking in the ingestion design — do not assume the answers.

## 7. Data & Model Considerations

### 7.1 Training Data

For the competition prototype, the model can be trained and validated on public annotated panoramic X-ray datasets (e.g. the DENTEX challenge dataset, the Tufts Dental Database, and various Roboflow dental datasets) rather than requiring proprietary clinic data from day one. A small number of anonymized real scans from a partner clinic can be used for a live demo.

### 7.2 Privacy & Compliance

## 8. Competition Scope vs. Future Roadmap

### 8.1 In scope for the competition prototype

### 8.2 Out of scope for the competition (future roadmap)

## 9. Key Risks

## 10. Summary

The reframed version of this project — an assistive AI + patient history system sold to clinics, rather than a consumer subscription product — is stronger because it removes the imaging-hardware budget problem, has a clearer B2B business model, and creates a real data asset (patient history + feedback loop) that stands on its own even without the AI layer. The main remaining work before development starts is validating the actual clinic imaging workflow with a real partner clinic, and keeping the competition build scoped to a small, working pilot rather than a full production system.

End of document.
