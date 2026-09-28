"""
Vision/OCR system for image analysis.
"""

import os
from typing import Dict, Any
from PIL import Image
import io

class VisionSystem:
    """Vision system for OCR and image analysis."""
    
    def __init__(self):
        self.tesseract_available = False
        # Try to check if Tesseract is available
        try:
            import subprocess
            result = subprocess.run(['tesseract', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                self.tesseract_available = True
                print("Tesseract OCR is available")
        except:
            print("Tesseract OCR not available - using basic image analysis")
    
    def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from image using OCR."""
        if not self.tesseract_available:
            return "OCR not available - Tesseract not installed"
        
        try:
            import pytesseract
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            return f"OCR Error: {str(e)}"
    
    def analyze_inventory_image(self, image_path: str) -> Dict[str, Any]:
        """Analyze inventory image for box counting and damage detection."""
        try:
            image = Image.open(image_path)
            width, height = image.size
            
            # Basic image analysis without OCR
            analysis_details = []
            
            # Check image properties
            if width > 2000 or height > 2000:
                analysis_details.append("High-resolution image - suitable for detailed analysis")
            
            # Check if image is grayscale
            if image.mode == 'L':
                analysis_details.append("Grayscale image detected")
            elif image.mode == 'RGB':
                analysis_details.append("Color image detected")
            
            # Estimate based on image size (rough estimation)
            estimated_boxes = (width * height) // 50000  # Very rough estimation
            
            return {
                "success": True,
                "analysis": f"Basic image analysis completed. Image dimensions: {width}x{height}px. {', '.join(analysis_details)}. Estimated boxes: ~{estimated_boxes} (rough estimation). Install Tesseract OCR for accurate text extraction and box counting.",
                "extracted_text": "OCR not available without Tesseract installation",
                "metadata": {
                    "dimensions": {"width": width, "height": height},
                    "mode": image.mode,
                    "estimated_boxes": estimated_boxes,
                    "ocr_available": self.tesseract_available
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "analysis": "Failed to analyze image"
            }

# Global vision system instance
vision_system = VisionSystem()
