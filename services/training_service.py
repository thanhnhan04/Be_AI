"""
Training Service - Orchestrate model training pipeline
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

MODELS_DIR = Path("models")
METADATA_FILE = MODELS_DIR / "training_metadata.json"


class TrainingService:
    """Service để quản lý training pipeline"""
    
    def __init__(self):
        self.training_status = "idle"  # idle, preprocessing, training, completed, failed
        self.last_training = None
        self._load_metadata()
    
    def _load_metadata(self):
        """Load training metadata từ file"""
        try:
            if METADATA_FILE.exists():
                with open(METADATA_FILE, 'r') as f:
                    metadata = json.load(f)
                    self.last_training = metadata
        except Exception as e:
            logger.warning(f"Could not load metadata: {e}")
    
    def _save_metadata(self, metadata: Dict):
        """Save training metadata"""
        try:
            MODELS_DIR.mkdir(exist_ok=True)
            with open(METADATA_FILE, 'w') as f:
                json.dump(metadata, f, indent=2)
            self.last_training = metadata
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    async def run_preprocessing(self) -> Dict:
        """
        Chạy preprocessing: MongoDB → CSV
        Step 2 trong flow
        """
        if self.training_status == "preprocessing":
            return {"status": "error", "message": "Preprocessing already running"}
        
        self.training_status = "preprocessing"
        
        try:
            logger.info("Starting preprocessing...")
            
            # Run preprocessing script
            result = subprocess.run(
                [sys.executable, "scripts/preprocess_interactions.py"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                self.training_status = "idle"
                return {
                    "status": "success",
                    "message": "Preprocessing completed",
                    "output": result.stdout,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                self.training_status = "failed"
                return {
                    "status": "error",
                    "message": "Preprocessing failed",
                    "error": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            self.training_status = "failed"
            return {
                "status": "error",
                "message": "Preprocessing timeout (>5 minutes)"
            }
        except Exception as e:
            self.training_status = "failed"
            logger.error(f"Preprocessing error: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def run_training(self) -> Dict:
        """
        Chạy model training
        Steps 3-5 trong flow: Label encoding → Train ALS → Save model
        """
        if self.training_status == "training":
            return {"status": "error", "message": "Training already running"}
        
        self.training_status = "training"
        
        try:
            logger.info("Starting model training...")
            
            # Run training script
            result = subprocess.run(
                [sys.executable, "scripts/train_als_model.py"],
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )
            
            if result.returncode == 0:
                self.training_status = "completed"
                
                # Parse metrics từ output (nếu có)
                metadata = {
                    "status": "success",
                    "trained_at": datetime.utcnow().isoformat(),
                    "output": result.stdout
                }
                self._save_metadata(metadata)
                
                return metadata
            else:
                self.training_status = "failed"
                return {
                    "status": "error",
                    "message": "Training failed",
                    "error": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            self.training_status = "failed"
            return {
                "status": "error",
                "message": "Training timeout (>30 minutes)"
            }
        except Exception as e:
            self.training_status = "failed"
            logger.error(f"Training error: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def run_full_pipeline(self) -> Dict:
        """
        Chạy full pipeline: Preprocessing → Training
        """
        logger.info("Starting full training pipeline...")
        
        # Step 1: Preprocessing
        preprocess_result = await self.run_preprocessing()
        if preprocess_result['status'] != 'success':
            return {
                "status": "error",
                "step": "preprocessing",
                "details": preprocess_result
            }
        
        # Step 2: Training
        training_result = await self.run_training()
        if training_result['status'] != 'success':
            return {
                "status": "error",
                "step": "training",
                "details": training_result
            }
        
        return {
            "status": "success",
            "message": "Full pipeline completed successfully",
            "preprocessing": preprocess_result,
            "training": training_result
        }
    
    def get_status(self) -> Dict:
        """Get current training status"""
        return {
            "current_status": self.training_status,
            "last_training": self.last_training
        }
    
    def get_metrics(self) -> Optional[Dict]:
        """Get training metrics từ metadata"""
        if self.last_training and self.last_training.get('status') == 'success':
            return {
                "trained_at": self.last_training.get('trained_at'),
                "output": self.last_training.get('output', '')
            }
        return None


# Singleton instance
training_service = TrainingService()
