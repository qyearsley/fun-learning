#!/usr/bin/env python3
"""
Script to generate new questions and redistribute them uniquely to NPCs.
This ensures each NPC has its own unique set of questions with no overlap.
"""

import json
from pathlib import Path

# New questions to add
NEW_QUESTIONS = {
    # More algorithms questions
    "merge_sort": {
        "question_text": "What is the space complexity of merge sort?",
        "topic": "algorithms",
        "answers": [
            {
                "text": "O(1)",
                "correct": False,
                "response": "Merge sort requires additional space for merging.",
            },
            {
                "text": "O(log n)",
                "correct": False,
                "response": "Not quite. Think about the auxiliary space needed.",
            },
            {
                "text": "O(n)",
                "correct": True,
                "response": "Correct! Merge sort needs O(n) auxiliary space.",
                "reward_knowledge": "merge_sort",
            },
            {
                "text": "O(n²)",
                "correct": False,
                "response": "Too much! Merge sort is more space-efficient than that.",
            },
        ],
    },
    "bfs_vs_dfs": {
        "question_text": "Which graph traversal guarantees finding the shortest path in an unweighted graph?",
        "topic": "algorithms",
        "answers": [
            {
                "text": "Depth-First Search",
                "correct": False,
                "response": "DFS explores as deep as possible first.",
            },
            {
                "text": "Breadth-First Search",
                "correct": True,
                "response": "Correct! BFS explores level by level, finding shortest paths.",
                "reward_knowledge": "graph_traversal",
            },
            {
                "text": "Both are equivalent",
                "correct": False,
                "response": "They have different properties!",
            },
            {
                "text": "Neither guarantees it",
                "correct": False,
                "response": "One of them does guarantee it.",
            },
        ],
    },
    "greedy_algorithms": {
        "question_text": "Which problem can be solved optimally using a greedy algorithm?",
        "topic": "algorithms",
        "answers": [
            {
                "text": "0/1 Knapsack",
                "correct": False,
                "response": "0/1 Knapsack requires dynamic programming.",
            },
            {
                "text": "Traveling Salesman",
                "correct": False,
                "response": "TSP is NP-hard, greedy doesn't guarantee optimal.",
            },
            {
                "text": "Huffman Coding",
                "correct": True,
                "response": "Yes! Huffman coding is a classic greedy algorithm.",
                "reward_knowledge": "greedy",
            },
            {
                "text": "Longest Common Subsequence",
                "correct": False,
                "response": "LCS needs dynamic programming.",
            },
        ],
    },
    "amortized_analysis": {
        "question_text": "What does amortized time complexity measure?",
        "topic": "algorithms",
        "answers": [
            {
                "text": "Worst case only",
                "correct": False,
                "response": "Amortized analysis considers sequences of operations.",
            },
            {
                "text": "Best case only",
                "correct": False,
                "response": "No, it's about average over sequences.",
            },
            {
                "text": "Average over sequence",
                "correct": True,
                "response": "Correct! Amortized analysis averages cost over operation sequences.",
                "reward_knowledge": "amortized",
            },
            {
                "text": "Space complexity",
                "correct": False,
                "response": "Amortized analysis is about time, not space.",
            },
        ],
    },
    # More data structures questions
    "trie_usage": {
        "question_text": "What is a trie (prefix tree) best used for?",
        "topic": "data_structures",
        "answers": [
            {
                "text": "Sorting numbers",
                "correct": False,
                "response": "Tries are not typically used for sorting.",
            },
            {
                "text": "String prefix matching",
                "correct": True,
                "response": "Perfect! Tries excel at prefix-based string operations.",
                "reward_knowledge": "trie",
            },
            {
                "text": "Graph traversal",
                "correct": False,
                "response": "Tries are tree structures, not graphs.",
            },
            {
                "text": "Random access",
                "correct": False,
                "response": "Arrays are better for random access.",
            },
        ],
    },
    "bloom_filter": {
        "question_text": "What is a key characteristic of a Bloom filter?",
        "topic": "data_structures",
        "answers": [
            {
                "text": "No false positives",
                "correct": False,
                "response": "Bloom filters can have false positives!",
            },
            {
                "text": "No false negatives",
                "correct": True,
                "response": "Correct! Bloom filters never have false negatives.",
                "reward_knowledge": "bloom_filter",
            },
            {
                "text": "Perfect accuracy",
                "correct": False,
                "response": "Bloom filters trade accuracy for space efficiency.",
            },
            {"text": "Slow lookups", "correct": False, "response": "Bloom filters are very fast!"},
        ],
    },
    "skip_list": {
        "question_text": "What is the expected time complexity of search in a skip list?",
        "topic": "data_structures",
        "answers": [
            {"text": "O(1)", "correct": False, "response": "Not quite that fast!"},
            {
                "text": "O(log n)",
                "correct": True,
                "response": "Correct! Skip lists provide O(log n) expected search time.",
                "reward_knowledge": "skip_list",
            },
            {
                "text": "O(n)",
                "correct": False,
                "response": "Skip lists are faster than linear search.",
            },
            {
                "text": "O(n log n)",
                "correct": False,
                "response": "Too slow for a search operation.",
            },
        ],
    },
    "b_tree": {
        "question_text": "Why are B-trees commonly used in databases?",
        "topic": "data_structures",
        "answers": [
            {
                "text": "They use less memory",
                "correct": False,
                "response": "Memory isn't the primary reason.",
            },
            {
                "text": "Minimize disk I/O",
                "correct": True,
                "response": "Yes! B-trees minimize expensive disk operations.",
                "reward_knowledge": "b_tree",
            },
            {
                "text": "Faster than hash tables",
                "correct": False,
                "response": "Hash tables are faster for exact matches.",
            },
            {
                "text": "Easier to implement",
                "correct": False,
                "response": "B-trees are actually complex to implement!",
            },
        ],
    },
    # More theory questions
    "chomsky_hierarchy": {
        "question_text": "In the Chomsky hierarchy, which languages can a finite automaton recognize?",
        "topic": "theory",
        "answers": [
            {
                "text": "Regular languages",
                "correct": True,
                "response": "Correct! Finite automata recognize regular languages.",
                "reward_knowledge": "chomsky",
            },
            {
                "text": "Context-free languages",
                "correct": False,
                "response": "Context-free needs push-down automata.",
            },
            {
                "text": "All languages",
                "correct": False,
                "response": "Finite automata are limited in power.",
            },
            {
                "text": "No languages",
                "correct": False,
                "response": "They can recognize regular languages!",
            },
        ],
    },
    "rice_theorem": {
        "question_text": "What does Rice's Theorem state?",
        "topic": "theory",
        "answers": [
            {
                "text": "All problems are decidable",
                "correct": False,
                "response": "Many problems are undecidable!",
            },
            {
                "text": "Non-trivial properties of programs are undecidable",
                "correct": True,
                "response": "Correct! Rice's Theorem is fundamental to computability.",
                "reward_knowledge": "rice",
            },
            {
                "text": "P = NP",
                "correct": False,
                "response": "Rice's Theorem doesn't address P vs NP.",
            },
            {
                "text": "All algorithms terminate",
                "correct": False,
                "response": "The halting problem shows this is undecidable.",
            },
        ],
    },
    "reduction": {
        "question_text": "In complexity theory, what does a reduction prove?",
        "topic": "theory",
        "answers": [
            {
                "text": "A problem is easy",
                "correct": False,
                "response": "Reductions often prove hardness!",
            },
            {
                "text": "Relative difficulty",
                "correct": True,
                "response": "Yes! Reductions show one problem is at least as hard as another.",
                "reward_knowledge": "reduction",
            },
            {
                "text": "Problems are identical",
                "correct": False,
                "response": "Reductions show relationships, not equivalence.",
            },
            {
                "text": "Algorithms are optimal",
                "correct": False,
                "response": "Reductions are about problem hardness.",
            },
        ],
    },
    "space_hierarchy": {
        "question_text": "What does the Space Hierarchy Theorem state?",
        "topic": "theory",
        "answers": [
            {
                "text": "All space bounds are equivalent",
                "correct": False,
                "response": "Different space bounds have different power!",
            },
            {
                "text": "More space = more problems solvable",
                "correct": True,
                "response": "Correct! More space enables solving harder problems.",
                "reward_knowledge": "space_hierarchy",
            },
            {
                "text": "Space and time are identical",
                "correct": False,
                "response": "Space and time are related but distinct.",
            },
            {
                "text": "Constant space solves everything",
                "correct": False,
                "response": "Many problems require more space.",
            },
        ],
    },
    # More ML questions
    "batch_normalization": {
        "question_text": "What is the primary benefit of batch normalization?",
        "topic": "machine_learning",
        "answers": [
            {
                "text": "Reduces model size",
                "correct": False,
                "response": "Batch norm doesn't reduce model size.",
            },
            {
                "text": "Stabilizes training",
                "correct": True,
                "response": "Yes! Batch norm reduces internal covariate shift.",
                "reward_knowledge": "batch_norm",
            },
            {
                "text": "Prevents all overfitting",
                "correct": False,
                "response": "It helps but doesn't prevent all overfitting.",
            },
            {
                "text": "Eliminates need for activation",
                "correct": False,
                "response": "Activation functions are still needed!",
            },
        ],
    },
    "dropout": {
        "question_text": "How does dropout regularization work?",
        "topic": "machine_learning",
        "answers": [
            {
                "text": "Removes layers",
                "correct": False,
                "response": "Dropout doesn't remove entire layers.",
            },
            {
                "text": "Randomly drops neurons during training",
                "correct": True,
                "response": "Correct! Dropout randomly deactivates neurons.",
                "reward_knowledge": "dropout",
            },
            {
                "text": "Reduces learning rate",
                "correct": False,
                "response": "That's a different technique.",
            },
            {
                "text": "Adds noise to inputs",
                "correct": False,
                "response": "Dropout affects neurons, not inputs directly.",
            },
        ],
    },
    "learning_rate_schedule": {
        "question_text": "Why use a learning rate schedule?",
        "topic": "machine_learning",
        "answers": [
            {
                "text": "Speeds up training only",
                "correct": False,
                "response": "It's about convergence quality too.",
            },
            {
                "text": "Helps converge to better minima",
                "correct": True,
                "response": "Yes! Schedules help escape local minima and converge better.",
                "reward_knowledge": "lr_schedule",
            },
            {
                "text": "Prevents underfitting",
                "correct": False,
                "response": "Schedules don't directly address underfitting.",
            },
            {
                "text": "Reduces model size",
                "correct": False,
                "response": "Learning rate doesn't affect model size.",
            },
        ],
    },
    "bias_variance_tradeoff": {
        "question_text": "What happens when model complexity increases?",
        "topic": "machine_learning",
        "answers": [
            {
                "text": "Bias increases, variance decreases",
                "correct": False,
                "response": "It's the opposite!",
            },
            {
                "text": "Bias decreases, variance increases",
                "correct": True,
                "response": "Correct! This is the bias-variance tradeoff.",
                "reward_knowledge": "bias_variance",
            },
            {
                "text": "Both increase",
                "correct": False,
                "response": "They move in opposite directions.",
            },
            {
                "text": "Both decrease",
                "correct": False,
                "response": "That would be ideal but doesn't happen!",
            },
        ],
    },
    # More web development questions
    "cors": {
        "question_text": "What does CORS (Cross-Origin Resource Sharing) control?",
        "topic": "web_development",
        "answers": [
            {
                "text": "Server performance",
                "correct": False,
                "response": "CORS is about security, not performance.",
            },
            {
                "text": "Cross-domain requests",
                "correct": True,
                "response": "Correct! CORS controls which domains can access resources.",
                "reward_knowledge": "cors",
            },
            {
                "text": "CSS styling",
                "correct": False,
                "response": "CORS has nothing to do with styling!",
            },
            {
                "text": "Database access",
                "correct": False,
                "response": "CORS is a browser security feature.",
            },
        ],
    },
    "jwt": {
        "question_text": "What is a key advantage of JWT (JSON Web Tokens)?",
        "topic": "web_development",
        "answers": [
            {
                "text": "Server must store session",
                "correct": False,
                "response": "JWT is stateless - no server storage!",
            },
            {
                "text": "Stateless authentication",
                "correct": True,
                "response": "Yes! JWTs enable stateless, scalable auth.",
                "reward_knowledge": "jwt",
            },
            {
                "text": "Better encryption",
                "correct": False,
                "response": "JWTs are signed, not necessarily encrypted.",
            },
            {
                "text": "Smaller than cookies",
                "correct": False,
                "response": "JWTs are actually larger than session cookies!",
            },
        ],
    },
    "graphql_vs_rest": {
        "question_text": "What is a main advantage of GraphQL over REST?",
        "topic": "web_development",
        "answers": [
            {
                "text": "Always faster",
                "correct": False,
                "response": "Speed depends on implementation.",
            },
            {
                "text": "Client specifies exact data needed",
                "correct": True,
                "response": "Correct! GraphQL eliminates over/under-fetching.",
                "reward_knowledge": "graphql",
            },
            {
                "text": "No need for a schema",
                "correct": False,
                "response": "GraphQL requires a strict schema!",
            },
            {
                "text": "Better security",
                "correct": False,
                "response": "Security depends on implementation.",
            },
        ],
    },
    "websockets": {
        "question_text": "When should you use WebSockets instead of HTTP?",
        "topic": "web_development",
        "answers": [
            {
                "text": "All web applications",
                "correct": False,
                "response": "WebSockets are for specific use cases.",
            },
            {
                "text": "Real-time bidirectional communication",
                "correct": True,
                "response": "Yes! WebSockets excel at real-time data.",
                "reward_knowledge": "websockets",
            },
            {
                "text": "File uploads",
                "correct": False,
                "response": "HTTP handles file uploads fine.",
            },
            {
                "text": "Static websites",
                "correct": False,
                "response": "Static sites don't need WebSockets!",
            },
        ],
    },
    # More networking questions
    "cdn": {
        "question_text": "What is the primary purpose of a CDN (Content Delivery Network)?",
        "topic": "networking",
        "answers": [
            {
                "text": "Reduce server costs",
                "correct": False,
                "response": "Cost isn't the primary benefit.",
            },
            {
                "text": "Reduce latency via geographic distribution",
                "correct": True,
                "response": "Correct! CDNs cache content closer to users.",
                "reward_knowledge": "cdn",
            },
            {
                "text": "Increase security",
                "correct": False,
                "response": "Security is a side benefit, not the main purpose.",
            },
            {
                "text": "Compress files",
                "correct": False,
                "response": "Compression can happen but isn't the main purpose.",
            },
        ],
    },
    "nat": {
        "question_text": "What does NAT (Network Address Translation) do?",
        "topic": "networking",
        "answers": [
            {
                "text": "Encrypts traffic",
                "correct": False,
                "response": "NAT doesn't provide encryption.",
            },
            {
                "text": "Maps private IPs to public IPs",
                "correct": True,
                "response": "Correct! NAT enables private networks to share public IPs.",
                "reward_knowledge": "nat",
            },
            {
                "text": "Speeds up routing",
                "correct": False,
                "response": "NAT can actually add overhead.",
            },
            {
                "text": "Replaces DNS",
                "correct": False,
                "response": "NAT and DNS serve different purposes.",
            },
        ],
    },
    "load_balancer_algorithms": {
        "question_text": "Which load balancing algorithm considers server load?",
        "topic": "networking",
        "answers": [
            {
                "text": "Round Robin",
                "correct": False,
                "response": "Round Robin distributes blindly.",
            },
            {"text": "Random", "correct": False, "response": "Random doesn't consider load."},
            {
                "text": "Least Connections",
                "correct": True,
                "response": "Yes! Least Connections routes to least busy server.",
                "reward_knowledge": "load_balancing",
            },
            {
                "text": "IP Hash",
                "correct": False,
                "response": "IP Hash ensures session affinity, not load balancing.",
            },
        ],
    },
    # More security questions
    "sql_injection": {
        "question_text": "How can you prevent SQL injection attacks?",
        "topic": "security",
        "answers": [
            {
                "text": "Use string concatenation",
                "correct": False,
                "response": "String concat enables injection!",
            },
            {
                "text": "Use parameterized queries",
                "correct": True,
                "response": "Correct! Parameterized queries prevent injection.",
                "reward_knowledge": "sql_injection",
            },
            {
                "text": "Disable error messages",
                "correct": False,
                "response": "Hiding errors doesn't prevent injection.",
            },
            {
                "text": "Use GET instead of POST",
                "correct": False,
                "response": "HTTP method doesn't prevent injection!",
            },
        ],
    },
    "csrf": {
        "question_text": "What does a CSRF token protect against?",
        "topic": "security",
        "answers": [
            {"text": "XSS attacks", "correct": False, "response": "CSRF tokens don't prevent XSS."},
            {
                "text": "Cross-Site Request Forgery",
                "correct": True,
                "response": "Correct! CSRF tokens validate request origin.",
                "reward_knowledge": "csrf",
            },
            {
                "text": "SQL injection",
                "correct": False,
                "response": "SQL injection requires different defenses.",
            },
            {
                "text": "DDoS attacks",
                "correct": False,
                "response": "CSRF tokens don't help with DDoS.",
            },
        ],
    },
    "oauth2": {
        "question_text": "What is OAuth 2.0 primarily used for?",
        "topic": "security",
        "answers": [
            {
                "text": "Password encryption",
                "correct": False,
                "response": "OAuth doesn't handle password encryption.",
            },
            {
                "text": "Delegated authorization",
                "correct": True,
                "response": "Yes! OAuth enables third-party access without sharing passwords.",
                "reward_knowledge": "oauth",
            },
            {
                "text": "Data encryption",
                "correct": False,
                "response": "OAuth is for authorization, not encryption.",
            },
            {"text": "DNS security", "correct": False, "response": "OAuth isn't related to DNS."},
        ],
    },
    "zero_trust": {
        "question_text": "What is the core principle of Zero Trust security?",
        "topic": "security",
        "answers": [
            {
                "text": "Trust the network perimeter",
                "correct": False,
                "response": "Zero Trust doesn't trust the perimeter!",
            },
            {
                "text": "Never trust, always verify",
                "correct": True,
                "response": "Correct! Zero Trust verifies every request.",
                "reward_knowledge": "zero_trust",
            },
            {
                "text": "Trust internal users",
                "correct": False,
                "response": "Zero Trust doesn't assume trust.",
            },
            {
                "text": "No authentication needed",
                "correct": False,
                "response": "Zero Trust requires strong authentication!",
            },
        ],
    },
    # More systems questions
    "virtual_memory": {
        "question_text": "What is the primary benefit of virtual memory?",
        "topic": "systems",
        "answers": [
            {
                "text": "Faster execution",
                "correct": False,
                "response": "Virtual memory can actually slow things down.",
            },
            {
                "text": "Isolation and larger address space",
                "correct": True,
                "response": "Correct! Virtual memory provides isolation and apparent memory size.",
                "reward_knowledge": "virtual_memory",
            },
            {
                "text": "Better graphics",
                "correct": False,
                "response": "Graphics use VRAM, different concept.",
            },
            {
                "text": "Network performance",
                "correct": False,
                "response": "Virtual memory is about RAM, not networking.",
            },
        ],
    },
    "context_switch": {
        "question_text": "What happens during a context switch?",
        "topic": "systems",
        "answers": [
            {"text": "CPU is destroyed", "correct": False, "response": "The CPU isn't damaged!"},
            {
                "text": "Process state is saved and restored",
                "correct": True,
                "response": "Yes! Context switches save/restore CPU state.",
                "reward_knowledge": "context_switch",
            },
            {
                "text": "Memory is cleared",
                "correct": False,
                "response": "Memory persists across context switches.",
            },
            {"text": "New OS is loaded", "correct": False, "response": "The OS stays the same!"},
        ],
    },
    "page_replacement": {
        "question_text": "Which page replacement algorithm is optimal but impractical?",
        "topic": "systems",
        "answers": [
            {"text": "FIFO", "correct": False, "response": "FIFO is practical but not optimal."},
            {
                "text": "LRU",
                "correct": False,
                "response": "LRU is practical and good, but not optimal.",
            },
            {
                "text": "Optimal (Bélády's)",
                "correct": True,
                "response": "Correct! Optimal requires knowing the future.",
                "reward_knowledge": "page_replacement",
            },
            {"text": "Random", "correct": False, "response": "Random is definitely not optimal!"},
        ],
    },
    "scheduler_types": {
        "question_text": "Which scheduling algorithm can cause starvation?",
        "topic": "systems",
        "answers": [
            {
                "text": "Round Robin",
                "correct": False,
                "response": "Round Robin is fair and prevents starvation.",
            },
            {
                "text": "Priority Scheduling",
                "correct": True,
                "response": "Yes! Low-priority processes can starve.",
                "reward_knowledge": "scheduling",
            },
            {"text": "FCFS", "correct": False, "response": "FCFS eventually serves everyone."},
            {
                "text": "Lottery Scheduling",
                "correct": False,
                "response": "Lottery scheduling prevents starvation.",
            },
        ],
    },
    # More distributed systems questions
    "eventual_consistency": {
        "question_text": "What does eventual consistency guarantee?",
        "topic": "distributed_systems",
        "answers": [
            {
                "text": "Immediate consistency",
                "correct": False,
                "response": "That's strong consistency!",
            },
            {
                "text": "Consistency after bounded time",
                "correct": True,
                "response": "Correct! Eventually all replicas will be consistent.",
                "reward_knowledge": "eventual_consistency",
            },
            {
                "text": "No consistency guarantee",
                "correct": False,
                "response": "There is a guarantee, just not immediate.",
            },
            {
                "text": "Perfect consistency always",
                "correct": False,
                "response": "That's not achievable in distributed systems!",
            },
        ],
    },
    "consensus": {
        "question_text": "What problem does the Paxos algorithm solve?",
        "topic": "distributed_systems",
        "answers": [
            {"text": "Sorting", "correct": False, "response": "Paxos isn't about sorting!"},
            {
                "text": "Distributed consensus",
                "correct": True,
                "response": "Yes! Paxos enables agreement in distributed systems.",
                "reward_knowledge": "paxos",
            },
            {
                "text": "Encryption",
                "correct": False,
                "response": "Paxos doesn't handle encryption.",
            },
            {
                "text": "Load balancing",
                "correct": False,
                "response": "Paxos is about consensus, not balancing.",
            },
        ],
    },
    "vector_clocks": {
        "question_text": "What do vector clocks help determine?",
        "topic": "distributed_systems",
        "answers": [
            {
                "text": "Absolute time",
                "correct": False,
                "response": "Vector clocks don't provide absolute time.",
            },
            {
                "text": "Causal ordering of events",
                "correct": True,
                "response": "Correct! Vector clocks track causality.",
                "reward_knowledge": "vector_clocks",
            },
            {
                "text": "Server load",
                "correct": False,
                "response": "Vector clocks aren't about load.",
            },
            {
                "text": "Network speed",
                "correct": False,
                "response": "Vector clocks track logical time, not speed.",
            },
        ],
    },
    "quorum": {
        "question_text": "In a quorum-based system, what determines consistency?",
        "topic": "distributed_systems",
        "answers": [
            {
                "text": "Single server",
                "correct": False,
                "response": "Quorums need multiple servers!",
            },
            {
                "text": "Read + Write quorum > N",
                "correct": True,
                "response": "Yes! Overlapping quorums ensure consistency.",
                "reward_knowledge": "quorum",
            },
            {
                "text": "All servers must agree",
                "correct": False,
                "response": "Quorums need majority, not all.",
            },
            {
                "text": "Random selection",
                "correct": False,
                "response": "Quorums are deterministic!",
            },
        ],
    },
    # More devops questions
    "infrastructure_as_code": {
        "question_text": "What is a benefit of Infrastructure as Code (IaC)?",
        "topic": "devops",
        "answers": [
            {
                "text": "Manual is better",
                "correct": False,
                "response": "Automation is a key benefit!",
            },
            {
                "text": "Reproducible infrastructure",
                "correct": True,
                "response": "Yes! IaC enables consistent deployments.",
                "reward_knowledge": "iac",
            },
            {
                "text": "Slower deployments",
                "correct": False,
                "response": "IaC actually speeds up deployments!",
            },
            {
                "text": "No version control",
                "correct": False,
                "response": "IaC enables versioning infrastructure!",
            },
        ],
    },
    "blue_green_deployment": {
        "question_text": "What is blue-green deployment?",
        "topic": "devops",
        "answers": [
            {
                "text": "Color-coded servers",
                "correct": False,
                "response": "It's not about actual colors!",
            },
            {
                "text": "Two identical environments for zero-downtime",
                "correct": True,
                "response": "Correct! Blue-green enables instant switchover.",
                "reward_knowledge": "blue_green",
            },
            {
                "text": "Slow gradual rollout",
                "correct": False,
                "response": "That's more like canary deployment.",
            },
            {
                "text": "Backup strategy only",
                "correct": False,
                "response": "It's a deployment strategy!",
            },
        ],
    },
    "monitoring_vs_observability": {
        "question_text": "What is the key difference between monitoring and observability?",
        "topic": "devops",
        "answers": [
            {
                "text": "They're identical",
                "correct": False,
                "response": "They serve different purposes!",
            },
            {
                "text": "Observability enables understanding unknown unknowns",
                "correct": True,
                "response": "Yes! Observability lets you explore unexpected issues.",
                "reward_knowledge": "observability",
            },
            {"text": "Monitoring is newer", "correct": False, "response": "Monitoring came first!"},
            {
                "text": "Observability is cheaper",
                "correct": False,
                "response": "Cost isn't the main distinction.",
            },
        ],
    },
    "circuit_breaker": {
        "question_text": "What does the circuit breaker pattern prevent?",
        "topic": "devops",
        "answers": [
            {
                "text": "Electrical failures",
                "correct": False,
                "response": "It's a software pattern!",
            },
            {
                "text": "Cascading failures",
                "correct": True,
                "response": "Correct! Circuit breakers stop failure propagation.",
                "reward_knowledge": "circuit_breaker",
            },
            {
                "text": "Security breaches",
                "correct": False,
                "response": "Circuit breakers are about resilience.",
            },
            {
                "text": "Memory leaks",
                "correct": False,
                "response": "Not the purpose of circuit breakers.",
            },
        ],
    },
    # More design patterns questions
    "decorator_pattern": {
        "question_text": "What does the Decorator pattern do?",
        "topic": "design_patterns",
        "answers": [
            {
                "text": "Makes code pretty",
                "correct": False,
                "response": "It's not about aesthetics!",
            },
            {
                "text": "Adds behavior dynamically",
                "correct": True,
                "response": "Yes! Decorators wrap objects with new functionality.",
                "reward_knowledge": "decorator",
            },
            {
                "text": "Removes functionality",
                "correct": False,
                "response": "Decorators add, not remove.",
            },
            {
                "text": "Compiles code",
                "correct": False,
                "response": "Decorators are runtime, not compile-time.",
            },
        ],
    },
    "adapter_pattern": {
        "question_text": "When should you use the Adapter pattern?",
        "topic": "design_patterns",
        "answers": [
            {
                "text": "When interfaces are compatible",
                "correct": False,
                "response": "Adapters are for incompatible interfaces!",
            },
            {
                "text": "To make incompatible interfaces work together",
                "correct": True,
                "response": "Correct! Adapters bridge incompatible interfaces.",
                "reward_knowledge": "adapter",
            },
            {
                "text": "To speed up code",
                "correct": False,
                "response": "Adapters don't improve performance.",
            },
            {
                "text": "For database access",
                "correct": False,
                "response": "Adapters are general-purpose.",
            },
        ],
    },
    "command_pattern": {
        "question_text": "What does the Command pattern enable?",
        "topic": "design_patterns",
        "answers": [
            {
                "text": "Faster execution",
                "correct": False,
                "response": "Commands don't improve speed.",
            },
            {
                "text": "Encapsulating requests as objects",
                "correct": True,
                "response": "Yes! Commands turn requests into first-class objects.",
                "reward_knowledge": "command",
            },
            {
                "text": "Direct method calls",
                "correct": False,
                "response": "Commands add indirection!",
            },
            {
                "text": "Database operations",
                "correct": False,
                "response": "Commands are general-purpose.",
            },
        ],
    },
    "state_pattern": {
        "question_text": "What problem does the State pattern solve?",
        "topic": "design_patterns",
        "answers": [
            {
                "text": "Managing application state cleanly",
                "correct": True,
                "response": "Correct! State pattern avoids large conditionals.",
                "reward_knowledge": "state",
            },
            {
                "text": "Storing data",
                "correct": False,
                "response": "State pattern is about behavior, not storage.",
            },
            {"text": "Threading", "correct": False, "response": "Not related to threads."},
            {
                "text": "Error handling",
                "correct": False,
                "response": "Not the purpose of State pattern.",
            },
        ],
    },
    # More database questions
    "indexing": {
        "question_text": "What is a trade-off of adding database indexes?",
        "topic": "databases",
        "answers": [
            {"text": "No trade-offs", "correct": False, "response": "There are always trade-offs!"},
            {
                "text": "Faster reads, slower writes",
                "correct": True,
                "response": "Correct! Indexes speed up queries but slow down inserts.",
                "reward_knowledge": "indexing",
            },
            {
                "text": "Slower everything",
                "correct": False,
                "response": "Indexes do help read performance.",
            },
            {
                "text": "More storage needed, but no performance impact",
                "correct": False,
                "response": "Indexes affect performance!",
            },
        ],
    },
    "normalization": {
        "question_text": "What is the purpose of database normalization?",
        "topic": "databases",
        "answers": [
            {
                "text": "Make queries faster",
                "correct": False,
                "response": "Normalization can actually slow queries!",
            },
            {
                "text": "Reduce data redundancy",
                "correct": True,
                "response": "Yes! Normalization eliminates duplicate data.",
                "reward_knowledge": "normalization",
            },
            {
                "text": "Increase storage",
                "correct": False,
                "response": "Normalization usually reduces storage.",
            },
            {
                "text": "Add more tables",
                "correct": False,
                "response": "Adding tables is a side effect, not the goal.",
            },
        ],
    },
    "materialized_views": {
        "question_text": "When should you use materialized views?",
        "topic": "databases",
        "answers": [
            {
                "text": "Always, for every query",
                "correct": False,
                "response": "Materialized views have trade-offs!",
            },
            {
                "text": "For expensive queries run frequently",
                "correct": True,
                "response": "Yes! Materialized views cache expensive computations.",
                "reward_knowledge": "materialized_views",
            },
            {
                "text": "To save disk space",
                "correct": False,
                "response": "Materialized views use more space!",
            },
            {
                "text": "Never, they're deprecated",
                "correct": False,
                "response": "Materialized views are still useful!",
            },
        ],
    },
    "write_ahead_log": {
        "question_text": "What is the purpose of a Write-Ahead Log (WAL)?",
        "topic": "databases",
        "answers": [
            {
                "text": "Speed up reads",
                "correct": False,
                "response": "WAL is about durability, not read speed.",
            },
            {
                "text": "Ensure durability and recovery",
                "correct": True,
                "response": "Correct! WAL enables crash recovery.",
                "reward_knowledge": "wal",
            },
            {"text": "Compress data", "correct": False, "response": "WAL doesn't compress data."},
            {
                "text": "Replicate data",
                "correct": False,
                "response": "Replication uses WAL but isn't its purpose.",
            },
        ],
    },
    # More programming fundamentals
    "closure": {
        "question_text": "What is a closure in programming?",
        "topic": "programming_fundamentals",
        "answers": [
            {"text": "A closed loop", "correct": False, "response": "Not about loops!"},
            {
                "text": "Function with access to outer scope",
                "correct": True,
                "response": "Yes! Closures capture their environment.",
                "reward_knowledge": "closure",
            },
            {
                "text": "A finished program",
                "correct": False,
                "response": "That's not what closure means.",
            },
            {
                "text": "A type of class",
                "correct": False,
                "response": "Closures are about functions.",
            },
        ],
    },
    "lazy_evaluation": {
        "question_text": "What is lazy evaluation?",
        "topic": "programming_fundamentals",
        "answers": [
            {"text": "Slow execution", "correct": False, "response": "Lazy doesn't mean slow!"},
            {
                "text": "Computing values only when needed",
                "correct": True,
                "response": "Correct! Lazy evaluation defers computation.",
                "reward_knowledge": "lazy_eval",
            },
            {
                "text": "Caching all results",
                "correct": False,
                "response": "That's memoization, different concept.",
            },
            {
                "text": "Parallel execution",
                "correct": False,
                "response": "Lazy evaluation is about deferral.",
            },
        ],
    },
    "immutability": {
        "question_text": "What is a benefit of immutable data structures?",
        "topic": "programming_fundamentals",
        "answers": [
            {
                "text": "Use less memory",
                "correct": False,
                "response": "Immutability can use more memory!",
            },
            {
                "text": "Easier to reason about, thread-safe",
                "correct": True,
                "response": "Yes! Immutability prevents many bugs.",
                "reward_knowledge": "immutability",
            },
            {
                "text": "Faster mutations",
                "correct": False,
                "response": "Immutable means no mutations!",
            },
            {
                "text": "Better for I/O",
                "correct": False,
                "response": "Immutability is about state management.",
            },
        ],
    },
    "type_inference": {
        "question_text": "What does type inference do?",
        "topic": "programming_fundamentals",
        "answers": [
            {"text": "Removes all types", "correct": False, "response": "Types still exist!"},
            {
                "text": "Automatically deduces types",
                "correct": True,
                "response": "Correct! Type inference determines types from context.",
                "reward_knowledge": "type_inference",
            },
            {
                "text": "Makes code slower",
                "correct": False,
                "response": "Inference happens at compile time.",
            },
            {
                "text": "Only works with numbers",
                "correct": False,
                "response": "Type inference works with all types.",
            },
        ],
    },
    # More software engineering questions
    "technical_debt": {
        "question_text": "What is technical debt?",
        "topic": "software_engineering",
        "answers": [
            {
                "text": "Money owed for tools",
                "correct": False,
                "response": "Not about financial debt!",
            },
            {
                "text": "Cost of suboptimal design choices",
                "correct": True,
                "response": "Yes! Technical debt accumulates from shortcuts.",
                "reward_knowledge": "tech_debt",
            },
            {"text": "Literal debt", "correct": False, "response": "It's a metaphor!"},
            {
                "text": "Bug count",
                "correct": False,
                "response": "Bugs are different from tech debt.",
            },
        ],
    },
    "cohesion": {
        "question_text": "What does high cohesion mean?",
        "topic": "software_engineering",
        "answers": [
            {
                "text": "Many responsibilities",
                "correct": False,
                "response": "High cohesion means focused!",
            },
            {
                "text": "Single, well-defined responsibility",
                "correct": True,
                "response": "Correct! High cohesion = focused modules.",
                "reward_knowledge": "cohesion",
            },
            {"text": "Lots of dependencies", "correct": False, "response": "That's high coupling!"},
            {
                "text": "Complex code",
                "correct": False,
                "response": "Cohesion is about responsibility.",
            },
        ],
    },
    "refactoring": {
        "question_text": "What should refactoring NOT do?",
        "topic": "software_engineering",
        "answers": [
            {
                "text": "Improve code structure",
                "correct": False,
                "response": "That's the purpose of refactoring!",
            },
            {
                "text": "Change external behavior",
                "correct": True,
                "response": "Correct! Refactoring preserves behavior.",
                "reward_knowledge": "refactoring",
            },
            {
                "text": "Make code more readable",
                "correct": False,
                "response": "Readability is a goal!",
            },
            {
                "text": "Remove duplication",
                "correct": False,
                "response": "DRY is a refactoring goal.",
            },
        ],
    },
    # More testing questions
    "integration_testing": {
        "question_text": "What do integration tests verify?",
        "topic": "testing",
        "answers": [
            {"text": "Individual functions", "correct": False, "response": "That's unit testing!"},
            {
                "text": "Components working together",
                "correct": True,
                "response": "Yes! Integration tests verify component interactions.",
                "reward_knowledge": "integration_test",
            },
            {"text": "User experience", "correct": False, "response": "That's UX testing."},
            {
                "text": "Performance only",
                "correct": False,
                "response": "Integration tests verify correctness.",
            },
        ],
    },
    "property_based_testing": {
        "question_text": "What is property-based testing?",
        "topic": "testing",
        "answers": [
            {
                "text": "Testing object properties",
                "correct": False,
                "response": "Not about object properties!",
            },
            {
                "text": "Testing with generated inputs",
                "correct": True,
                "response": "Yes! Property tests use random inputs to verify invariants.",
                "reward_knowledge": "property_test",
            },
            {
                "text": "Testing CSS properties",
                "correct": False,
                "response": "Nothing to do with CSS!",
            },
            {
                "text": "Manual testing",
                "correct": False,
                "response": "Property tests are automated.",
            },
        ],
    },
    "mutation_testing": {
        "question_text": "What does mutation testing measure?",
        "topic": "testing",
        "answers": [
            {
                "text": "Code changes over time",
                "correct": False,
                "response": "Not about version control!",
            },
            {
                "text": "Test suite effectiveness",
                "correct": True,
                "response": "Yes! Mutation testing finds weak tests.",
                "reward_knowledge": "mutation_test",
            },
            {"text": "Database mutations", "correct": False, "response": "Not about databases!"},
            {
                "text": "Performance changes",
                "correct": False,
                "response": "Mutation testing is about correctness.",
            },
        ],
    },
}


def main():
    # Read existing questions
    questions_path = Path(__file__).parent.parent / "neural_dive" / "data" / "questions.json"
    with open(questions_path) as f:
        questions = json.load(f)

    print(f"Loaded {len(questions)} existing questions")

    # Add new questions
    questions.update(NEW_QUESTIONS)

    print(f"Total questions after additions: {len(questions)}")

    # Write back
    with open(questions_path, "w") as f:
        json.dump(questions, f, indent=2)

    print(f"✓ Updated questions.json with {len(NEW_QUESTIONS)} new questions")

    print("\nNew questions by topic:")
    from collections import Counter

    topics = Counter(q.get("topic", "unknown") for q in NEW_QUESTIONS.values())
    for topic, count in sorted(topics.items()):
        print(f"  {topic}: {count}")


if __name__ == "__main__":
    main()
