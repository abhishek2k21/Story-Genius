"""
Week 18 Integration Test
Verifies the full "Creator Reality" workflow.
1. Create Brand Kit
2. Generate Preview
3. Edit Script
4. Plan Content Calendar
5. Check Analytics
"""
import sys
import time
from pathlib import Path
from datetime import date, timedelta

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.brand.brand_kit import get_brand_service
from app.preview.service import generate_preview
from app.editor.script_editor import get_script_editor
from app.calendar.service import get_calendar_service
from app.analytics.performance import get_analytics

def test_creator_workflow():
    print("\n" + "="*70)
    print("🚀 WEEK 18 INTEGRATION TEST: Creator Reality")
    print("="*70)
    
    user_id = "test_creator_123"
    
    # 1. Brand Kit
    print("\n[1/5] Creating Brand Kit...")
    brand_service = get_brand_service()
    kit = brand_service.create_kit(
        user_id=user_id,
        name="Tech Insights",
        visual_style="neon_genz",
        intro_template="Welcome to Tech Insights!"
    )
    print(f"  ✅ Kit Created: {kit.name} ({kit.id})")
    print(f"  Style: {kit.visual_style}")
    
    # 2. Preview Generation
    print("\n[2/5] Generating Video Preview...")
    topic = "The spicy history of chili peppers"
    result = generate_preview(
        topic=topic,
        audience_baseline="general_adult",
        brand_kit_id=kit.id,
        num_scenes=3
    )
    preview = result['preview']
    print(f"  ✅ Preview Generated: {preview['topic']}")
    print(f"  Estimated Cost: ${preview['estimated_cost']:.3f}")
    print(f"  Hook Score: {preview['hook_score']}")
    print(f"  Script Preview: {preview['scenes'][0]['script']}")
    
    # 3. Script Editing
    print("\n[3/5] Editing Script...")
    editor = get_script_editor()
    # Save preview to editor (simulate DB Save)
    from app.preview.models import Preview, ScenePreview
    # Reconstruct preview object from dict for editor
    preview_obj = Preview()
    preview_obj.id = preview['id']
    preview_obj.scenes = [ScenePreview(**s) for s in preview['scenes']]
    editor.save_preview(preview_obj)
    
    # Edit scene 0
    new_text = "Wait, chili peppers aren't actually peppers? Let's dive in."
    updated_preview = editor.update_scene_text(preview['id'], 0, new_text)
    print(f"  ✅ Scene 1 Edited: \"{updated_preview.scenes[0].script}\"")
    print(f"  New Duration: {updated_preview.estimated_duration:.1f}s")
    
    # 4. Content Calendar
    print("\n[4/5] Planning Content Calendar...")
    calendar_service = get_calendar_service()
    start_date = date.today()
    end_date = start_date + timedelta(days=7)
    
    plan = calendar_service.create_plan(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        frequency=3,
        themes=["Food History", "Tech Myths", "Space Facts"]
    )
    
    # Assign our preview to the first slot
    first_slot = plan.slots[0]
    calendar_service.update_slot_topic(plan.id, first_slot.id, topic)
    first_slot.preview_id = preview['id']
    
    print(f"  ✅ Plan Created: {len(plan.slots)} slots")
    print(f"  First Slot: {first_slot.date} - {first_slot.theme}")
    print(f"  Topic Assigned: {first_slot.topic}")
    
    # 5. Analytics
    print("\n[5/5] Checking Performance...")
    analytics = get_analytics()
    # Mock some data
    analytics.mock_data_generation(["job_123", "job_456"])
    analytics.record_metrics("job_new", "youtube", views=5000, retention_at_3s=0.85)
    
    insights = analytics.get_insights(user_id)
    top_videos = analytics.get_top_performers(user_id)
    
    print(f"  ✅ Total Views: {insights['total_views']}")
    print(f"  ✅ Top Video Views: {top_videos[0].views}")
    print(f"  Best Hook Type: {insights['best_hook_type']}")
    
    print("\n" + "="*70)
    print("✅ WEEK 18 INTEGRATION TEST PASSED")
    print("="*70)


if __name__ == "__main__":
    test_creator_workflow()
