"""
Enhanced Orchestrator Service with Full Pipeline
Includes media generation, validation, and critic scoring.
"""
import uuid
import os
import concurrent.futures
from datetime import datetime
from typing import Optional

from app.core.models import Job, JobStatus, Story, Scene
from app.core.database import get_db_session, DBJob, DBStory, DBScene, DBVideo, DBCriticScore
from app.core.logging import JobLogger, get_logger
from app.core.config import settings
from app.story.adapter import StoryAdapter
from app.media.audio_service import AudioService
from app.media.video_service import VideoService
from app.strategy.shorts_rules import ShortsValidator
from app.critic.service import CriticService

logger = get_logger(__name__)


class OrchestratorService:
    """
    Main orchestrator that coordinates the complete shorts generation pipeline.
    """
    
    def __init__(self):
        self.db = get_db_session()
        self.audio_service = AudioService()
        self.video_service = VideoService()
        self.validator = ShortsValidator()
        self.critic = CriticService()
    
    def create_job(self, request: dict) -> Job:
        """Create a new job from a request."""
        job = Job(
            id=str(uuid.uuid4()),
            status=JobStatus.QUEUED,
            platform=request.get("platform", "youtube_shorts"),
            audience=request.get("audience", "kids_india"),
            duration=request.get("duration", 30),
            genre=request.get("genre", "kids"),
            language=request.get("language", "en-hi"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db_job = DBJob(
            id=job.id,
            status=job.status.value,
            platform=job.platform if isinstance(job.platform, str) else job.platform.value,
            audience=job.audience,
            duration=job.duration,
            genre=job.genre,
            language=job.language,
            created_at=job.created_at,
            updated_at=job.updated_at
        )
        
        self.db.add(db_job)
        self.db.commit()
        
        logger.info(f"Created job {job.id[:8]} - {job.platform}")
        return job
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        db_job = self.db.query(DBJob).filter(DBJob.id == job_id).first()
        if not db_job:
            return None
        
        return Job(
            id=db_job.id,
            status=JobStatus(db_job.status),
            platform=db_job.platform,
            audience=db_job.audience,
            duration=db_job.duration,
            genre=db_job.genre,
            language=db_job.language,
            created_at=db_job.created_at,
            updated_at=db_job.updated_at,
            story_id=db_job.story_id,
            video_url=db_job.video_url,
            error_message=db_job.error_message,
            hook_score=db_job.hook_score,
            pacing_score=db_job.pacing_score,
            loop_score=db_job.loop_score,
            total_score=db_job.total_score,
            retry_count=db_job.retry_count
        )
    
    def update_job_status(self, job_id: str, status: JobStatus, error_message: str = None):
        """Update job status in database."""
        db_job = self.db.query(DBJob).filter(DBJob.id == job_id).first()
        if db_job:
            db_job.status = status.value
            db_job.updated_at = datetime.utcnow()
            if error_message:
                db_job.error_message = error_message
            self.db.commit()
            logger.info(f"Job {job_id[:8]} status → {status.value}")
    
    def update_job_scores(self, job_id: str, scores: dict):
        """Update job critic scores."""
        db_job = self.db.query(DBJob).filter(DBJob.id == job_id).first()
        if db_job:
            db_job.hook_score = scores.get("hook_score")
            db_job.pacing_score = scores.get("pacing_score")
            db_job.loop_score = scores.get("loop_score")
            db_job.total_score = scores.get("total_score")
            self.db.commit()
    
    def save_story(self, story: Story):
        """Save story and its scenes to database."""
        db_story = DBStory(
            id=story.id,
            job_id=story.job_id,
            total_duration=story.total_duration,
            created_at=story.created_at
        )
        self.db.add(db_story)
        
        for scene in story.scenes:
            db_scene = DBScene(
                id=str(uuid.uuid4()),
                story_id=story.id,
                scene_order=scene.id,
                start_sec=scene.start_sec,
                end_sec=scene.end_sec,
                purpose=scene.purpose.value,
                narration_text=scene.narration_text,
                visual_prompt=scene.visual_prompt,
                audio_path=scene.audio_path,
                video_path=scene.video_path
            )
            self.db.add(db_scene)
        
        db_job = self.db.query(DBJob).filter(DBJob.id == story.job_id).first()
        if db_job:
            db_job.story_id = story.id
        
        self.db.commit()
        logger.info(f"Saved story {story.id[:8]} with {len(story.scenes)} scenes")
    
    def save_video(self, job_id: str, video_path: str, duration: int):
        """Save final video metadata."""
        db_video = DBVideo(
            id=str(uuid.uuid4()),
            job_id=job_id,
            storage_url=video_path,
            duration=duration,
            resolution="1080x1920"
        )
        self.db.add(db_video)
        
        db_job = self.db.query(DBJob).filter(DBJob.id == job_id).first()
        if db_job:
            db_job.video_url = video_path
        
        self.db.commit()
    
    def save_critic_score(self, job_id: str, score, platform: str):
        """Save critic score to database."""
        db_score = DBCriticScore(
            id=str(uuid.uuid4()),
            job_id=job_id,
            platform=platform,
            total_score=score.total_score,
            hook_score=score.hook_score,
            pacing_score=score.pacing_score,
            loop_score=score.loop_score,
            verdict=score.verdict,
            feedback=score.feedback
        )
        self.db.add(db_score)
        self.db.commit()
    
    def generate_scene_assets(self, scenes: list, job_id: str):
        """Generate audio for all scenes in parallel."""
        job_logger = JobLogger(job_id)
        
        def process_scene(scene):
            try:
                # Generate audio
                audio_path = str(settings.MEDIA_DIR / f"{job_id[:8]}_scene_{scene.id}_audio.mp3")
                self.audio_service.generate_audio(scene.narration_text, audio_path)
                scene.audio_path = audio_path
                job_logger.info(f"Scene {scene.id} audio ready")
                return scene
            except Exception as e:
                job_logger.error(f"Scene {scene.id} failed: {e}")
                return scene
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(process_scene, scene) for scene in scenes]
            for future in concurrent.futures.as_completed(futures):
                future.result()
    
    def start_job(self, job_id: str) -> bool:
        """
        Execute the complete shorts generation pipeline.
        """
        job_logger = JobLogger(job_id)
        job_logger.info("Starting job execution...")
        
        try:
            # 1. Update status to RUNNING
            self.update_job_status(job_id, JobStatus.RUNNING)
            job = self.get_job(job_id)
            
            if not job:
                job_logger.error("Job not found")
                return False
            
            retry_count = 0
            max_retries = settings.MAX_RETRIES
            story = None
            story_adapter = StoryAdapter(job)  # Initialize once
            
            while retry_count <= max_retries:
                # 2. Generate/Regenerate story
                if retry_count == 0:
                    job_logger.step(1, 6, "Generating intelligent story...")
                    story = story_adapter.generate_story(use_hook_engine=True)
                else:
                    target = self.critic.get_retry_target(score) if 'score' in locals() else None
                    job_logger.warning(f"Retry {retry_count}: Targeting {target or 'full story'}...")
                    
                    if target == "hook_only":
                        story = story_adapter.regenerate_hook_only(story)
                    elif target == "ending_only":
                        story = story_adapter.regenerate_ending_only(story)
                    else:
                        story = story_adapter.generate_story(use_hook_engine=True)

                # 3. Validate shorts rules
                job_logger.step(2, 6, "Validating shorts rules...")
                is_valid, messages = self.validator.validate_all(story.scenes)
                for msg in messages:
                    job_logger.info(msg)
                
                if not is_valid:
                    story.scenes[0] = self.validator.fix_hook(story.scenes[0])
                    story.scenes = self.validator.fix_duration(story.scenes, job.duration)
                
                # 4. Score with critic (Week 2 Enhanced)
                job_logger.step(3, 6, "Scoring content (Week 2)...")
                
                # Pass expected curve ID for alignment check
                curve_id = story_adapter.emotion_curve.id
                score = self.critic.score_content(story, job.platform, expected_curve_id=curve_id)
                
                self.save_critic_score(job_id, score, job.platform)
                self.update_job_scores(job_id, {
                    "hook_score": score.hook_score,
                    "pacing_score": score.pacing_score,
                    "loop_score": score.loop_score,
                    "total_score": score.total_score
                })
                
                if self.critic.should_retry(score) and retry_count < max_retries:
                    retry_count += 1
                    continue
                
                # 5. Memory Storage (Week 2)
                if score.hook_score > 0.85:
                    from app.memory.service import MemoryService
                    memory = MemoryService()
                    # Find hook scene
                    hook_scene = next((s for s in story.scenes if s.purpose == "hook"), None)
                    if hook_scene:
                        memory.store_winning_hook(
                            hook_text=hook_scene.narration_text,
                            hook_type="generated",  # TODO: passthrough type
                            score=score.hook_score,
                            platform=job.platform,
                            visual_prompt=hook_scene.visual_prompt
                        )
                
                break
            
            # 6. Generate media assets
            job_logger.step(5, 6, "Generating audio & video...")
            # Set voice based on persona
            self.audio_service.set_voice(story_adapter.persona.voice_id)
            self.generate_scene_assets(story.scenes, job_id)
            
            # Generate final video (Veo + Stitching)
            video_path = self.video_service.create_shorts_video(story.scenes, job_id, style_prefix="cinematic, 4k")
            self.save_video(job_id, video_path, story.total_duration)

            # 7. Save story and complete
            job_logger.step(6, 6, "Saving results...")
            self.save_story(story)
            
            self.update_job_status(job_id, JobStatus.COMPLETED)
            job_logger.info(f"Job completed with score {score.total_score}")
            return True
            
        except Exception as e:
            job_logger.error(f"Job failed: {str(e)}")
            import traceback
            traceback.print_exc()
            self.update_job_status(job_id, JobStatus.FAILED, str(e))
            return False
    
    def close(self):
        """Close database session."""
        self.db.close()
