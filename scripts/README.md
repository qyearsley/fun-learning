# Helper Scripts

This directory contains utility scripts for maintaining and expanding Neural Dive.

## Scripts Overview

### `generate_questions.py`

**Purpose:** Adds new questions to the game's question database.

**What it does:**
1. Reads the existing `neural_dive/data/questions.json`
2. Adds 57 new pre-written questions covering various CS topics
3. Writes the updated questions back to the file
4. Reports statistics about questions added by topic

**When to use:**
- When you want to add the pre-defined set of new questions
- During initial setup or content expansion
- To restore questions if they were accidentally deleted

**Usage:**
```bash
python3 scripts/generate_questions.py
```

**Output:**
```
Loaded 66 existing questions
Total questions after additions: 122
✓ Updated questions.json with 57 new questions

New questions by topic:
  algorithms: 4
  data_structures: 4
  ...
```

**Note:** This script contains a hardcoded set of questions. If you want to add custom questions, edit `neural_dive/data/questions.json` directly following the [Question Guide](../QUESTION_GUIDE.md).

---

### `redistribute_questions.py`

**Purpose:** Assigns questions uniquely to NPCs, ensuring no question appears multiple times.

**What it does:**
1. Reads `neural_dive/data/questions.json` and `neural_dive/data/npcs.json`
2. Organizes questions by topic
3. Assigns 6 questions to each NPC based on their thematic area
4. Ensures **zero overlap** - each question is used by exactly one NPC
5. Updates `npcs.json` with the new assignments
6. Verifies no duplicates exist

**When to use:**
- After adding new questions
- After modifying NPC themes
- When questions are overlapping between NPCs
- During setup or content updates

**Usage:**
```bash
python3 scripts/redistribute_questions.py
```

**Output:**
```
Loaded 122 questions and 23 NPCs

Questions available per topic:
  algorithms: 8
  data_structures: 8
  ...

Assigning questions to NPCs:
  ALGO_SPIRIT: 6 questions (algorithms)
  HEAP_MASTER: 6 questions (data_structures)
  ...

✓ Assigned 111 questions total (no duplicates)
  Unused questions: 11
✓ Verification passed: No duplicate questions!

✓ Updated neural_dive/data/npcs.json
```

**Configuration:**
The script uses a `NPC_THEMES` dictionary to map each NPC to appropriate topics:
```python
NPC_THEMES = {
    'ALGO_SPIRIT': ['algorithms'],
    'HEAP_MASTER': ['data_structures'],
    'WEB_ARCHITECT': ['web_development'],
    ...
}
```

Edit this dictionary in the script to change which topics an NPC should ask about.

---

## Workflow: Adding New Questions

**Step 1: Write Questions**
1. Edit `neural_dive/data/questions.json`
2. Follow the [Question Guide](../QUESTION_GUIDE.md)
3. Add your questions with unique IDs

**Step 2: Redistribute to NPCs**
```bash
python3 scripts/redistribute_questions.py
```

This ensures:
- ✅ Each NPC has unique questions
- ✅ No overlap between NPCs
- ✅ Questions are thematically appropriate

**Step 3: Test In-Game**
```bash
./ndive --fixed --seed 42
```
Fixed positions and seed make testing reproducible.

---

## Common Tasks

### View Question Statistics
```bash
python3 -c "
import json
with open('neural_dive/data/questions.json') as f:
    questions = json.load(f)
print(f'Total questions: {len(questions)}')
"
```

### Check for Duplicate Assignments
```bash
python3 -c "
import json
from collections import Counter

with open('neural_dive/data/npcs.json') as f:
    npcs = json.load(f)

all_questions = []
for npc_data in npcs.values():
    all_questions.extend(npc_data.get('questions', []))

counts = Counter(all_questions)
duplicates = {q: c for q, c in counts.items() if c > 1}

if duplicates:
    print('Duplicates found:')
    for q, count in duplicates.items():
        print(f'  {q}: {count} times')
else:
    print('✓ No duplicates!')
"
```

### List Questions by Topic
```bash
python3 -c "
import json
from collections import defaultdict

with open('neural_dive/data/questions.json') as f:
    questions = json.load(f)

by_topic = defaultdict(list)
for q_id, q_data in questions.items():
    by_topic[q_data['topic']].append(q_id)

for topic in sorted(by_topic.keys()):
    print(f'{topic}: {len(by_topic[topic])} questions')
"
```

---

## Troubleshooting

### "Some NPCs have few questions"
This happens when:
- Not enough questions exist for that topic
- Multiple NPCs share the same topic

**Solution:** Add more questions for that topic in `questions.json`, then run `redistribute_questions.py`.

### "Questions are duplicated between NPCs"
This shouldn't happen after running `redistribute_questions.py`, but if it does:
1. Manually edit `neural_dive/data/npcs.json` to remove duplicates
2. Run `redistribute_questions.py` to fix automatically

### "NPC has wrong questions for their theme"
Edit the `NPC_THEMES` dictionary in `redistribute_questions.py`, then rerun the script.

---

## Advanced: Creating Your Own Script

Want to add questions programmatically? Here's a template:

```python
#!/usr/bin/env python3
import json
from pathlib import Path

# Your new questions
NEW_QUESTIONS = {
    "my_question_id": {
        "question_text": "What is...?",
        "topic": "algorithms",
        "difficulty": "medium",  # optional
        "answers": [
            {"text": "Answer 1", "correct": False, "response": "Not quite!"},
            {"text": "Answer 2", "correct": True, "response": "Correct!", "reward_knowledge": "my_knowledge"},
            {"text": "Answer 3", "correct": False, "response": "That's..."},
            {"text": "Answer 4", "correct": False, "response": "No, because..."}
        ]
    }
}

# Load existing
questions_path = Path("neural_dive/data/questions.json")
with open(questions_path) as f:
    questions = json.load(f)

# Add new
questions.update(NEW_QUESTIONS)

# Save
with open(questions_path, 'w') as f:
    json.dump(questions, f, indent=2)

print(f"Added {len(NEW_QUESTIONS)} questions!")
```

Then run:
```bash
python3 my_script.py
python3 scripts/redistribute_questions.py
```

---

## See Also

- [Question Authoring Guide](../QUESTION_GUIDE.md) - How to write good questions
- [Contributing Guidelines](../CONTRIBUTING.md) - How to contribute to the project
- [Main README](../README.md) - Project overview and setup
