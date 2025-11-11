#!/usr/bin/env python3
"""
Script to redistribute questions uniquely to NPCs.
Ensures each NPC has 6-7 unique questions with no overlap.
"""

from collections import defaultdict
import json
from pathlib import Path

# NPC themes mapping - defines which topics each NPC should ask about
NPC_THEMES = {
    # Floor 1 - Basics
    "ALGO_SPIRIT": ["algorithms"],
    "HEAP_MASTER": ["data_structures"],
    "DP_SAGE": ["algorithms", "ai_ml"],  # Secondary specialty
    "PATTERN_ARCHITECT": ["design_patterns"],
    "TEST_ORACLE": ["testing"],
    # Floor 2 - Systems & Web
    "NET_DAEMON": ["networking"],
    "WEB_ARCHITECT": ["web_development"],
    "CRYPTO_GUARDIAN": ["security"],
    "SYSTEM_CORE": ["systems"],
    "COMPILER_SAGE": ["compilers", "programming_fundamentals"],
    "SCALE_MASTER": ["system_design"],
    # Floor 3 - Advanced
    "DB_GUARDIAN": ["databases"],
    "CLOUD_MIND": ["distributed_systems"],
    "SILICON_SAGE": ["systems", "architecture"],
    "THEORY_ORACLE": ["theory"],
    "AI_CONSCIOUSNESS": ["machine_learning"],
    "ML_SAGE": ["machine_learning", "ai_ml"],
    "VIRUS_HUNTER": ["theory", "security"],  # Threatening enemy
    "CODE_AUDITOR": ["software_engineering"],
    "SECURITY_PROBE": ["security"],
    "OPS_COMMANDER": ["devops"],
}


def main():
    # Load data
    base_path = Path(__file__).parent.parent / "neural_dive" / "data"
    questions_path = base_path / "questions.json"
    npcs_path = base_path / "npcs.json"

    with open(questions_path) as f:
        questions = json.load(f)

    with open(npcs_path) as f:
        npcs = json.load(f)

    print(f"Loaded {len(questions)} questions and {len(npcs)} NPCs\n")

    # Organize questions by topic
    questions_by_topic = defaultdict(list)
    for q_id, q_data in questions.items():
        topic = q_data.get("topic", "unknown")
        questions_by_topic[topic].append(q_id)

    print("Questions available per topic:")
    for topic in sorted(questions_by_topic.keys()):
        print(f"  {topic}: {len(questions_by_topic[topic])}")
    print()

    # Track used questions globally
    used_questions = set()

    # Assign questions to each NPC
    npc_assignments = {}
    target_questions_per_npc = 6

    print("Assigning questions to NPCs:")
    for npc_name, themes in NPC_THEMES.items():
        if npc_name not in npcs:
            print(f"  ⚠️  {npc_name} not found in npcs.json, skipping")
            continue

        # Collect available questions for this NPC's themes
        available = []
        for theme in themes:
            theme_questions = questions_by_topic.get(theme, [])
            # Only include questions not yet used
            theme_questions = [q for q in theme_questions if q not in used_questions]
            available.extend(theme_questions)

        # Remove duplicates while preserving order
        available = list(dict.fromkeys(available))

        # Take target number of questions
        assigned = available[:target_questions_per_npc]

        # Mark as used
        used_questions.update(assigned)

        # Store assignment
        npc_assignments[npc_name] = assigned
        npcs[npc_name]["questions"] = assigned

        print(f"  {npc_name}: {len(assigned)} questions ({'/'.join(themes)})")
        if len(assigned) < target_questions_per_npc:
            print(f"    ⚠️  Only found {len(assigned)}/{target_questions_per_npc}")

    print(f"\n✓ Assigned {len(used_questions)} questions total (no duplicates)")
    print(f"  Unused questions: {len(questions) - len(used_questions)}")

    # Verify no duplicates
    all_assigned = []
    for assignments in npc_assignments.values():
        all_assigned.extend(assignments)

    if len(all_assigned) == len(set(all_assigned)):
        print("✓ Verification passed: No duplicate questions!\n")
    else:
        duplicates = len(all_assigned) - len(set(all_assigned))
        print(f"❌ ERROR: Found {duplicates} duplicate assignments!\n")
        return 1

    # Write updated npcs.json
    with open(npcs_path, "w") as f:
        json.dump(npcs, f, indent=2)

    print(f"✓ Updated {npcs_path}")

    # Summary
    print("\n=== SUMMARY ===")
    print(f"Total NPCs with questions: {len(npc_assignments)}")
    print(f"Total unique questions assigned: {len(used_questions)}")
    print(f"Average questions per NPC: {len(used_questions) / len(npc_assignments):.1f}")

    return 0


if __name__ == "__main__":
    exit(main())
