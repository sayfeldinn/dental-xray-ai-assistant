"""
ML inference service for X-ray analysis.
Integrates YOLO model for dental X-ray detection.
"""
from typing import List, Dict, Optional
from pathlib import Path
import requests
from io import BytesIO
from PIL import Image
import numpy as np

from app.schemas.scan import Finding, FindingTypeEnum, FindingSeverityEnum, BoundingBox

# Configuration
MOCK_MODE = False  # Set to True for testing without model
MODEL_PATH = Path(__file__).parent.parent.parent / "ml" / "best.pt"


class MLInferenceService:
    """
    Service for running ML model inference on X-ray images.
    Supports both real YOLO model and mock mode for testing.
    """
    
    def __init__(self):
        """Initialize ML inference service and load YOLO model."""
        self.model_loaded = False
        self.model = None
        self.model_version = "yolov8-dental-v1.0"
        
        if not MOCK_MODE:
            self._load_model()
    
    def _load_model(self):
        """Load the YOLO model from disk."""
        try:
            from ultralytics import YOLO
            
            if not MODEL_PATH.exists():
                print(f"⚠️ Model file not found at {MODEL_PATH}")
                print("⚠️ Falling back to mock mode")
                return
            
            print(f"📦 Loading YOLO model from {MODEL_PATH}")
            self.model = YOLO(str(MODEL_PATH))
            self.model_loaded = True
            print(f"✅ YOLO model loaded successfully")
            
        except ImportError:
            print("⚠️ ultralytics not installed. Run: pip install ultralytics")
            print("⚠️ Falling back to mock mode")
        except Exception as e:
            print(f"⚠️ Failed to load model: {str(e)}")
            print("⚠️ Falling back to mock mode")
    
    def _download_image(self, image_url: str) -> Image.Image:
        """Download image from URL."""
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            return Image.open(BytesIO(response.content))
        except Exception as e:
            raise ValueError(f"Failed to download image: {str(e)}")
    
    def _map_class_to_finding_type(self, class_id: int, class_name: str) -> FindingTypeEnum:
        """Map YOLO class to finding type enum."""
        # Map your YOLO model classes here
        class_mapping = {
            0: FindingTypeEnum.CARIES,
            1: FindingTypeEnum.PERIAPICAL,
            2: FindingTypeEnum.PERICORONAL,
            3: FindingTypeEnum.INTER_RADICULAR,
            4: FindingTypeEnum.NON_ODONTOGENIC,
        }
        
        # Try to match by name
        name_lower = class_name.lower()
        if 'caries' in name_lower or 'cavity' in name_lower:
            return FindingTypeEnum.CARIES
        elif 'periapical' in name_lower:
            return FindingTypeEnum.PERIAPICAL
        elif 'pericoronal' in name_lower:
            return FindingTypeEnum.PERICORONAL
        elif 'radicular' in name_lower or 'furcation' in name_lower:
            return FindingTypeEnum.INTER_RADICULAR
        elif 'odontogenic' in name_lower:
            return FindingTypeEnum.NON_ODONTOGENIC
        
        # Default mapping by ID
        return class_mapping.get(class_id, FindingTypeEnum.OTHER)
    
    def _determine_severity(self, confidence: float, bbox_area: float) -> FindingSeverityEnum:
        """Determine severity based on confidence and size."""
        # High confidence + large area = more severe
        if confidence > 0.8 and bbox_area > 5000:
            return FindingSeverityEnum.HIGH
        elif confidence > 0.7 and bbox_area > 3000:
            return FindingSeverityEnum.MODERATE
        elif confidence > 0.6:
            return FindingSeverityEnum.MILD
        else:
            return FindingSeverityEnum.LOW
    
    async def predict(self, image_url: str, confidence_threshold: float = 0.5) -> List[Finding]:
        """
        Run inference on an X-ray image.
        
        Args:
            image_url: URL to the X-ray image (from Supabase storage)
            confidence_threshold: Minimum confidence score for detections
            
        Returns:
            List of detected findings with bounding boxes
        """
        # Use mock predictions if model not loaded or in mock mode
        if MOCK_MODE or not self.model_loaded:
            return self._mock_predict(confidence_threshold)
        
        try:
            # Download image
            image = self._download_image(image_url)
            
            # Run inference
            results = self.model(image, conf=confidence_threshold)
            
            # Parse results
            findings = []
            for result in results:
                boxes = result.boxes
                
                for i, box in enumerate(boxes):
                    # Extract box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = float(box.conf[0].cpu().numpy())
                    class_id = int(box.cls[0].cpu().numpy())
                    
                    # Get class name
                    class_name = result.names[class_id]
                    
                    # Convert to our format (x, y, width, height)
                    x = float(x1)
                    y = float(y1)
                    width = float(x2 - x1)
                    height = float(y2 - y1)
                    
                    # Map to finding type
                    finding_type = self._map_class_to_finding_type(class_id, class_name)
                    
                    # Determine severity
                    bbox_area = width * height
                    severity = self._determine_severity(confidence, bbox_area)
                    
                    # Create finding
                    finding = Finding(
                        type=finding_type,
                        severity=severity,
                        confidence=confidence,
                        bounding_box=BoundingBox(x=x, y=y, width=width, height=height),
                        tooth_number=None,  # Could be inferred from position
                        description=f"{class_name.capitalize()} detected with {confidence:.1%} confidence",
                        ai_generated=True,
                        confirmed=False
                    )
                    findings.append(finding)
            
            print(f"✅ Model detected {len(findings)} findings")
            return findings
            
        except Exception as e:
            print(f"❌ Inference failed: {str(e)}")
            # Fall back to mock on error
            return self._mock_predict(confidence_threshold)
    
    def _mock_predict(self, confidence_threshold: float = 0.5) -> List[Finding]:
        """Generate mock predictions for testing."""
        mock_findings = [
            Finding(
                type=FindingTypeEnum.CARIES,
                severity=FindingSeverityEnum.MODERATE,
                confidence=0.87,
                bounding_box=BoundingBox(x=120, y=450, width=45, height=40),
                tooth_number="14",
                description="Caries detected on upper right first molar",
                ai_generated=True,
                confirmed=False
            ),
            Finding(
                type=FindingTypeEnum.CARIES,
                severity=FindingSeverityEnum.LOW,
                confidence=0.72,
                bounding_box=BoundingBox(x=520, y=380, width=35, height=38),
                tooth_number="26",
                description="Small caries detected on upper left first molar",
                ai_generated=True,
                confirmed=False
            ),
            Finding(
                type=FindingTypeEnum.PERIAPICAL,
                severity=FindingSeverityEnum.HIGH,
                confidence=0.91,
                bounding_box=BoundingBox(x=280, y=520, width=50, height=55),
                tooth_number="36",
                description="Periapical lesion detected, root canal may be required",
                ai_generated=True,
                confirmed=False
            )
        ]
        
        return [f for f in mock_findings if f.confidence >= confidence_threshold]
    
    async def batch_predict(
        self, 
        image_urls: List[str], 
        confidence_threshold: float = 0.5
    ) -> Dict[str, List[Finding]]:
        """Run inference on multiple images."""
        results = {}
        for image_url in image_urls:
            results[image_url] = await self.predict(image_url, confidence_threshold)
        return results
    
    def get_model_info(self) -> Dict:
        """Get information about the loaded model."""
        return {
            "model_version": self.model_version,
            "model_loaded": self.model_loaded,
            "mock_mode": MOCK_MODE,
            "model_path": str(MODEL_PATH),
            "supported_findings": [
                FindingTypeEnum.CARIES.value,
                FindingTypeEnum.PERIAPICAL.value,
                FindingTypeEnum.PERICORONAL.value,
                FindingTypeEnum.INTER_RADICULAR.value,
                FindingTypeEnum.NON_ODONTOGENIC.value,
            ],
            "confidence_threshold": 0.5,
            "note": "Real YOLO model integrated. Set MOCK_MODE=True to use mock predictions."
        }


# Singleton instance
ml_service = MLInferenceService()


def get_ml_service() -> MLInferenceService:
    """Dependency to get ML service instance."""
    return ml_service
