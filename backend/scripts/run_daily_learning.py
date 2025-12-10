"""
Daily learning cycle - Run as scheduled task
Discovers patterns, generates questions, updates knowledge base
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from diagnosis.learning_engine import LearningEngine

async def run_daily_learning():
    """Execute daily learning tasks"""
    
    print("\n" + "="*70)
    print(f"🧠 LEARNING CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    engine = LearningEngine()
    
    try:
        # Task 1: Discover patterns from successful sessions
        print("\n📊 Task 1: Pattern Discovery")
        print("-"*70)
        patterns = await engine.discover_new_patterns(lookback_days=7)
        print(f"✅ Discovered {len(patterns)} new pattern candidates")
        
        for p in patterns[:5]:  # Show first 5
            print(f"   - {p['symptom_combination']} → {p['cause']}")
            print(f"     Support: {p['observed_count']}, Success: {p['success_count']}, Confidence: {p['confidence']:.3f}")
        
        # Task 2: Generate new questions
        print("\n❓ Task 2: Question Generation")
        print("-"*70)
        questions = await engine.generate_new_questions(lookback_days=7)
        print(f"✅ Generated {len(questions)} new question candidates")
        
        for q in questions[:3]:  # Show first 3
            print(f"   - {q['question_text']}")
            print(f"     IG estimate: {q['information_gain_estimate']:.3f}, Times helpful: {q['times_helpful']}")
        
        # Task 3: Update question effectiveness
        print("\n📈 Task 3: Question Effectiveness Analysis")
        print("-"*70)
        await engine.update_question_effectiveness()
        print("✅ Updated effectiveness metrics for all questions")
        
        # Task 4: Check pending approvals
        print("\n⏳ Task 4: Pending Approvals")
        print("-"*70)
        pending_count = await engine.get_pending_approval_count()
        print(f"ℹ️ {pending_count} patterns awaiting admin approval")
        
        if pending_count > 0:
            print("   → Login to admin dashboard to review and approve")
        
        # Task 5: Export approved patterns
        print("\n💾 Task 5: Knowledge Base Export")
        print("-"*70)
        export_result = await engine.export_to_json()
        if export_result:
            print("✅ Exported approved patterns to JSON files:")
            print(f"   - {export_result['symptom_mappings_count']} patterns → symptom_mappings.json")
            print(f"   - {export_result['questions_count']} questions → questions.json")
        else:
            print("ℹ️ No new approved patterns to export")
        
        # Summary
        print("\n" + "="*70)
        print("📊 LEARNING CYCLE SUMMARY")
        print("="*70)
        print(f"✅ Pattern candidates: {len(patterns)}")
        print(f"✅ Question candidates: {len(questions)}")
        print(f"⏳ Pending approval: {pending_count}")
        print(f"💾 Exported: {export_result.get('total_exported', 0) if export_result else 0}")
        
        print("\n🎉 Learning cycle completed successfully!")
        
        return {
            "success": True,
            "patterns_discovered": len(patterns),
            "questions_generated": len(questions),
            "pending_approval": pending_count,
            "exported": export_result.get('total_exported', 0) if export_result else 0
        }
        
    except Exception as e:
        print(f"\n❌ Error during learning cycle: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = asyncio.run(run_daily_learning())
    
    # Exit with appropriate code
    sys.exit(0 if result.get("success") else 1)
