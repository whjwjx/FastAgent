import sys
import os

# Add parent directory to path to import models and services
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.session import SessionLocal
from models.models import Thought
from services.embedding_service import get_embedding
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def backfill():
    db = SessionLocal()
    try:
        # Find thoughts with no embedding
        thoughts = db.query(Thought).filter(Thought.embedding == None, Thought.is_deleted == False).all()
        
        if not thoughts:
            logger.info("No thoughts without embeddings found.")
            return
            
        logger.info(f"Found {len(thoughts)} thoughts to backfill.")
        
        for thought in thoughts:
            logger.info(f"Processing thought ID: {thought.id}")
            embedding = get_embedding(thought.original_content)
            if embedding:
                thought.embedding = embedding
                db.commit()
                logger.info(f"Successfully backfilled thought ID: {thought.id}")
            else:
                logger.warning(f"Failed to get embedding for thought ID: {thought.id}")
                
        logger.info("Backfill complete.")
    except Exception as e:
        logger.error(f"Error during backfill: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    backfill()
