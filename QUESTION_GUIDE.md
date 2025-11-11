# Question Authoring Guide

This guide will help you create high-quality educational questions for Neural Dive.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Question Structure](#question-structure)
3. [Best Practices](#best-practices)
4. [Common Pitfalls](#common-pitfalls)
5. [Difficulty Ratings](#difficulty-ratings)
6. [Examples](#examples)

---

## Quick Start

Questions are stored in `neural_dive/data/questions.json`. Each question has:
- A unique ID (snake_case)
- Question text
- Topic category
- 4 multiple choice answers (1 correct, 3 wrong)
- Optional difficulty rating

**Minimal Example:**
```json
"example_question": {
  "question_text": "What is the time complexity of binary search?",
  "topic": "algorithms",
  "answers": [
    {"text": "O(n)", "correct": false, "response": "Not quite. Binary search is more efficient."},
    {"text": "O(log n)", "correct": true, "response": "Correct! Binary search halves the search space each step.", "reward_knowledge": "binary_search"},
    {"text": "O(n²)", "correct": false, "response": "That's too slow!"},
    {"text": "O(1)", "correct": false, "response": "Only if you're very lucky!"}
  ]
}
```

---

## Question Structure

### Question ID
- Use `snake_case`
- Be descriptive but concise
- Examples: `hash_table_lookup`, `rest_vs_graphql`, `mutex_deadlock`

### Question Text
**✅ DO:**
- Keep it under 100 characters when possible
- Be clear and unambiguous
- Focus on one concept
- Use simple language

**❌ DON'T:**
- Use overly technical jargon without context
- Ask multi-part questions
- Make it too verbose
- Assume specific framework knowledge

**Good Examples:**
- "What is the purpose of a mutex?"
- "Which sorting algorithm is most efficient for nearly-sorted data?"
- "What does the CAP theorem state?"

**Bad Examples:**
- "In the context of distributed systems using eventual consistency with vector clocks, what..." (too complex)
- "What are the differences between REST, GraphQL, and gRPC, and when would you use each?" (multi-part)
- "What does React's useEffect hook do?" (framework-specific)

### Topic Categories

Choose from existing topics or create new ones:
- `algorithms` - Algorithm analysis, complexity
- `data_structures` - Arrays, trees, graphs, etc.
- `systems` - Operating systems, memory, processes
- `networking` - Protocols, HTTP, TCP/IP
- `databases` - SQL, NoSQL, transactions
- `security` - Cryptography, auth, vulnerabilities
- `web_development` - HTTP, REST, APIs
- `distributed_systems` - CAP, consensus, replication
- `machine_learning` - ML concepts, models
- `design_patterns` - Software design patterns
- `testing` - Test strategies, TDD
- `devops` - CI/CD, deployment, monitoring
- `programming_fundamentals` - Basics, paradigms
- `software_engineering` - SOLID, refactoring
- `theory` - Computability, complexity theory

### Answers

Each question must have **exactly 4 answers**.

#### Correct Answer
```json
{
  "text": "O(log n)",
  "correct": true,
  "response": "Correct! Binary search halves the search space.",
  "reward_knowledge": "binary_search"  // Optional
}
```

**Response Guidelines:**
- Start with "Correct!" or "Yes!"
- Explain WHY it's correct in 1-2 sentences
- Keep it under 100 characters
- Be encouraging

**reward_knowledge:** Optional. Grants a knowledge module on correct answer.

#### Wrong Answers
```json
{
  "text": "O(n)",
  "correct": false,
  "response": "Not quite. Binary search is more efficient."
}
```

**Wrong Answer Guidelines:**
- Make them plausible! (common misconceptions)
- Give helpful feedback
- Explain what concept they might be confusing
- Don't be condescending
- Keep responses under 80 characters

**Good wrong answers:**
- Common misconceptions ("O(n)" for binary search)
- Off-by-one concept ("POST" when asking about idempotent methods)
- Related but different ("TCP" when answer is "UDP")
- Extreme values ("O(1)" for something that's O(n))

**Bad wrong answers:**
- Obviously ridiculous ("Purple" as an HTTP method)
- Completely unrelated ("Sorting" when asking about databases)
- Joke answers (keep it professional)

---

## Best Practices

### 1. Focus on Understanding, Not Memorization

**✅ Good:**
```json
"question_text": "Why are B-trees commonly used in databases?",
"answers": [
  {"text": "Minimize disk I/O", "correct": true, ...},
  {"text": "Use less memory", "correct": false, ...},
  ...
]
```

**❌ Bad:**
```json
"question_text": "In what year was the B-tree invented?"
```

### 2. One Clear Right Answer

**✅ Good:**
```json
"question_text": "What time complexity does a hash table provide for average-case lookups?"
// Clear answer: O(1)
```

**❌ Bad:**
```json
"question_text": "Which is the best sorting algorithm?"
// Depends on context!
```

### 3. Balanced Difficulty

Make wrong answers tempting but not misleading:

**✅ Good:**
```json
"question_text": "What does SOLID's Single Responsibility Principle state?",
"answers": [
  {"text": "A class should have one reason to change", "correct": true},
  {"text": "A class should do only one thing", "correct": false}, // Close!
  {"text": "A class should have one method", "correct": false}, // Clearly wrong
  {"text": "A class should inherit from one parent", "correct": false}
]
```

### 4. Inclusive Language

- Avoid gendered pronouns ("they" instead of "he/she")
- Don't assume cultural knowledge
- Use universal examples
- Be respectful and professional

### 5. Appropriate Scope

**✅ Good:**
- Core CS concepts (data structures, algorithms)
- Widely-used technologies (HTTP, SQL, Git)
- Fundamental principles (SOLID, DRY)

**❌ Avoid:**
- Obscure libraries/frameworks
- Version-specific features
- Company-specific terminology
- Cutting-edge research (unless fundamental)

---

## Common Pitfalls

### ❌ Too Specific
```json
"question_text": "In PostgreSQL 14.2, what is the default value of work_mem?"
```
**Problem:** Too specific to one version of one database.

**Better:**
```json
"question_text": "What is the purpose of database query planning?"
```

### ❌ Trick Questions
```json
"question_text": "Is Python compiled or interpreted?"
"answers": [
  {"text": "Interpreted", "correct": false},  // Wait, what?
  {"text": "Both", "correct": true}  // Trick!
]
```
**Problem:** Confusing rather than educational.

### ❌ Requires Outside Knowledge
```json
"question_text": "What does the React useState hook return?"
```
**Problem:** Assumes React experience.

**Better:**
```json
"question_text": "What is the purpose of state in UI frameworks?"
```

### ❌ Multiple Correct Answers
```json
"question_text": "Which data structure provides O(1) access?",
"answers": [
  {"text": "Array", "correct": true},  // True!
  {"text": "Hash Table", "correct": false}  // Also true!
]
```
**Problem:** Ambiguous.

**Better:**
```json
"question_text": "Which data structure provides O(1) indexed access by integer position?"
// Now "Array" is clearly the answer
```

---

## Difficulty Ratings (Optional)

You can add an optional `difficulty` field:

```json
{
  "question_text": "...",
  "topic": "algorithms",
  "difficulty": "medium",  // Optional: easy, medium, hard
  "answers": [...]
}
```

### Difficulty Guidelines

**Easy:**
- Basic definitions
- Simple true/false concepts
- Common knowledge
- Example: "What does HTTP stand for?"

**Medium (default):**
- Requires understanding
- Application of concepts
- Common patterns
- Example: "When should you use a hash table vs. a binary search tree?"

**Hard:**
- Deep understanding required
- Complex scenarios
- Trade-offs and edge cases
- Example: "What are the implications of the CAP theorem for database design?"

---

## Examples

### ✅ Excellent Question
```json
"mutex_purpose": {
  "question_text": "What is the primary purpose of a mutex?",
  "topic": "systems",
  "difficulty": "easy",
  "answers": [
    {
      "text": "Prevent race conditions",
      "correct": true,
      "response": "Correct! Mutexes ensure exclusive access to shared resources.",
      "reward_knowledge": "concurrency"
    },
    {
      "text": "Speed up code execution",
      "correct": false,
      "response": "Mutexes actually add overhead for safety."
    },
    {
      "text": "Allocate memory",
      "correct": false,
      "response": "Memory allocation is separate from synchronization."
    },
    {
      "text": "Handle errors",
      "correct": false,
      "response": "Mutexes are for synchronization, not error handling."
    }
  ]
}
```

**Why it's good:**
- Clear, focused question
- One unambiguous correct answer
- Plausible wrong answers (common misconceptions)
- Helpful, educational responses
- Appropriate difficulty rating

### ❌ Poor Question
```json
"react_question": {
  "question_text": "In React 18, when using Suspense with startTransition, how does useTransition affect the rendering behavior of nested components when combined with useDeferredValue?",
  "topic": "web_development",
  "answers": [...]
}
```

**Problems:**
- Too specific (React 18)
- Too complex (multiple concepts)
- Too long
- Framework-specific
- Requires deep framework knowledge

---

## Testing Your Questions

Before submitting questions, ask yourself:

1. **Can someone answer without Googling?**
   - If they know the concept, yes
   - If they need to look up syntax, no

2. **Is there exactly one right answer?**
   - No ambiguity
   - No "depends on context"

3. **Are the wrong answers helpful?**
   - Do they teach something?
   - Are they common mistakes?

4. **Is it universally relevant?**
   - Not specific to one company/framework/version
   - Applicable to most developers

5. **Would a beginner understand what's being asked?**
   - Clear terminology
   - Focused on one concept

---

## Contributing

To add questions:

1. Edit `neural_dive/data/questions.json`
2. Follow this guide
3. Ensure unique question IDs
4. Run `python3 scripts/redistribute_questions.py` to assign to NPCs
5. Test in-game

For major additions (10+ questions), consider:
- Running `python3 scripts/generate_questions.py` as a template
- Opening an issue first to discuss
- Creating a pull request with explanations

---

## Questions About Questions?

- Check existing questions in `neural_dive/data/questions.json` for examples
- Open an issue on GitHub for clarification
- Refer to this guide when in doubt

**Remember:** Good questions are clear, educational, and fun! 🎮

---

**Quick Checklist:**
- [ ] Question is clear and under 100 chars
- [ ] Topic is appropriate
- [ ] Exactly 4 answers
- [ ] One clear correct answer
- [ ] Wrong answers are plausible
- [ ] Responses are helpful and concise
- [ ] No framework-specific details
- [ ] No trick questions
- [ ] Tested in-game
