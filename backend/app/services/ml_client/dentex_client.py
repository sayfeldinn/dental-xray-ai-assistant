"""
DentalAI - Dentex Week 3 ML Client
HTTP client for communicating with the dentex_week3 AI microservice.
"""

import httpx
from typing import Dict, Any, List
from io import BytesIO
from app.core.config import settings


class DentexClient:
    """Client for dentex_week3 AI inference microservice."""
    
    def __init__(
        self,
        base_url: str = None,
        timeout: int = None
    ):
        """
        Initialize Dentex client.
        
        Args:
            base_url: ML service URL (defaults to settings)
            timeout: Request timeout in seconds (defaults to settings)
        """
        self.base_url = (base_url or settings.ML_SERVICE_URL).rstrip('/')
        self.timeout = timeout or settings.ML_TIMEOUT_SECONDS
        self.default_confidence = settings.ML_DEFAULT_CONFIDENCE
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if ML service is healthy.
        
        Returns:
            Health status response
            
        Raises:
            httpx.HTTPError: If service is unreachable
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/")
            response.raise_for_status()
            return response.json()
    
    async def analyze_scan(
        self,
        image_bytes: bytes,
        filename: str = "scan.jpg",
        confidence_threshold: float = None
    ) -> Dict[str, Any]:
        """
        Send panoramic X-ray to dentex_week3 for analysis.
        
        Args:
            image_bytes: Raw image bytes (JPEG/PNG/WebP)
            filename: Original filename for context
            confidence_threshold: Minimum confidence for detections
        
        Returns:
            Complete ML inference payload including:
            - image_width, image_height
            - quadrants: List of quadrant detections with boxes
            - detections: List of disease detections with tooth associations
            - report: Generated clinical text summary
            - metadata: Model information
            
        Raises:
            httpx.HTTPError: If ML service fails
        """
        confidence = confidence_threshold or self.default_confidence
        
        # Prepare multipart form data
        files = {
            'file': (filename, BytesIO(image_bytes), 'image/jpeg')
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/predict",
                files=files,
                params={'confidence_threshold': confidence}
            )
            response.raise_for_status()
            return response.json()
    
    def parse_detections_to_findings(
        self,
        ml_output: Dict[str, Any],
        scan_id: str,
        patient_id: str
    ) -> List[Dict[str, Any]]:
        """
        Parse dentex_week3 output into Finding records.
        
        Args:
            ml_output: Raw ML service response
            scan_id: UUID of the scan
            patient_id: UUID of the patient
        
        Returns:
            List of finding dictionaries ready for database insertion
        """
        findings = []
        detections = ml_output.get('detections', [])
        
        for detection in detections:
            # Extract tooth information
            quadrant = detection.get('quadrant')
            tooth_id = detection.get('tooth_id')
            tooth_label = detection.get('tooth', '')
            
            # Calculate FDI notation
            if quadrant and tooth_id:
                tooth_fdi = f"{quadrant}{tooth_id}"
            else:
                # Fallback if tooth_id not directly available
                if isinstance(tooth_label, str) and '_' in tooth_label:
                    tooth_num = tooth_label.split('_')[-1]
                    tooth_fdi = f"{quadrant}{tooth_num}" if quadrant else tooth_label
                else:
                    tooth_fdi = str(tooth_label)
            
            # Extract disease information
            disease = detection.get('disease', 'Unknown')
            disease_conf = detection.get('disease_confidence', 0.0)
            tooth_conf = detection.get('tooth_confidence')
            assoc_conf = detection.get('association_confidence')
            
            # Extract bounding box
            box = detection.get('box', [0, 0, 0, 0])
            
            finding = {
                'scan_id': scan_id,
                'patient_id': patient_id,
                'quadrant': quadrant,
                'tooth_id': tooth_id,
                'tooth_fdi': tooth_fdi,
                'disease': disease,
                'disease_confidence': disease_conf,
                'tooth_confidence': tooth_conf,
                'association_confidence': assoc_conf,
                'box': box,
                'review_status': 'pending'
            }
            
            findings.append(finding)
        
        return findings
    
    async def submit_feedback(
        self,
        image_id: str,
        quadrant: int,
        tooth: int,
        original_disease: str,
        is_correct: bool,
        corrected_disease: str = None,
        notes: str = None
    ) -> Dict[str, Any]:
        """
        Submit dentist feedback to ML service for future retraining.
        
        Args:
            image_id: Scan identifier
            quadrant: Tooth quadrant
            tooth: Tooth number
            original_disease: AI predicted disease
            is_correct: Whether AI was correct
            corrected_disease: Dentist's correction if wrong
            notes: Additional feedback notes
        
        Returns:
            Feedback submission confirmation
        """
        payload = {
            'image_id': image_id,
            'quadrant': quadrant,
            'tooth': tooth,
            'original_disease': original_disease,
            'is_correct': is_correct,
            'corrected_disease': corrected_disease,
            'notes': notes
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.base_url}/feedback/finding",
                json=payload
            )
            response.raise_for_status()
            return response.json()


# Global client instance
dentex_client = DentexClient()
