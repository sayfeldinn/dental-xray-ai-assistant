/**
 * X-ray Review page - View AI predictions with bounding boxes
 */
import { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../services/api';

export default function Review() {
  const { scanId } = useParams();
  const navigate = useNavigate();
  const canvasRef = useRef(null);
  const imageRef = useRef(null);
  
  const [scan, setScan] = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedPrediction, setSelectedPrediction] = useState(null);
  const [showBoundingBoxes, setShowBoundingBoxes] = useState(true);
  const [imageLoaded, setImageLoaded] = useState(false);

  useEffect(() => {
    loadScanData();
  }, [scanId]);

  useEffect(() => {
    if (imageLoaded) {
      drawBoundingBoxes();
    }
  }, [imageLoaded, predictions, showBoundingBoxes, selectedPrediction, scan]);

  const loadScanData = async () => {
    try {
      setLoading(true);
      
      // Load scan details
      const scanResponse = await api.get(`/scans/${scanId}`);
      setScan(scanResponse.data);

      // Load predictions
      const predictionsResponse = await api.get(`/scans/${scanId}/predictions`);
      setPredictions(predictionsResponse.data);

    } catch (err) {
      console.error('Error loading scan data:', err);
      setError('Failed to load scan data');
    } finally {
      setLoading(false);
    }
  };

  const handleImageLoad = () => {
    setImageLoaded(true);
    const canvas = canvasRef.current;
    const image = imageRef.current;
    
    if (canvas && image) {
      canvas.width = image.offsetWidth;
      canvas.height = image.offsetHeight;
    }
  };

  const drawBoundingBoxes = () => {
    const canvas = canvasRef.current;
    const image = imageRef.current;
    
    if (!canvas || !image || !showBoundingBoxes) {
      // Clear canvas if boxes are hidden
      if (canvas) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
      return;
    }

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Scale factors (predictions are in original image coordinates)
    const scaleX = image.offsetWidth / image.naturalWidth;
    const scaleY = image.offsetHeight / image.naturalHeight;

    // Quadrant boxes from the coordinator model, drawn faintly and dashed so
    // they read as context behind the findings rather than as detections.
    (scan?.quadrants || []).forEach((q) => {
      if (!Array.isArray(q.box) || q.box.length !== 4) return;
      const [qx1, qy1, qx2, qy2] = q.box;
      const qx = qx1 * scaleX;
      const qy = qy1 * scaleY;
      const qw = (qx2 - qx1) * scaleX;
      const qh = (qy2 - qy1) * scaleY;

      ctx.save();
      ctx.setLineDash([6, 4]);
      ctx.strokeStyle = 'rgba(107, 114, 128, 0.65)';
      ctx.lineWidth = 1;
      ctx.strokeRect(qx, qy, qw, qh);
      ctx.restore();

      const label = `Q${q.quadrant}`;
      ctx.font = '12px Arial';
      const metrics = ctx.measureText(label);
      ctx.fillStyle = 'rgba(107, 114, 128, 0.8)';
      ctx.fillRect(qx + 2, qy + 2, metrics.width + 8, 16);
      ctx.fillStyle = '#ffffff';
      ctx.fillText(label, qx + 6, qy + 14);
    });

    predictions.forEach((pred) => {
      const isSelected = selectedPrediction?.id === pred.id;
      
      // Scale bounding box coordinates
      const x = pred.bbox_x * scaleX;
      const y = pred.bbox_y * scaleY;
      const width = pred.bbox_width * scaleX;
      const height = pred.bbox_height * scaleY;

      // Draw bounding box
      ctx.strokeStyle = isSelected ? '#ef4444' : '#2563eb';
      ctx.lineWidth = isSelected ? 3 : 2;
      ctx.strokeRect(x, y, width, height);

      // Draw semi-transparent fill
      ctx.fillStyle = isSelected ? 'rgba(239, 68, 68, 0.1)' : 'rgba(37, 99, 235, 0.1)';
      ctx.fillRect(x, y, width, height);

      // Draw label
      const label = `${pred.finding_type} (${Math.round(pred.confidence * 100)}%)`;
      ctx.font = '14px Arial';
      ctx.fillStyle = isSelected ? '#ef4444' : '#2563eb';
      
      // Label background
      const textMetrics = ctx.measureText(label);
      const textHeight = 20;
      ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
      ctx.fillRect(x, y - textHeight, textMetrics.width + 8, textHeight);
      
      // Label text
      ctx.fillStyle = isSelected ? '#ef4444' : '#2563eb';
      ctx.fillText(label, x + 4, y - 5);
    });
  };

  const handleCorrection = async (predictionId, isCorrect) => {
    try {
      await api.post('/feedback/', {
        prediction_id: predictionId,
        scan_id: scanId,
        is_correct: isCorrect,
        corrected_by: 'dentist' // In real app, use actual user ID
      });

      // Reload predictions to show updated status
      loadScanData();
      
      alert(isCorrect ? 'Marked as correct' : 'Correction logged');
    } catch (err) {
      console.error('Error logging correction:', err);
      setError('Failed to log correction');
    }
  };

  const handleConfirmAll = async () => {
    try {
      // Confirm all predictions
      for (const pred of predictions) {
        await handleCorrection(pred.id, true);
      }

      // Navigate to treatment confirmation
      navigate(`/treatments/${scanId}`);
    } catch (err) {
      console.error('Error confirming predictions:', err);
      setError('Failed to confirm predictions');
    }
  };

  const getSeverityBadge = (severity) => {
    const styles = {
      low: { bg: '#d1fae5', color: '#065f46', text: 'Low' },
      medium: { bg: '#fef3c7', color: '#92400e', text: 'Medium' },
      high: { bg: '#fee2e2', color: '#991b1b', text: 'High' }
    };
    
    const style = styles[severity] || styles.low;
    
    return (
      <span style={{
        padding: '4px 8px',
        backgroundColor: style.bg,
        color: style.color,
        borderRadius: '12px',
        fontSize: '11px',
        fontWeight: '500'
      }}>
        {style.text}
      </span>
    );
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>Loading scan data...</div>
      </div>
    );
  }

  if (!scan) {
    return (
      <div style={styles.container}>
        <div style={styles.error}>Scan not found</div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <button onClick={() => navigate('/scans')} style={styles.backButton}>
          ← Back to Scans
        </button>
        <h1 style={styles.title}>X-Ray Review - Scan #{scanId}</h1>
        <button 
          onClick={handleConfirmAll}
          style={styles.confirmButton}
          disabled={predictions.length === 0}
        >
          ✓ Confirm All & Continue
        </button>
      </div>

      {error && (
        <div style={styles.errorBanner}>
          {error}
          <button onClick={() => setError('')} style={styles.closeError}>×</button>
        </div>
      )}

      <div style={styles.content}>
        {/* Image Viewer */}
        <div style={styles.imageSection}>
          <div style={styles.imageHeader}>
            <h3>X-Ray Image</h3>
            <label style={styles.checkbox}>
              <input
                type="checkbox"
                checked={showBoundingBoxes}
                onChange={(e) => setShowBoundingBoxes(e.target.checked)}
              />
              <span style={{ marginLeft: '8px' }}>Show Bounding Boxes</span>
            </label>
          </div>

          <div style={styles.imageContainer}>
            <img
              ref={imageRef}
              src={scan.image_url}
              alt="X-ray scan"
              style={styles.xrayImage}
              onLoad={handleImageLoad}
              onError={(e) => {
                e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAwIiBoZWlnaHQ9IjYwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iODAwIiBoZWlnaHQ9IjYwMCIgZmlsbD0iI2VlZSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LXNpemU9IjE4IiBmaWxsPSIjOTk5IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+SW1hZ2UgTm90IEZvdW5kPC90ZXh0Pjwvc3ZnPg==';
              }}
            />
            <canvas
              ref={canvasRef}
              style={styles.canvas}
            />
          </div>

          {predictions.length === 0 && (
            <div style={styles.noFindings}>
              <p>No findings detected in this X-ray</p>
            </div>
          )}
        </div>

        {/* Findings List */}
        <div style={styles.findingsSection}>
          <h3 style={styles.findingsTitle}>
            AI-Detected Findings ({predictions.length})
          </h3>

          {scan.ai_report && (
            <div style={styles.reportCard}>
              <div style={styles.reportHeader}>
                <span style={styles.reportBadge}>AI-generated</span>
                <span style={styles.reportHint}>
                  Draft for review — not a diagnosis
                </span>
              </div>
              <p style={styles.reportText}>{scan.ai_report}</p>
            </div>
          )}

          {predictions.length > 0 ? (
            <div style={styles.findingsList}>
              {predictions.map((pred) => (
                <div
                  key={pred.id}
                  style={{
                    ...styles.findingCard,
                    ...(selectedPrediction?.id === pred.id ? styles.findingCardSelected : {})
                  }}
                  onClick={() => setSelectedPrediction(pred)}
                >
                  <div style={styles.findingHeader}>
                    <h4 style={styles.findingType}>{pred.finding_type}</h4>
                    {getSeverityBadge(pred.severity)}
                  </div>

                  <div style={styles.findingDetails}>
                    <p><strong>Confidence:</strong> {Math.round(pred.confidence * 100)}%</p>
                    <p><strong>Location:</strong> Tooth #{pred.tooth_number || 'N/A'}</p>
                    {pred.notes && (
                      <p style={styles.notes}>{pred.notes}</p>
                    )}
                  </div>

                  <div style={styles.findingActions}>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCorrection(pred.id, true);
                      }}
                      style={styles.correctButton}
                    >
                      ✓ Correct
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCorrection(pred.id, false);
                      }}
                      style={styles.incorrectButton}
                    >
                      ✗ Incorrect
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={styles.emptyFindings}>
              <p>No pathologies detected</p>
              <p style={{ fontSize: '14px', color: '#666', marginTop: '8px' }}>
                The AI analysis found no concerning findings in this X-ray
              </p>
            </div>
          )}

          {predictions.length > 0 && (
            <div style={styles.instructions}>
              <p><strong>Instructions:</strong></p>
              <ul style={styles.instructionsList}>
                <li>Click on a finding to highlight it on the image</li>
                <li>Mark each finding as correct or incorrect</li>
                <li>Once reviewed, click "Confirm All & Continue" to proceed to treatment</li>
              </ul>
            </div>
          )}
        </div>
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
    marginBottom: '24px',
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
    fontSize: '28px',
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
    display: 'grid',
    gridTemplateColumns: '2fr 1fr',
    gap: '24px',
    alignItems: 'start',
  },
  imageSection: {
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '20px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
  },
  imageHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
  },
  checkbox: {
    display: 'flex',
    alignItems: 'center',
    fontSize: '14px',
    cursor: 'pointer',
  },
  imageContainer: {
    position: 'relative',
    width: '100%',
    backgroundColor: '#000',
    borderRadius: '4px',
    overflow: 'hidden',
  },
  xrayImage: {
    width: '100%',
    height: 'auto',
    display: 'block',
  },
  canvas: {
    position: 'absolute',
    top: 0,
    left: 0,
    pointerEvents: 'none',
  },
  noFindings: {
    textAlign: 'center',
    padding: '24px',
    color: '#666',
  },
  findingsSection: {
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '20px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    maxHeight: 'calc(100vh - 200px)',
    overflow: 'auto',
  },
  findingsTitle: {
    margin: '0 0 16px 0',
    fontSize: '20px',
    color: '#333',
  },
  reportCard: {
    backgroundColor: '#f8fafc',
    border: '1px solid #e2e8f0',
    borderLeft: '3px solid #2563eb',
    borderRadius: '6px',
    padding: '14px 16px',
    marginBottom: '20px',
  },
  reportHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '10px',
    flexWrap: 'wrap',
  },
  reportBadge: {
    backgroundColor: '#dbeafe',
    color: '#1e40af',
    borderRadius: '10px',
    padding: '2px 8px',
    fontSize: '11px',
    fontWeight: '600',
  },
  reportHint: {
    fontSize: '11px',
    color: '#94a3b8',
    fontStyle: 'italic',
  },
  reportText: {
    margin: 0,
    fontSize: '13px',
    lineHeight: 1.6,
    color: '#334155',
    whiteSpace: 'pre-wrap',
  },
  findingsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  findingCard: {
    border: '2px solid #e5e7eb',
    borderRadius: '8px',
    padding: '16px',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  findingCardSelected: {
    borderColor: '#ef4444',
    backgroundColor: '#fef2f2',
  },
  findingHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '12px',
  },
  findingType: {
    margin: 0,
    fontSize: '16px',
    color: '#333',
    textTransform: 'capitalize',
  },
  findingDetails: {
    fontSize: '14px',
    color: '#666',
    marginBottom: '12px',
  },
  notes: {
    marginTop: '8px',
    fontStyle: 'italic',
    color: '#888',
  },
  findingActions: {
    display: 'flex',
    gap: '8px',
  },
  correctButton: {
    flex: 1,
    padding: '6px 12px',
    backgroundColor: '#059669',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '13px',
  },
  incorrectButton: {
    flex: 1,
    padding: '6px 12px',
    backgroundColor: '#ef4444',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '13px',
  },
  emptyFindings: {
    textAlign: 'center',
    padding: '32px',
    color: '#666',
  },
  instructions: {
    marginTop: '24px',
    padding: '16px',
    backgroundColor: '#f0f9ff',
    borderRadius: '4px',
    fontSize: '14px',
    color: '#1e40af',
  },
  instructionsList: {
    marginTop: '8px',
    marginBottom: 0,
    paddingLeft: '20px',
  },
};
