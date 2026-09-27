/**
 * Patients management page - Week 2 Implementation
 * Full CRUD operations for patient records
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { patientAPI } from '../services/api';

export default function Patients() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);

  // Fetch patients on mount
  useEffect(() => {
    fetchPatients();
  }, [searchTerm]);

  const fetchPatients = async () => {
    try {
      setLoading(true);
      const response = await patientAPI.list({ search: searchTerm, page: 1, page_size: 50 });
      setPatients(response.data.patients);
      setError('');
    } catch (err) {
      setError('Failed to load patients');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSignOut = async () => {
    await signOut();
    navigate('/login');
  };

  return (
    <div style={styles.container}>
      {/* Navigation */}
      <nav style={styles.nav}>
        <h1 style={styles.logo}>DentalAI</h1>
        <div style={styles.navRight}>
          <button onClick={() => navigate('/dashboard')} style={styles.backButton}>
            ← Dashboard
          </button>
          <span style={styles.userEmail}>{user?.email}</span>
          <button onClick={handleSignOut} style={styles.signOutButton}>
            Sign Out
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <div style={styles.content}>
        <div style={styles.header}>
          <h2 style={styles.title}>Patients</h2>
          <button 
            onClick={() => setShowAddModal(true)} 
            style={styles.addButton}
          >
            + Add Patient
          </button>
        </div>

        {/* Search */}
        <input
          type="text"
          placeholder="Search patients by name or email..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={styles.searchInput}
        />

        {/* Error Message */}
        {error && (
          <div style={styles.error}>{error}</div>
        )}

        {/* Loading State */}
        {loading ? (
          <div style={styles.loading}>Loading patients...</div>
        ) : (
          <>
            {/* Patients List */}
            {patients.length === 0 ? (
              <div style={styles.emptyState}>
                <p>No patients found.</p>
                <p style={styles.emptyHint}>Click "+ Add Patient" to create your first patient record.</p>
              </div>
            ) : (
              <div style={styles.patientsList}>
                {patients.map((patient) => (
                  <div 
                    key={patient.id} 
                    style={styles.patientCard}
                    onClick={() => navigate(`/patients/${patient.id}`)}
                  >
                    <div style={styles.patientInfo}>
                      <h3 style={styles.patientName}>
                        {patient.first_name} {patient.last_name}
                      </h3>
                      <p style={styles.patientDetail}>
                        📧 {patient.email || 'No email'}
                      </p>
                      <p style={styles.patientDetail}>
                        📞 {patient.phone || 'No phone'}
                      </p>
                      <p style={styles.patientDetail}>
                        🎂 {new Date(patient.date_of_birth).toLocaleDateString()}
                      </p>
                    </div>
                    <div style={styles.patientMeta}>
                      <span style={styles.genderBadge}>
                        {patient.gender}
                      </span>
                      {patient.allergies && patient.allergies.length > 0 && (
                        <span style={styles.allergyBadge}>
                          ⚠️ {patient.allergies.length} allergies
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {/* Add Patient Modal */}
      {showAddModal && (
        <AddPatientModal
          onClose={() => setShowAddModal(false)}
          onSuccess={() => {
            setShowAddModal(false);
            fetchPatients();
          }}
        />
      )}
    </div>
  );
}

// Add Patient Modal Component
function AddPatientModal({ onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    date_of_birth: '',
    gender: 'male',
    phone: '',
    email: '',
    address: '',
    allergies: [],
    current_medications: [],
    medical_conditions: [],
    notes: ''
  });
  const [allergyInput, setAllergyInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await patientAPI.create(formData);
      onSuccess();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create patient');
    } finally {
      setLoading(false);
    }
  };

  const addAllergy = () => {
    if (allergyInput.trim()) {
      setFormData({
        ...formData,
        allergies: [...formData.allergies, allergyInput.trim()]
      });
      setAllergyInput('');
    }
  };

  return (
    <div style={styles.modalOverlay} onClick={onClose}>
      <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
        <h2 style={styles.modalTitle}>Add New Patient</h2>
        
        {error && <div style={styles.error}>{error}</div>}

        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.formRow}>
            <div style={styles.formGroup}>
              <label style={styles.label}>First Name *</label>
              <input
                type="text"
                required
                value={formData.first_name}
                onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                style={styles.input}
              />
            </div>
            <div style={styles.formGroup}>
              <label style={styles.label}>Last Name *</label>
              <input
                type="text"
                required
                value={formData.last_name}
                onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                style={styles.input}
              />
            </div>
          </div>

          <div style={styles.formRow}>
            <div style={styles.formGroup}>
              <label style={styles.label}>Date of Birth *</label>
              <input
                type="date"
                required
                value={formData.date_of_birth}
                onChange={(e) => setFormData({...formData, date_of_birth: e.target.value})}
                style={styles.input}
              />
            </div>
            <div style={styles.formGroup}>
              <label style={styles.label}>Gender *</label>
              <select
                value={formData.gender}
                onChange={(e) => setFormData({...formData, gender: e.target.value})}
                style={styles.input}
              >
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>

          <div style={styles.formRow}>
            <div style={styles.formGroup}>
              <label style={styles.label}>Phone</label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({...formData, phone: e.target.value})}
                style={styles.input}
              />
            </div>
            <div style={styles.formGroup}>
              <label style={styles.label}>Email</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                style={styles.input}
              />
            </div>
          </div>

          <div style={styles.formGroup}>
            <label style={styles.label}>Allergies</label>
            <div style={styles.allergyInput}>
              <input
                type="text"
                value={allergyInput}
                onChange={(e) => setAllergyInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addAllergy())}
                placeholder="Type and press Enter"
                style={{...styles.input, flex: 1}}
              />
              <button type="button" onClick={addAllergy} style={styles.addAllergyBtn}>
                Add
              </button>
            </div>
            {formData.allergies.length > 0 && (
              <div style={styles.allergyList}>
                {formData.allergies.map((allergy, idx) => (
                  <span key={idx} style={styles.allergyTag}>
                    {allergy}
                    <button
                      type="button"
                      onClick={() => setFormData({
                        ...formData,
                        allergies: formData.allergies.filter((_, i) => i !== idx)
                      })}
                      style={styles.removeTag}
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          <div style={styles.formGroup}>
            <label style={styles.label}>Notes</label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({...formData, notes: e.target.value})}
              style={{...styles.input, minHeight: '80px', fontFamily: 'inherit'}}
              placeholder="Additional notes about the patient..."
            />
          </div>

          <div style={styles.modalActions}>
            <button type="button" onClick={onClose} style={styles.cancelButton}>
              Cancel
            </button>
            <button type="submit" disabled={loading} style={styles.submitButton}>
              {loading ? 'Creating...' : 'Create Patient'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
  },
  nav: {
    backgroundColor: 'white',
    padding: '16px 32px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  logo: {
    fontSize: '24px',
    fontWeight: 'bold',
    color: '#2563eb',
    margin: 0,
  },
  navRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  backButton: {
    padding: '8px 16px',
    backgroundColor: '#f3f4f6',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  userEmail: {
    color: '#666',
    fontSize: '14px',
  },
  signOutButton: {
    padding: '8px 16px',
    backgroundColor: '#ef4444',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  content: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '32px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '24px',
  },
  title: {
    fontSize: '32px',
    margin: 0,
    color: '#333',
  },
  addButton: {
    padding: '12px 24px',
    backgroundColor: '#2563eb',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '16px',
    fontWeight: '500',
  },
  searchInput: {
    width: '100%',
    padding: '12px 16px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '16px',
    marginBottom: '24px',
  },
  error: {
    backgroundColor: '#fee',
    color: '#c33',
    padding: '12px',
    borderRadius: '4px',
    marginBottom: '16px',
  },
  loading: {
    textAlign: 'center',
    padding: '48px',
    color: '#666',
  },
  emptyState: {
    textAlign: 'center',
    padding: '64px 32px',
    backgroundColor: 'white',
    borderRadius: '8px',
    color: '#666',
  },
  emptyHint: {
    marginTop: '8px',
    color: '#999',
    fontSize: '14px',
  },
  patientsList: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
    gap: '16px',
  },
  patientCard: {
    backgroundColor: 'white',
    padding: '20px',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    cursor: 'pointer',
    transition: 'transform 0.2s, box-shadow 0.2s',
  },
  patientInfo: {
    marginBottom: '12px',
  },
  patientName: {
    fontSize: '20px',
    marginBottom: '8px',
    color: '#333',
  },
  patientDetail: {
    fontSize: '14px',
    color: '#666',
    margin: '4px 0',
  },
  patientMeta: {
    display: 'flex',
    gap: '8px',
    flexWrap: 'wrap',
  },
  genderBadge: {
    padding: '4px 12px',
    backgroundColor: '#e0e7ff',
    color: '#4338ca',
    borderRadius: '12px',
    fontSize: '12px',
    textTransform: 'capitalize',
  },
  allergyBadge: {
    padding: '4px 12px',
    backgroundColor: '#fef3c7',
    color: '#92400e',
    borderRadius: '12px',
    fontSize: '12px',
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
    padding: '32px',
    borderRadius: '8px',
    maxWidth: '600px',
    width: '90%',
    maxHeight: '90vh',
    overflow: 'auto',
  },
  modalTitle: {
    fontSize: '24px',
    marginBottom: '24px',
    color: '#333',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  formRow: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '16px',
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column',
  },
  label: {
    marginBottom: '8px',
    fontWeight: '500',
    color: '#333',
    fontSize: '14px',
  },
  input: {
    padding: '10px 12px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '14px',
  },
  allergyInput: {
    display: 'flex',
    gap: '8px',
  },
  addAllergyBtn: {
    padding: '10px 20px',
    backgroundColor: '#10b981',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  allergyList: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
    marginTop: '8px',
  },
  allergyTag: {
    padding: '4px 8px',
    backgroundColor: '#fef3c7',
    borderRadius: '4px',
    fontSize: '12px',
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  },
  removeTag: {
    background: 'none',
    border: 'none',
    color: '#92400e',
    cursor: 'pointer',
    fontSize: '16px',
    padding: '0 4px',
  },
  modalActions: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '12px',
    marginTop: '24px',
  },
  cancelButton: {
    padding: '10px 20px',
    backgroundColor: '#f3f4f6',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  submitButton: {
    padding: '10px 20px',
    backgroundColor: '#2563eb',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
};
