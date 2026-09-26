/**
 * Main dashboard page
 */
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Dashboard() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  const handleSignOut = async () => {
    try {
      await signOut();
      navigate('/login');
    } catch (error) {
      console.error('Sign out error:', error);
    }
  };

  return (
    <div style={styles.container}>
      <nav style={styles.nav}>
        <h1 style={styles.logo}>DentalAI</h1>
        <div style={styles.navRight}>
          <span style={styles.userEmail}>{user?.email}</span>
          <button onClick={handleSignOut} style={styles.signOutButton}>
            Sign Out
          </button>
        </div>
      </nav>

      <div style={styles.content}>
        <h2 style={styles.title}>Dashboard</h2>
        
        <div style={styles.grid}>
          <div 
            style={styles.card} 
            onClick={() => navigate('/patients')}
          >
            <h3 style={styles.cardTitle}>📋 Patients</h3>
            <p style={styles.cardDescription}>
              Manage patient records and medical history
            </p>
          </div>

          <div 
            style={styles.card}
            onClick={() => navigate('/scans')}
          >
            <h3 style={styles.cardTitle}>🩻 X-Ray Scans</h3>
            <p style={styles.cardDescription}>
              Upload and review panoramic X-rays
            </p>
          </div>

          <div 
            style={styles.card}
            onClick={() => navigate('/review')}
          >
            <h3 style={styles.cardTitle}>🔍 Review Findings</h3>
            <p style={styles.cardDescription}>
              Review AI-detected findings and confirm diagnoses
            </p>
          </div>

          <div 
            style={styles.card}
            onClick={() => navigate('/treatments')}
          >
            <h3 style={styles.cardTitle}>💊 Treatments</h3>
            <p style={styles.cardDescription}>
              View and manage treatment plans
            </p>
          </div>
        </div>

        <div style={styles.welcomeSection}>
          <h3>Welcome to DentalAI</h3>
          <p>
            This is Week 1 implementation of the AI-assisted diagnostic system.
            Navigate through the sections above to manage patients and scans.
          </p>
          <p style={styles.note}>
            <strong>Note:</strong> The AI model integration will be completed in Week 2-3.
            Currently using mock data for demonstration.
          </p>
        </div>
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
  title: {
    fontSize: '32px',
    marginBottom: '32px',
    color: '#333',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
    gap: '24px',
    marginBottom: '48px',
  },
  card: {
    backgroundColor: 'white',
    padding: '24px',
    borderRadius: '8px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    cursor: 'pointer',
    transition: 'transform 0.2s, box-shadow 0.2s',
  },
  cardTitle: {
    fontSize: '20px',
    marginBottom: '8px',
    color: '#333',
  },
  cardDescription: {
    color: '#666',
    fontSize: '14px',
    lineHeight: '1.5',
  },
  welcomeSection: {
    backgroundColor: 'white',
    padding: '24px',
    borderRadius: '8px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
  },
  note: {
    marginTop: '16px',
    padding: '12px',
    backgroundColor: '#fef3c7',
    borderRadius: '4px',
    fontSize: '14px',
  },
};
