/**
 * Scans page - Upload and list X-ray scans
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { supabase } from '../services/supabase';

export default function Scans() {
  const navigate = useNavigate();
  const [scans, setScans] = useState([]);
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Load scans
      const scansResponse = await api.get('/scans/');
      console.log('Scans response:', scansResponse.data);
      
      // Handle different response formats
      if (scansResponse.data) {
        if (Array.isArray(scansResponse.data)) {
          setScans(scansResponse.data);
        } else if (scansResponse.data.scans && Array.isArray(scansResponse.data.scans)) {
          setScans(scansResponse.data.scans);
        } else {
          setScans([]);
        }
      } else {
        setScans([]);
      }
      
      // Load patients for dropdown
      const patientsResponse = await api.get('/patients/');
      console.log('Patients response:', patientsResponse.data);
      
      // Handle different response formats
      if (patientsResponse.data) {
        if (Array.isArray(patientsResponse.data)) {
          setPatients(patientsResponse.data);
        } else if (patientsResponse.data.patients && Array.isArray(patientsResponse.data.patients)) {
          setPatients(patientsResponse.data.patients);
        } else {
          setPatients([]);
        }
      } else {
        setPatients([]);
      }
    } catch (err) {
      console.error('Error loading data:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load data';
      setError(errorMessage);
      setScans([]);
      setPatients([]);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        setError('Please select an image file');
        return;
      }
      setSelectedFile(file);
      setError('');
    }
  };

  const handleUpload = async () => {
    if (!selectedPatient || !selectedFile) {
      setError('Please select a patient and file');
      return;
    }

    try {
      setUploading(true);
      setError('');

      // Use backend upload endpoint instead of direct Supabase upload
      const formData = new FormData();
      formData.append('file', selectedFile);

      // Upload via backend API with query parameters
      const response = await api.post(
        `/scans/upload?patient_id=${selectedPatient}&scan_type=panoramic`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      console.log('Upload successful:', response.data);

      // Reset form and reload
      setShowUploadModal(false);
      setSelectedPatient('');
      setSelectedFile(null);
      loadData();
      
      alert('X-ray scan uploaded successfully!');
    } catch (err) {
      console.error('Upload error:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to upload scan';
      setError(errorMessage);
    } finally {
      setUploading(false);
    }
  };

  const handleAnalyze = async (scanId) => {
    try {
      // Trigger ML inference
      await api.post(`/ml/infer/${scanId}`);
      
      // Navigate to review screen
      navigate(`/review/${scanId}`);
    } catch (err) {
      console.error('Analysis error:', err);
      setError('Failed to analyze scan');
    }
  };

  const getStatusBadge = (status) => {
    const statusStyles = {
      pending: { bg: '#fef3c7', color: '#92400e', text: 'Pending' },
      processing: { bg: '#dbeafe', color: '#1e40af', text: 'Processing' },
      completed: { bg: '#d1fae5', color: '#065f46', text: 'Completed' },
      reviewed: { bg: '#e0e7ff', color: '#3730a3', text: 'Reviewed' }
    };
    
    const style = statusStyles[status] || statusStyles.pending;
    
    return (
      <span style={{
        padding: '4px 12px',
        backgroundColor: style.bg,
        color: style.color,
        borderRadius: '12px',
        fontSize: '12px',
        fontWeight: '500'
      }}>
        {style.text}
      </span>
    );
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <button onClick={() => navigate('/dashboard')} style={styles.backButton}>
          ← Back to Dashboard
        </button>
        <h1 style={styles.title}>X-Ray Scans</h1>
        <button onClick={() => setShowUploadModal(true)} style={styles.uploadButton}>
          + Upload New Scan
        </button>
      </div>

      {error && (
        <div style={styles.error}>
          {error}
          <button onClick={() => setError('')} style={styles.closeError}>×</button>
        </div>
      )}

      {/* Debug Info */}
      {!loading && (
        <div style={{ padding: '16px', backgroundColor: '#f0f9ff', borderRadius: '4px', marginBottom: '16px', fontSize: '14px' }}>
          <strong>Debug:</strong> Loaded {scans.length} scans and {patients.length} patients. 
          {patients.length === 0 && ' ⚠️ No patients found - add patients first!'}
        </div>
      )}

      {/* Scans List */}
      {loading ? (
        <div style={styles.loading}>Loading scans...</div>
      ) : scans.length === 0 ? (
        <div style={styles.empty}>
          <p>No scans uploaded yet</p>
          <button onClick={() => setShowUploadModal(true)} style={styles.uploadButton}>
            Upload First Scan
          </button>
        </div>
      ) : (
        <div style={styles.grid}>
          {scans.map((scan) => (
            <div key={scan.id} style={styles.card}>
              <img 
                src={scan.image_url} 
                alt="X-ray scan" 
                style={styles.scanImage}
                onError={(e) => {
                  e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2VlZSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LXNpemU9IjE0IiBmaWxsPSIjOTk5IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+SW1hZ2UgTm90IEZvdW5kPC90ZXh0Pjwvc3ZnPg==';
                }}
              />
              
              <div style={styles.cardContent}>
                <div style={styles.cardHeader}>
                  <h3 style={styles.cardTitle}>
                    Scan #{scan.id}
                  </h3>
                  {getStatusBadge(scan.status)}
                </div>
                
                <div style={styles.cardDetails}>
                  <p><strong>Patient:</strong> {scan.patient_name || `Patient #${scan.patient_id}`}</p>
                  <p><strong>Date:</strong> {new Date(scan.created_at).toLocaleDateString()}</p>
                  <p><strong>Type:</strong> {scan.scan_type || 'Panoramic'}</p>
                </div>

                <div style={styles.cardActions}>
                  {scan.status === 'pending' && (
                    <button 
                      onClick={() => handleAnalyze(scan.id)}
                      style={styles.analyzeButton}
                    >
                      🔍 Analyze
                    </button>
                  )}
                  {(scan.status === 'completed' || scan.status === 'reviewed') && (
                    <button 
                      onClick={() => navigate(`/review/${scan.id}`)}
                      style={styles.reviewButton}
                    >
                      👁️ View Results
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <div style={styles.modalOverlay}>
          <div style={styles.modal}>
            <div style={styles.modalHeader}>
              <h2>Upload X-Ray Scan</h2>
              <button 
                onClick={() => {
                  setShowUploadModal(false);
                  setError('');
                  setSelectedFile(null);
                  setSelectedPatient('');
                }}
                style={styles.closeButton}
              >
                ×
              </button>
            </div>

            <div style={styles.modalBody}>
              <div style={styles.formGroup}>
                <label style={styles.label}>Select Patient *</label>
                <select
                  value={selectedPatient}
                  onChange={(e) => setSelectedPatient(e.target.value)}
                  style={styles.select}
                  disabled={uploading}
                >
                  <option value="">-- Select Patient --</option>
                  {patients.length === 0 ? (
                    <option value="" disabled>No patients available. Add a patient first.</option>
                  ) : (
                    patients.map((patient) => (
                      <option key={patient.id} value={patient.id}>
                        {patient.first_name} {patient.last_name} (Age: {patient.age})
                      </option>
                    ))
                  )}
                </select>
                {patients.length === 0 && (
                  <p style={{ color: '#ef4444', fontSize: '12px', marginTop: '4px' }}>
                    No patients found. Please add a patient first from the Patients page.
                  </p>
                )}
              </div>

              <div style={styles.formGroup}>
                <label style={styles.label}>X-Ray Image *</label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileSelect}
                  style={styles.fileInput}
                  disabled={uploading}
                />
                {selectedFile && (
                  <p style={styles.fileName}>Selected: {selectedFile.name}</p>
                )}
              </div>

              {selectedFile && (
                <div style={styles.preview}>
                  <img 
                    src={URL.createObjectURL(selectedFile)} 
                    alt="Preview"
                    style={styles.previewImage}
                  />
                </div>
              )}
            </div>

            <div style={styles.modalFooter}>
              <button
                onClick={() => {
                  setShowUploadModal(false);
                  setError('');
                  setSelectedFile(null);
                  setSelectedPatient('');
                }}
                style={styles.cancelButton}
                disabled={uploading}
              >
                Cancel
              </button>
              <button
                onClick={handleUpload}
                style={styles.submitButton}
                disabled={uploading || !selectedPatient || !selectedFile}
              >
                {uploading ? 'Uploading...' : 'Upload Scan'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
    padding: '32px',
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
  uploadButton: {
    padding: '10px 20px',
    backgroundColor: '#2563eb',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '500',
  },
  error: {
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
  empty: {
    textAlign: 'center',
    padding: '48px',
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
    gap: '24px',
  },
  card: {
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    overflow: 'hidden',
  },
  scanImage: {
    width: '100%',
    height: '200px',
    objectFit: 'cover',
    backgroundColor: '#f0f0f0',
  },
  cardContent: {
    padding: '16px',
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '12px',
  },
  cardTitle: {
    fontSize: '18px',
    margin: 0,
    color: '#333',
  },
  cardDetails: {
    marginBottom: '16px',
    fontSize: '14px',
    color: '#666',
  },
  cardActions: {
    display: 'flex',
    gap: '8px',
  },
  analyzeButton: {
    flex: 1,
    padding: '8px 16px',
    backgroundColor: '#2563eb',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  reviewButton: {
    flex: 1,
    padding: '8px 16px',
    backgroundColor: '#059669',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  modal: {
    backgroundColor: 'white',
    borderRadius: '8px',
    width: '90%',
    maxWidth: '600px',
    maxHeight: '90vh',
    overflow: 'auto',
  },
  modalHeader: {
    padding: '20px',
    borderBottom: '1px solid #e5e7eb',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  closeButton: {
    background: 'none',
    border: 'none',
    fontSize: '28px',
    cursor: 'pointer',
    color: '#666',
    lineHeight: 1,
  },
  modalBody: {
    padding: '20px',
  },
  formGroup: {
    marginBottom: '20px',
  },
  label: {
    display: 'block',
    marginBottom: '8px',
    fontSize: '14px',
    fontWeight: '500',
    color: '#333',
  },
  select: {
    width: '100%',
    padding: '10px',
    border: '1px solid #d1d5db',
    borderRadius: '4px',
    fontSize: '14px',
  },
  fileInput: {
    width: '100%',
    padding: '10px',
    border: '1px solid #d1d5db',
    borderRadius: '4px',
    fontSize: '14px',
  },
  fileName: {
    marginTop: '8px',
    fontSize: '12px',
    color: '#666',
  },
  preview: {
    marginTop: '16px',
    textAlign: 'center',
  },
  previewImage: {
    maxWidth: '100%',
    maxHeight: '300px',
    borderRadius: '4px',
    border: '1px solid #e5e7eb',
  },
  modalFooter: {
    padding: '20px',
    borderTop: '1px solid #e5e7eb',
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '12px',
  },
  cancelButton: {
    padding: '10px 20px',
    backgroundColor: 'white',
    border: '1px solid #d1d5db',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  submitButton: {
    padding: '10px 20px',
    backgroundColor: '#2563eb',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  },
};
