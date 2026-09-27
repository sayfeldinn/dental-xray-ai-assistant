/**
 * Treatment Confirmation page - Show treatment recommendations with drug warnings
 */
import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../services/api';

export default function Treatments() {
  const { scanId } = useParams();
  const navigate = useNavigate();
  
  const [scan, setScan] = useState(null);
  const [patient, setPatient] = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    loadTreatmentData();
  }, [scanId]);

  const loadTreatmentData = async () => {
    try {
      setLoading(true);
      
      // Load scan details
      const scanResponse = await api.get(`/scans/${scanId}`);
      setScan(scanResponse.data);

      // Load patient details
      const patientResponse = await api.get(`/patients/${scanResponse.data.patient_id}`);
      setPatient(patientResponse.data);

      // Load predictions
      const predictionsResponse = await api.get(`/scans/${scanId}/predictions`);
      setPredictions(predictionsResponse.data);

      // Load treatment recommendations
      const recsResponse = await api.get(`/recommendations/${scanId}`);
      setRecommendations(recsResponse.data);

    } catch (err) {
      console.error('Error loading treatment data:', err);
      setError('Failed to load treatment data');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmTreatment = async () => {
    try {
      setConfirming(true);
      
      // In a real app, this would create treatment plans in the database
      for (const rec of recommendations) {
        await api.post('/treatments/', {
          scan_id: scanId,
          patient_id: patient.id,
          finding_type: rec.finding_type,
          treatment_plan: rec.treatment,
          medications: rec.medications,
          status: 'planned'
        });
      }

      alert('Treatment plan confirmed and saved!');
      navigate('/dashboard');
      
    } catch (err) {
      console.error('Error confirming treatment:', err);
      setError('Failed to confirm treatment plan');
    } finally {
      setConfirming(false);
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      low: '#059669',
      medium: '#d97706',
      high: '#dc2626'
    };
    return colors[severity] || colors.low;
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>Loading treatment plan...</div>
      </div>
    );
  }

  if (!scan || !patient) {
    return (
      <div style={styles.container}>
        <div style={styles.error}>Data not found</div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <button onClick={() => navigate(`/review/${scanId}`)} style={styles.backButton}>
          ← Back to Review
        </button>
        <h1 style={styles.title}>Treatment Plan</h1>
        <button 
          onClick={handleConfirmTreatment}
          style={styles.confirmButton}
          disabled={confirming || recommendations.length === 0}
        >
          {confirming ? 'Confirming...' : '✓ Confirm Treatment Plan'}
        </button>
      </div>

      {error && (
        <div style={styles.errorBanner}>
          {error}
          <button onClick={() => setError('')} style={styles.closeError}>×</button>
        </div>
      )}

      <div style={styles.content}>
        {/* Patient Information */}
        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>Patient Information</h2>
          <div style={styles.patientCard}>
            <div style={styles.patientInfo}>
              <div style={styles.infoRow}>
                <span style={styles.label}>Name:</span>
                <span style={styles.value}>
                  {patient.first_name} {patient.last_name}
                </span>
              </div>
              <div style={styles.infoRow}>
                <span style={styles.label}>Age:</span>
                <span style={styles.value}>{patient.age} years</span>
              </div>
              <div style={styles.infoRow}>
                <span style={styles.label}>Gender:</span>
                <span style={styles.value}>{patient.gender}</span>
              </div>
              <div style={styles.infoRow}>
                <span style={styles.label}>Contact:</span>
                <span style={styles.value}>{patient.contact_number || 'N/A'}</span>
              </div>
            </div>

            {/* Medical History Alerts */}
            {patient.medical_history && patient.medical_history.length > 0 && (
              <div style={styles.medicalHistory}>
                <h3 style={styles.subsectionTitle}>⚠️ Medical History & Contraindications</h3>
                <ul style={styles.historyList}>
                  {patient.medical_history.map((condition, idx) => (
                    <li key={idx} style={styles.historyItem}>
                      <strong>{condition.condition}</strong>
                      {condition.contraindications && condition.contraindications.length > 0 && (
                        <div style={styles.contraindications}>
                          <span style={styles.contraindicationLabel}>Avoid:</span>
                          {condition.contraindications.map((drug, drugIdx) => (
                            <span key={drugIdx} style={styles.drugBadge}>
                              {drug}
                            </span>
                          ))}
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {patient.allergies && patient.allergies.length > 0 && (
              <div style={styles.allergies}>
                <h3 style={styles.subsectionTitle}>🚫 Known Allergies</h3>
                <div style={styles.allergyList}>
                  {patient.allergies.map((allergy, idx) => (
                    <span key={idx} style={styles.allergyBadge}>
                      {allergy}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Findings Summary */}
        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>Detected Findings ({predictions.length})</h2>
          <div style={styles.findingsSummary}>
            {predictions.length > 0 ? (
              predictions.map((pred) => (
                <div key={pred.id} style={styles.findingSummaryCard}>
                  <div style={styles.findingSummaryHeader}>
                    <span style={styles.findingName}>{pred.finding_type}</span>
                    <span 
                      style={{
                        ...styles.severityBadge,
                        backgroundColor: getSeverityColor(pred.severity) + '20',
                        color: getSeverityColor(pred.severity)
                      }}
                    >
                      {pred.severity}
                    </span>
                  </div>
                  <div style={styles.findingSummaryDetails}>
                    <span>Tooth #{pred.tooth_number || 'N/A'}</span>
                    <span>•</span>
                    <span>Confidence: {Math.round(pred.confidence * 100)}%</span>
                  </div>
                </div>
              ))
            ) : (
              <p style={styles.noFindings}>No pathologies detected</p>
            )}
          </div>
        </div>

        {/* Treatment Recommendations */}
        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>Recommended Treatments</h2>
          {recommendations.length > 0 ? (
            <div style={styles.recommendationsList}>
              {recommendations.map((rec, idx) => (
                <div key={idx} style={styles.recommendationCard}>
                  <div style={styles.recommendationHeader}>
                    <h3 style={styles.recommendationTitle}>
                      {idx + 1}. Treatment for {rec.finding_type}
                    </h3>
                    <span 
                      style={{
                        ...styles.priorityBadge,
                        backgroundColor: getSeverityColor(rec.severity) + '20',
                        color: getSeverityColor(rec.severity)
                      }}
                    >
                      {rec.severity} Priority
                    </span>
                  </div>

                  <div style={styles.recommendationBody}>
                    <div style={styles.treatmentSection}>
                      <h4 style={styles.treatmentSubheading}>Procedure</h4>
                      <p style={styles.treatmentText}>{rec.treatment}</p>
                    </div>

                    {rec.medications && rec.medications.length > 0 && (
                      <div style={styles.medicationsSection}>
                        <h4 style={styles.treatmentSubheading}>Recommended Medications</h4>
                        <ul style={styles.medicationsList}>
                          {rec.medications.map((med, medIdx) => {
                            // Check for contraindications
                            const hasContraindication = patient.medical_history?.some(
                              condition => condition.contraindications?.includes(med.name)
                            ) || patient.allergies?.includes(med.name);

                            return (
                              <li key={medIdx} style={styles.medicationItem}>
                                <div style={styles.medicationInfo}>
                                  <strong>{med.name}</strong>
                                  <span style={styles.medicationDosage}> - {med.dosage}</span>
                                </div>
                                {hasContraindication && (
                                  <div style={styles.warningBanner}>
                                    ⚠️ WARNING: Contraindicated for this patient!
                                  </div>
                                )}
                              </li>
                            );
                          })}
                        </ul>
                      </div>
                    )}

                    {rec.notes && (
                      <div style={styles.notesSection}>
                        <h4 style={styles.treatmentSubheading}>Additional Notes</h4>
                        <p style={styles.notesText}>{rec.notes}</p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={styles.noRecommendations}>
              <p>No treatment recommendations generated</p>
              <p style={{ fontSize: '14px', color: '#666', marginTop: '8px' }}>
                This may be because no findings were detected or confirmed
              </p>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        {recommendations.length > 0 && (
          <div style={styles.actionsSection}>
            <button
              onClick={() => navigate(`/review/${scanId}`)}
              style={styles.secondaryButton}
            >
              ← Review Findings Again
            </button>
            <button
              onClick={handleConfirmTreatment}
              style={styles.primaryButton}
              disabled={confirming}
            >
              {confirming ? 'Confirming...' : '✓ Confirm & Save Treatment Plan'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
    padding: '24px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '32px',
    flexWrap: 'wrap',
    gap: '16px',
  },
  backButton: {
    padding: '8px 16px',
    backgroundColor: 'white',
    border: '1px solid #ddd',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  title: {
    fontSize: '32px',
    margin: 0,
    color: '#333',
    flex: 1,
    textAlign: 'center',
  },
  confirmButton: {
    padding: '10px 20px',
    backgroundColor: '#059669',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '500',
  },
  errorBanner: {
    backgroundColor: '#fee2e2',
    border: '1px solid #ef4444',
    color: '#991b1b',
    padding: '12px 16px',
    borderRadius: '4px',
    marginBottom: '24px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  closeError: {
    background: 'none',
    border: 'none',
    fontSize: '20px',
    cursor: 'pointer',
    color: '#991b1b',
  },
  loading: {
    textAlign: 'center',
    padding: '48px',
    fontSize: '18px',
    color: '#666',
  },
  error: {
    textAlign: 'center',
    padding: '48px',
    fontSize: '18px',
    color: '#ef4444',
  },
  content: {
    maxWidth: '1200px',
    margin: '0 auto',
  },
  section: {
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '24px',
    marginBottom: '24px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
  },
  sectionTitle: {
    fontSize: '24px',
    marginTop: 0,
    marginBottom: '20px',
    color: '#333',
  },
  patientCard: {
    border: '1px solid #e5e7eb',
    borderRadius: '8px',
    padding: '20px',
  },
  patientInfo: {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '12px',
    marginBottom: '20px',
  },
  infoRow: {
    display: 'flex',
    gap: '8px',
  },
  label: {
    fontWeight: '600',
    color: '#666',
    minWidth: '80px',
  },
  value: {
    color: '#333',
  },
  medicalHistory: {
    marginTop: '20px',
    padding: '16px',
    backgroundColor: '#fef3c7',
    borderRadius: '6px',
    border: '1px solid #fbbf24',
  },
  subsectionTitle: {
    fontSize: '16px',
    marginTop: 0,
    marginBottom: '12px',
    color: '#92400e',
  },
  historyList: {
    margin: 0,
    paddingLeft: '20px',
  },
  historyItem: {
    marginBottom: '12px',
    color: '#78350f',
  },
  contraindications: {
    marginTop: '8px',
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
    alignItems: 'center',
  },
  contraindicationLabel: {
    fontSize: '13px',
    color: '#92400e',
  },
  drugBadge: {
    padding: '4px 8px',
    backgroundColor: '#fecaca',
    color: '#991b1b',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: '500',
  },
  allergies: {
    marginTop: '20px',
    padding: '16px',
    backgroundColor: '#fee2e2',
    borderRadius: '6px',
    border: '1px solid #ef4444',
  },
  allergyList: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
  },
  allergyBadge: {
    padding: '6px 12px',
    backgroundColor: '#fecaca',
    color: '#991b1b',
    borderRadius: '12px',
    fontSize: '13px',
    fontWeight: '500',
  },
  findingsSummary: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
    gap: '16px',
  },
  findingSummaryCard: {
    border: '1px solid #e5e7eb',
    borderRadius: '8px',
    padding: '16px',
  },
  findingSummaryHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px',
  },
  findingName: {
    fontSize: '16px',
    fontWeight: '600',
    color: '#333',
    textTransform: 'capitalize',
  },
  severityBadge: {
    padding: '4px 8px',
    borderRadius: '12px',
    fontSize: '11px',
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  findingSummaryDetails: {
    fontSize: '13px',
    color: '#666',
    display: 'flex',
    gap: '8px',
  },
  noFindings: {
    textAlign: 'center',
    padding: '24px',
    color: '#666',
  },
  recommendationsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  recommendationCard: {
    border: '2px solid #e5e7eb',
    borderRadius: '8px',
    overflow: 'hidden',
  },
  recommendationHeader: {
    backgroundColor: '#f9fafb',
    padding: '16px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottom: '1px solid #e5e7eb',
  },
  recommendationTitle: {
    margin: 0,
    fontSize: '18px',
    color: '#333',
    textTransform: 'capitalize',
  },
  priorityBadge: {
    padding: '6px 12px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  recommendationBody: {
    padding: '20px',
  },
  treatmentSection: {
    marginBottom: '20px',
  },
  treatmentSubheading: {
    fontSize: '15px',
    marginTop: 0,
    marginBottom: '8px',
    color: '#2563eb',
  },
  treatmentText: {
    margin: 0,
    color: '#666',
    lineHeight: '1.6',
  },
  medicationsSection: {
    marginBottom: '20px',
  },
  medicationsList: {
    margin: 0,
    paddingLeft: '20px',
  },
  medicationItem: {
    marginBottom: '12px',
  },
  medicationInfo: {
    color: '#333',
  },
  medicationDosage: {
    color: '#666',
    fontWeight: 'normal',
  },
  warningBanner: {
    marginTop: '6px',
    padding: '8px 12px',
    backgroundColor: '#fee2e2',
    border: '1px solid #ef4444',
    color: '#991b1b',
    borderRadius: '4px',
    fontSize: '13px',
    fontWeight: '600',
  },
  notesSection: {
    padding: '16px',
    backgroundColor: '#f0f9ff',
    borderRadius: '6px',
  },
  notesText: {
    margin: 0,
    color: '#1e40af',
    fontSize: '14px',
    lineHeight: '1.6',
  },
  noRecommendations: {
    textAlign: 'center',
    padding: '48px',
    color: '#666',
  },
  actionsSection: {
    display: 'flex',
    justifyContent: 'center',
    gap: '16px',
    padding: '24px',
  },
  secondaryButton: {
    padding: '12px 24px',
    backgroundColor: 'white',
    border: '1px solid #d1d5db',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '15px',
    fontWeight: '500',
  },
  primaryButton: {
    padding: '12px 32px',
    backgroundColor: '#059669',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '15px',
    fontWeight: '500',
  },
};
