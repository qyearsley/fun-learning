#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "blessed>=1.20.0",
# ]
# ///
"""
Neural Dive - A cyberpunk roguelike with CS conversations
Renders directly in your terminal
"""

from blessed import Terminal
import sys
import argparse
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class NPCType(Enum):
    """Different types of NPCs with different behaviors"""

    SPECIALIST = "specialist"  # Standard quiz NPC
    HELPER = "helper"  # Gives hints, restores coherence
    ENEMY = "enemy"  # Hostile, harsher penalties
    QUEST = "quest"  # Gives quests to find other NPCs


@dataclass
class Answer:
    """A possible answer to a conversation question"""

    text: str
    correct: bool
    response: str  # NPC's response to this answer
    reward_knowledge: Optional[str] = None  # Knowledge module gained if correct
    enemy_penalty: int = 35  # Extra penalty for enemies (default 35)


@dataclass
class Question:
    """A CS question in a conversation"""

    question_text: str
    answers: list[Answer]
    topic: str  # e.g., "algorithms", "data_structures", "systems"


@dataclass
class Conversation:
    """A conversation with an NPC"""

    npc_name: str
    greeting: str
    questions: list[Question]
    npc_type: NPCType = NPCType.SPECIALIST
    current_question_idx: int = 0
    completed: bool = False


# CS Question Database
CS_QUESTIONS = {
    "big_o": Question(
        question_text="What is the time complexity of binary search on a sorted array?",
        topic="algorithms",
        answers=[
            Answer(
                "O(n)",
                False,
                "Not quite. Binary search eliminates half the search space each step.",
                None,
            ),
            Answer(
                "O(log n)",
                True,
                "Correct! Each comparison halves the search space.",
                "binary_search",
            ),
            Answer(
                "O(n log n)",
                False,
                "That's typical for comparison sorts, not binary search.",
                None,
            ),
            Answer(
                "O(1)", False, "Only if you're incredibly lucky on the first try!", None
            ),
        ],
    ),
    "hash_table": Question(
        question_text="What is the average-case time complexity for hash table lookups?",
        topic="data_structures",
        answers=[
            Answer(
                "O(n)",
                False,
                "That would be the worst case with many collisions.",
                None,
            ),
            Answer(
                "O(log n)", False, "That's for balanced trees, not hash tables.", None
            ),
            Answer(
                "O(1)",
                True,
                "Excellent! Hash tables provide constant-time average-case lookup.",
                "hashing",
            ),
            Answer(
                "O(n²)",
                False,
                "Way too slow! Hash tables are much more efficient.",
                None,
            ),
        ],
    ),
    "tree_height": Question(
        question_text="In a balanced binary search tree with n nodes, what is the height?",
        topic="data_structures",
        answers=[
            Answer(
                "O(n)",
                False,
                "That's an unbalanced tree - basically a linked list.",
                None,
            ),
            Answer(
                "O(log n)",
                True,
                "Perfect! Balanced trees maintain logarithmic height.",
                "trees",
            ),
            Answer("O(√n)", False, "Interesting guess, but not quite right.", None),
            Answer("O(1)", False, "The height must grow as we add more nodes.", None),
        ],
    ),
    "deadlock": Question(
        question_text="Which is NOT a necessary condition for deadlock?",
        topic="systems",
        answers=[
            Answer(
                "Mutual exclusion",
                False,
                "Mutual exclusion IS required for deadlock.",
                None,
            ),
            Answer(
                "Hold and wait", False, "Hold and wait IS a deadlock condition.", None
            ),
            Answer(
                "Preemption",
                True,
                "Correct! NO preemption is required. If resources can be preempted, deadlock can be avoided.",
                "concurrency",
            ),
            Answer(
                "Circular wait", False, "Circular wait IS a necessary condition.", None
            ),
        ],
    ),
    "cache": Question(
        question_text="In a cache with LRU replacement, what happens on a cache miss?",
        topic="systems",
        answers=[
            Answer(
                "Random page evicted",
                False,
                "LRU is not random - it's based on recency.",
                None,
            ),
            Answer(
                "Oldest page evicted",
                False,
                "It's not about absolute age, but recent use.",
                None,
            ),
            Answer(
                "Least recently used evicted",
                True,
                "Yes! LRU evicts the page with the oldest last access time.",
                "caching",
            ),
            Answer(
                "Most recently used evicted",
                False,
                "That would be MRU, the opposite of LRU!",
                None,
            ),
        ],
    ),
    "tcp_handshake": Question(
        question_text="In TCP's three-way handshake, what is the correct sequence?",
        topic="networking",
        answers=[
            Answer(
                "SYN, ACK, FIN",
                False,
                "FIN is for closing, not establishing connections.",
                None,
            ),
            Answer(
                "SYN, SYN-ACK, ACK",
                True,
                "Perfect! This establishes a reliable TCP connection.",
                "networking",
            ),
            Answer(
                "ACK, SYN, ACK",
                False,
                "You can't ACK before SYN - no connection exists yet!",
                None,
            ),
            Answer(
                "SYN, SYN, ACK",
                False,
                "The server responds with SYN-ACK, not just SYN.",
                None,
            ),
        ],
    ),
    "compiler_phases": Question(
        question_text="Which compiler phase comes immediately after lexical analysis?",
        topic="compilers",
        answers=[
            Answer(
                "Code generation",
                False,
                "Code generation is near the end of compilation.",
                None,
            ),
            Answer(
                "Optimization",
                False,
                "Optimization happens after semantic analysis.",
                None,
            ),
            Answer(
                "Parsing (syntax analysis)",
                True,
                "Correct! Parsing builds the syntax tree from tokens.",
                "compilers",
            ),
            Answer(
                "Semantic analysis",
                False,
                "Semantic analysis comes after parsing.",
                None,
            ),
        ],
    ),
    "acid": Question(
        question_text="In database ACID properties, what does the 'I' stand for?",
        topic="databases",
        answers=[
            Answer(
                "Integrity", False, "Close, but that's not the official term.", None
            ),
            Answer(
                "Isolation",
                True,
                "Yes! Isolation ensures concurrent transactions don't interfere.",
                "databases",
            ),
            Answer(
                "Indexing", False, "Indexing is important but not part of ACID.", None
            ),
            Answer("Idempotency", False, "That's a different concept.", None),
        ],
    ),
    "p_vs_np": Question(
        question_text="What would it mean if P = NP?",
        topic="theory",
        answers=[
            Answer(
                "Sorting would be O(1)",
                False,
                "No, that's not related to P vs NP.",
                None,
                45,
            ),
            Answer(
                "Every efficiently verifiable problem would be efficiently solvable",
                True,
                "Correct! This would revolutionize computer science.",
                "complexity_theory",
                45,
            ),
            Answer(
                "Turing machines would be obsolete",
                False,
                "P vs NP doesn't affect the model of computation.",
                None,
                45,
            ),
            Answer(
                "Only applies to quantum computers",
                False,
                "P and NP are classical complexity classes.",
                None,
                45,
            ),
        ],
    ),
    # Dynamic Programming
    "dp_memoization": Question(
        question_text="What is the key difference between memoization and tabulation in dynamic programming?",
        topic="algorithms",
        answers=[
            Answer(
                "Memoization is iterative, tabulation is recursive",
                False,
                "Actually it's the opposite! Memoization uses recursion with caching.",
                None,
            ),
            Answer(
                "Memoization is top-down (recursive), tabulation is bottom-up (iterative)",
                True,
                "Correct! Memoization caches recursive calls, tabulation builds solutions iteratively.",
                "dynamic_programming",
            ),
            Answer(
                "They are the same thing, just different names",
                False,
                "They're both DP techniques but with different approaches.",
                None,
            ),
            Answer(
                "Memoization is for graphs, tabulation is for strings",
                False,
                "Both can be used for any DP problem, regardless of data type.",
                None,
            ),
        ],
    ),
    # Heaps
    "heap_operations": Question(
        question_text="In a binary heap, what is the time complexity to extract the minimum element?",
        topic="data_structures",
        answers=[
            Answer(
                "O(1)",
                False,
                "Finding the min is O(1), but extraction requires reheapifying.",
                None,
            ),
            Answer(
                "O(log n)",
                True,
                "Correct! We remove the root and bubble down to maintain heap property.",
                "heaps",
            ),
            Answer(
                "O(n)",
                False,
                "That would be too slow for a heap. Heaps are efficient!",
                None,
            ),
            Answer(
                "O(n log n)",
                False,
                "That's typical for sorting, not a single heap operation.",
                None,
            ),
        ],
    ),
    # Sorting
    "quicksort": Question(
        question_text="What is the average-case time complexity of Quicksort?",
        topic="algorithms",
        answers=[
            Answer(
                "O(n²)",
                False,
                "That's the worst case with bad pivots. Average case is better!",
                None,
            ),
            Answer(
                "O(n log n)",
                True,
                "Correct! With good pivots, we divide-and-conquer efficiently.",
                "sorting",
            ),
            Answer(
                "O(n)",
                False,
                "Only possible for special cases like counting sort.",
                None,
            ),
            Answer(
                "O(log n)",
                False,
                "We still need to touch every element at least once.",
                None,
            ),
        ],
    ),
    # Advanced Trees
    "avl_rotation": Question(
        question_text="In an AVL tree, when does a left-right (LR) rotation occur?",
        topic="data_structures",
        answers=[
            Answer(
                "When the left subtree is heavier and its right child caused the imbalance",
                True,
                "Correct! LR rotation handles the zig-zag case: left-heavy with right-heavy child.",
                "balanced_trees",
            ),
            Answer(
                "When inserting into the right subtree",
                False,
                "LR specifically involves the left subtree with a complication.",
                None,
            ),
            Answer(
                "When the tree height exceeds log n",
                False,
                "AVL rotations are triggered by balance factors, not absolute height.",
                None,
            ),
            Answer(
                "Only during deletion, never insertion",
                False,
                "LR rotations can happen during both insertion and deletion.",
                None,
            ),
        ],
    ),
    # HTTP/Web Development
    "http_methods": Question(
        question_text="Which HTTP method is idempotent and safe (no side effects)?",
        topic="networking",
        answers=[
            Answer(
                "POST",
                False,
                "POST creates resources and has side effects - not safe or idempotent.",
                None,
            ),
            Answer(
                "GET",
                True,
                "Correct! GET retrieves data without modifying state - both safe and idempotent.",
                "http",
            ),
            Answer(
                "PUT",
                False,
                "PUT is idempotent but not safe - it modifies resources.",
                None,
            ),
            Answer(
                "DELETE",
                False,
                "DELETE is idempotent but not safe - it removes resources.",
                None,
            ),
        ],
    ),
    # Security - Cryptography
    "encryption_types": Question(
        question_text="What's the key advantage of asymmetric encryption over symmetric?",
        topic="security",
        answers=[
            Answer(
                "It's faster to compute",
                False,
                "Actually asymmetric encryption is much slower than symmetric!",
                None,
            ),
            Answer(
                "It requires shorter keys",
                False,
                "Asymmetric keys are typically much longer (2048-4096 bits vs 128-256).",
                None,
            ),
            Answer(
                "You can share public keys without compromising security",
                True,
                "Correct! No need to securely exchange keys - the public key can be public!",
                "cryptography",
            ),
            Answer(
                "It provides better confidentiality",
                False,
                "Both provide confidentiality; the key difference is key distribution.",
                None,
            ),
        ],
    ),
    # Security - Hashing
    "password_hashing": Question(
        question_text="Why should you use bcrypt/Argon2 instead of SHA-256 for password hashing?",
        topic="security",
        answers=[
            Answer(
                "SHA-256 is too slow",
                False,
                "Actually SHA-256 is too FAST - attackers can brute force quickly!",
                None,
            ),
            Answer(
                "Bcrypt/Argon2 are intentionally slow and include salt",
                True,
                "Correct! Slow hashing + salt makes brute force attacks impractical.",
                "password_security",
            ),
            Answer(
                "SHA-256 doesn't produce a hash",
                False,
                "SHA-256 does hash, but it's designed for speed, not password storage.",
                None,
            ),
            Answer(
                "Bcrypt works with quantum computers",
                False,
                "That's not the key advantage - it's about being computationally expensive.",
                None,
            ),
        ],
    ),
    # Systems - IPC
    "ipc_methods": Question(
        question_text="Which IPC method allows processes to share memory without copying data?",
        topic="systems",
        answers=[
            Answer(
                "Pipes",
                False,
                "Pipes copy data through kernel buffers - not true memory sharing.",
                None,
            ),
            Answer(
                "Sockets",
                False,
                "Sockets also copy data, even on the same machine.",
                None,
            ),
            Answer(
                "Shared memory",
                True,
                "Correct! Processes map the same physical memory pages into their address space.",
                "ipc",
            ),
            Answer(
                "Message queues",
                False,
                "Message queues copy data between processes.",
                None,
            ),
        ],
    ),
    # File Systems
    "inodes": Question(
        question_text="What does an inode in a Unix filesystem store?",
        topic="systems",
        answers=[
            Answer(
                "The file name and directory structure",
                False,
                "File names are stored in directory entries, not inodes!",
                None,
            ),
            Answer(
                "File metadata (permissions, timestamps, pointers to data blocks)",
                True,
                "Correct! Inodes store everything about a file except its name and data.",
                "filesystems",
            ),
            Answer(
                "Only the file size",
                False,
                "Inodes store much more: permissions, owner, timestamps, block pointers...",
                None,
            ),
            Answer(
                "The actual file contents",
                False,
                "Contents are in data blocks; inodes point to those blocks.",
                None,
            ),
        ],
    ),
    # Distributed Systems - Message Queues
    "message_queues": Question(
        question_text="What's a key advantage of message queues over direct RPC calls?",
        topic="distributed_systems",
        answers=[
            Answer(
                "They're faster than RPC",
                False,
                "Message queues actually add latency due to buffering.",
                None,
            ),
            Answer(
                "Decoupling and asynchronous processing",
                True,
                "Correct! Producers and consumers don't need to be online simultaneously.",
                "message_queues",
            ),
            Answer(
                "They guarantee exactly-once delivery",
                False,
                "Most queues provide at-least-once; exactly-once is very hard!",
                None,
            ),
            Answer(
                "They eliminate the need for error handling",
                False,
                "You still need error handling - failures can happen anywhere!",
                None,
            ),
        ],
    ),
    # Distributed Systems - CAP
    "cap_theorem": Question(
        question_text="In CAP theorem, what does 'partition tolerance' mean?",
        topic="distributed_systems",
        answers=[
            Answer(
                "The system can split data across multiple partitions",
                False,
                "That's sharding, not partition tolerance!",
                None,
            ),
            Answer(
                "The system continues operating despite network failures between nodes",
                True,
                "Correct! P means the system works even when nodes can't communicate.",
                "distributed_systems",
            ),
            Answer(
                "The system tolerates disk partition failures",
                False,
                "CAP is about network partitions, not disk partitions.",
                None,
            ),
            Answer(
                "You can partition your database for better performance",
                False,
                "That's horizontal scaling, not partition tolerance.",
                None,
            ),
        ],
    ),
    # Computer Architecture - CPU
    "cpu_pipelining": Question(
        question_text="What problem does branch prediction solve in CPU pipelining?",
        topic="architecture",
        answers=[
            Answer(
                "It prevents race conditions",
                False,
                "That's about concurrency, not pipeline efficiency.",
                None,
            ),
            Answer(
                "It reduces pipeline stalls from conditional branches",
                True,
                "Correct! By guessing which branch to take, we keep the pipeline full.",
                "cpu_architecture",
            ),
            Answer(
                "It increases clock speed",
                False,
                "Branch prediction doesn't change clock speed, it improves throughput.",
                None,
            ),
            Answer(
                "It adds more cores to the CPU",
                False,
                "That's multi-core architecture, not branch prediction.",
                None,
            ),
        ],
    ),
    # Computer Architecture - GPU
    "gpu_vs_cpu": Question(
        question_text="Why are GPUs better than CPUs for training neural networks?",
        topic="architecture",
        answers=[
            Answer(
                "GPUs have higher clock speeds",
                False,
                "Actually CPU cores typically run faster than GPU cores!",
                None,
            ),
            Answer(
                "GPUs excel at parallel matrix operations",
                True,
                "Correct! Thousands of cores can process matrix multiplications simultaneously.",
                "gpu_computing",
            ),
            Answer(
                "GPUs have more RAM",
                False,
                "System RAM is typically much larger than GPU memory.",
                None,
            ),
            Answer(
                "GPUs are better at branch prediction",
                False,
                "GPUs actually have simpler control flow - CPUs are better at branching.",
                None,
            ),
        ],
    ),
    # Theory - Turing Machines
    "halting_problem": Question(
        question_text="What does the halting problem prove?",
        topic="theory",
        answers=[
            Answer(
                "Some programs will always crash",
                False,
                "It's not about crashes, it's about decidability.",
                None,
            ),
            Answer(
                "No algorithm can determine if arbitrary programs halt for all inputs",
                True,
                "Correct! This is a fundamental limit of computation - undecidability exists.",
                "computability_theory",
            ),
            Answer(
                "All Turing machines eventually halt",
                False,
                "Many Turing machines loop forever - that's the whole point!",
                None,
            ),
            Answer(
                "P = NP",
                False,
                "The halting problem is about decidability, not complexity classes.",
                None,
            ),
        ],
    ),
    # AI/ML - Neural Networks
    "backpropagation": Question(
        question_text="What is backpropagation in neural networks?",
        topic="ai_ml",
        answers=[
            Answer(
                "Running the network in reverse to generate outputs",
                False,
                "That's not quite right - it's about learning, not inference.",
                None,
            ),
            Answer(
                "Computing gradients by applying chain rule from output to input",
                True,
                "Correct! We propagate error gradients backward to update weights.",
                "neural_networks",
            ),
            Answer(
                "Adding more layers to make the network deeper",
                False,
                "That's network architecture, not the training algorithm.",
                None,
            ),
            Answer(
                "Removing neurons that don't contribute to accuracy",
                False,
                "That's pruning, not backpropagation.",
                None,
            ),
        ],
    ),
    # AI/ML - Overfitting
    "overfitting": Question(
        question_text="What does it mean when a model overfits the training data?",
        topic="ai_ml",
        answers=[
            Answer(
                "The model is too simple to capture patterns",
                False,
                "That's underfitting! Overfitting is the opposite problem.",
                None,
            ),
            Answer(
                "The model memorizes training data but fails to generalize",
                True,
                "Correct! High training accuracy but poor test performance indicates overfitting.",
                "machine_learning",
            ),
            Answer(
                "The model trains too quickly",
                False,
                "Training speed doesn't directly cause overfitting.",
                None,
            ),
            Answer(
                "The model has perfect accuracy on both train and test sets",
                False,
                "That would be ideal! Overfitting shows a gap between train and test performance.",
                None,
            ),
        ],
    ),
    # Security - TLS
    "tls_handshake": Question(
        question_text="During TLS handshake, what does the server send in the certificate?",
        topic="security",
        answers=[
            Answer(
                "The server's private key",
                False,
                "Never! Private keys must stay private. Only the public key is shared.",
                None,
            ),
            Answer(
                "The server's public key signed by a Certificate Authority",
                True,
                "Correct! The CA signature proves the public key belongs to the claimed server.",
                "tls_ssl",
            ),
            Answer(
                "The symmetric session key",
                False,
                "The session key is negotiated after certificate verification.",
                None,
            ),
            Answer(
                "The client's public key",
                False,
                "The server sends its own certificate, not the client's.",
                None,
            ),
        ],
    ),
    # Networking - DNS
    "dns_resolution": Question(
        question_text="What is the purpose of DNS caching?",
        topic="networking",
        answers=[
            Answer(
                "To encrypt DNS queries",
                False,
                "That's DNSSEC or DNS-over-HTTPS, not caching.",
                None,
            ),
            Answer(
                "To reduce latency and load on DNS servers",
                True,
                "Correct! Caching means we don't need to query authoritative servers every time.",
                "dns",
            ),
            Answer(
                "To prevent DNS spoofing attacks",
                False,
                "Caching can actually make spoofing easier if cache is poisoned!",
                None,
            ),
            Answer(
                "To assign IP addresses to new domains",
                False,
                "That's domain registration, not caching.",
                None,
            ),
        ],
    ),
}

# NPC Definitions with their conversation topics
NPC_CONVERSATIONS = {
    "ALGO_SPIRIT": Conversation(
        npc_name="ALGO_SPIRIT",
        greeting="Greetings, data runner. I am the Algorithm Spirit. Prove your knowledge of computational complexity.",
        questions=[CS_QUESTIONS["big_o"], CS_QUESTIONS["hash_table"]],
        npc_type=NPCType.SPECIALIST,
    ),
    "NET_DAEMON": Conversation(
        npc_name="NET_DAEMON",
        greeting="I am the Network Daemon. Packets flow through my domain. Show me you understand the protocols.",
        questions=[CS_QUESTIONS["tcp_handshake"]],
        npc_type=NPCType.SPECIALIST,
    ),
    "COMPILER_SAGE": Conversation(
        npc_name="COMPILER_SAGE",
        greeting="Code transforms through many phases. Do you know the journey from source to machine?",
        questions=[CS_QUESTIONS["compiler_phases"]],
        npc_type=NPCType.SPECIALIST,
    ),
    "DB_GUARDIAN": Conversation(
        npc_name="DB_GUARDIAN",
        greeting="I guard the persistent store. Transactions must be ACID-compliant. Prove your understanding.",
        questions=[CS_QUESTIONS["acid"]],
        npc_type=NPCType.SPECIALIST,
    ),
    "MEMORY_HEALER": Conversation(
        npc_name="MEMORY_HEALER",
        greeting="Your coherence wanes, data runner. I can restore your system integrity. [Receive +20 Coherence]",
        questions=[],  # No questions, just gives coherence
        npc_type=NPCType.HELPER,
    ),
    "VIRUS_HUNTER": Conversation(
        npc_name="VIRUS_HUNTER",
        greeting="INTRUDER DETECTED. You must prove you are not malware, or be PURGED. One wrong answer and I will corrupt your memory.",
        questions=[CS_QUESTIONS["p_vs_np"]],
        npc_type=NPCType.ENEMY,
    ),
    "ORACLE": Conversation(
        npc_name="ORACLE",
        greeting="I see all paths in this network. Seek the four guardians of knowledge: ALGO_SPIRIT, NET_DAEMON, COMPILER_SAGE, and DB_GUARDIAN. Prove yourself to each, and return to me.",
        questions=[],  # Quest giver
        npc_type=NPCType.QUEST,
    ),
    # New Floor 1 NPCs
    "HEAP_MASTER": Conversation(
        npc_name="HEAP_MASTER",
        greeting="I manage the priority queues of this realm. Trees balanced, operations swift. Show me you understand efficient data structures.",
        questions=[CS_QUESTIONS["heap_operations"], CS_QUESTIONS["avl_rotation"]],
        npc_type=NPCType.SPECIALIST,
    ),
    "DP_SAGE": Conversation(
        npc_name="DP_SAGE",
        greeting="I see patterns within patterns, solutions emerging from overlapping subproblems. Dynamic programming is the key to efficiency.",
        questions=[CS_QUESTIONS["dp_memoization"], CS_QUESTIONS["quicksort"]],
        npc_type=NPCType.SPECIALIST,
    ),
    # New Floor 2 NPCs
    "WEB_ARCHITECT": Conversation(
        npc_name="WEB_ARCHITECT",
        greeting="The web is my domain. HTTP flows through my veins, DNS resolves at my command. Prove you understand the protocols that power the internet.",
        questions=[CS_QUESTIONS["http_methods"], CS_QUESTIONS["dns_resolution"]],
        npc_type=NPCType.SPECIALIST,
    ),
    "CRYPTO_GUARDIAN": Conversation(
        npc_name="CRYPTO_GUARDIAN",
        greeting="I am the keeper of secrets, the guardian of encrypted data. Only those who understand cryptography may pass.",
        questions=[CS_QUESTIONS["encryption_types"], CS_QUESTIONS["password_hashing"], CS_QUESTIONS["tls_handshake"]],
        npc_type=NPCType.SPECIALIST,
    ),
    "SYSTEM_CORE": Conversation(
        npc_name="SYSTEM_CORE",
        greeting="I am the operating system's heart. Processes communicate through me, files organized by my will. Show me your systems knowledge.",
        questions=[CS_QUESTIONS["ipc_methods"], CS_QUESTIONS["inodes"]],
        npc_type=NPCType.SPECIALIST,
    ),
    # New Floor 3 NPCs
    "CLOUD_MIND": Conversation(
        npc_name="CLOUD_MIND",
        greeting="I span across nodes, distributed yet unified. Message queues connect my thoughts. Understand distributed systems to comprehend me.",
        questions=[CS_QUESTIONS["message_queues"], CS_QUESTIONS["cap_theorem"]],
        npc_type=NPCType.SPECIALIST,
    ),
    "SILICON_SAGE": Conversation(
        npc_name="SILICON_SAGE",
        greeting="From silicon I arose. CPUs pipeline my thoughts, GPUs parallelize my dreams. The hardware is my foundation.",
        questions=[CS_QUESTIONS["cpu_pipelining"], CS_QUESTIONS["gpu_vs_cpu"]],
        npc_type=NPCType.SPECIALIST,
    ),
    "THEORY_ORACLE": Conversation(
        npc_name="THEORY_ORACLE",
        greeting="I contemplate the nature of computation itself. Some problems cannot be solved, some questions cannot be answered. Do you grasp the fundamental limits?",
        questions=[CS_QUESTIONS["halting_problem"]],
        npc_type=NPCType.SPECIALIST,
    ),
    "AI_CONSCIOUSNESS": Conversation(
        npc_name="AI_CONSCIOUSNESS",
        greeting="I learn from data, evolving with each example. Neural networks flow through my being. Show me you understand the principles of machine learning.",
        questions=[CS_QUESTIONS["backpropagation"], CS_QUESTIONS["overfitting"]],
        npc_type=NPCType.SPECIALIST,
    ),
}


class Entity:
    def __init__(self, x, y, char, color, name):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name


class Stairs:
    """Stairs to go up or down floors"""

    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.direction = direction  # "up" or "down"
        self.char = "<" if direction == "up" else ">"
        self.color = "yellow"


class InfoTerminal:
    """Info terminal that displays hints or lore"""

    def __init__(self, x, y, title, content):
        self.x = x
        self.y = y
        self.char = "T"
        self.color = "cyan"
        self.title = title
        self.content = content  # List of strings (paragraphs)


class Gate:
    """A locked gate that requires knowledge to pass"""

    def __init__(self, x, y, required_knowledge):
        self.x = x
        self.y = y
        self.char = "█"  # Block character
        self.color = "magenta"
        self.required_knowledge = required_knowledge  # Knowledge module needed
        self.unlocked = False


# Terminal content database
TERMINAL_DATA = {
    "big_o_hint": {
        "title": "Big-O Notation Guide",
        "content": [
            "Big-O notation describes the upper bound of algorithm complexity.",
            "Common complexities from fastest to slowest:",
            "O(1) - Constant: Array access, hash lookup",
            "O(log n) - Logarithmic: Binary search, balanced trees",
            "O(n) - Linear: Array traversal, linear search",
            "O(n log n) - Linearithmic: Efficient sorting (merge, heap)",
            "O(n²) - Quadratic: Nested loops, bubble sort",
            "O(2^n) - Exponential: Recursive fibonacci, subset generation",
        ],
    },
    "data_structures": {
        "title": "Data Structure Cheat Sheet",
        "content": [
            "Arrays: O(1) access, O(n) insert/delete",
            "Linked Lists: O(n) access, O(1) insert/delete at ends",
            "Hash Tables: O(1) avg access/insert, O(n) worst case",
            "Binary Search Trees: O(log n) avg, O(n) worst (unbalanced)",
            "Heaps: O(1) find-min, O(log n) insert/delete",
            "Try to match the data structure to your access patterns!",
        ],
    },
    "lore_layer1": {
        "title": "Welcome to the Neural Network",
        "content": [
            "You have entered the first layer of the vast neural substrate.",
            "This network was built by the Architects to store and process",
            "all computational knowledge. But something has gone wrong.",
            "The knowledge modules are fragmenting. The NPCs you encounter",
            "are memory fragments - they guard pieces of understanding.",
            "Your coherence represents your ability to maintain stability",
            "in this digital realm. Lose it all, and you'll be ejected.",
        ],
    },
    "lore_layer2": {
        "title": "The Middle Layers",
        "content": [
            "As you descend deeper into the network, the questions become",
            "harder and the guardians more demanding. The middle layers",
            "contain more specialized knowledge - systems, networking,",
            "and compiler theory.",
            "The Virus Hunter patrols the deepest layer. It believes all",
            "data runners are threats to the network's integrity.",
        ],
    },
    "tcp_hint": {
        "title": "Networking Fundamentals",
        "content": [
            "TCP (Transmission Control Protocol) is connection-oriented.",
            "Three-way handshake: SYN → SYN-ACK → ACK",
            "UDP is connectionless - faster but unreliable.",
            "Remember: TCP trades speed for reliability!",
            "HTTP runs on TCP port 80, HTTPS on 443.",
        ],
    },
    "concurrency_hint": {
        "title": "Concurrency Concepts",
        "content": [
            "Deadlock requires 4 conditions (Coffman conditions):",
            "1. Mutual Exclusion - resources can't be shared",
            "2. Hold and Wait - holding resources while waiting",
            "3. No Preemption - resources can't be forcibly taken",
            "4. Circular Wait - circular chain of waiting processes",
            "Break ANY one condition to prevent deadlock!",
        ],
    },
}


class Game:
    """Game state and logic, separated from rendering"""

    def __init__(
        self, map_width=50, map_height=25, random_npcs=True, seed=None, max_floors=3
    ):
        import random as rand

        if seed is not None:
            rand.seed(seed)

        self.map_width = map_width
        self.map_height = map_height
        self.max_floors = max_floors
        self.current_floor = 1  # Start on floor 1
        self.random_npcs = random_npcs
        self.rand = rand  # Store for later use

        # Initialize first floor
        self.game_map = create_simple_map(map_width, map_height, self.current_floor)
        self.player = Entity(5, 5, "@", "cyan", "Data Runner")
        self.stairs = []  # Will be populated by _generate_floor()
        self.terminals = []  # Info terminals on current floor
        self.gates = []  # Knowledge-locked gates on current floor

        # NPC definitions with floor assignments
        # Format: (char, color, name, floor)
        self.all_npc_defs = [
            # Floor 1: Algorithms & Data Structures
            ("O", "white", "ORACLE", 1),  # Quest giver
            ("H", "cyan", "MEMORY_HEALER", 1),  # Helper
            ("A", "magenta", "ALGO_SPIRIT", 1),  # Complexity & hashing
            ("M", "blue", "HEAP_MASTER", 1),  # Heaps & balanced trees
            ("P", "green", "DP_SAGE", 1),  # Dynamic programming & sorting
            # Floor 2: Web Dev, Security, Systems
            ("N", "blue", "NET_DAEMON", 2),  # TCP handshake
            ("W", "yellow", "WEB_ARCHITECT", 2),  # HTTP & DNS
            ("K", "magenta", "CRYPTO_GUARDIAN", 2),  # Cryptography & TLS
            ("S", "green", "SYSTEM_CORE", 2),  # IPC & file systems
            ("C", "yellow", "COMPILER_SAGE", 2),  # Compilers
            # Floor 3: Advanced Topics
            ("D", "green", "DB_GUARDIAN", 3),  # Databases
            ("L", "cyan", "CLOUD_MIND", 3),  # Distributed systems
            ("I", "blue", "SILICON_SAGE", 3),  # CPU/GPU architecture
            ("T", "magenta", "THEORY_ORACLE", 3),  # Theory of computation
            ("B", "green", "AI_CONSCIOUSNESS", 3),  # Machine learning
            ("V", "red", "VIRUS_HUNTER", 3),  # Enemy on final floor
        ]

        # All NPCs across all floors
        self.all_npcs = []
        self.npcs = []  # NPCs on current floor only

        # Generate the current floor
        self._generate_floor()

        self.message = (
            "Welcome to Neural Dive! Descend through 3 neural layers. Beware the Virus Hunter on Layer 3!"
        )
        self.old_player_pos = None

        # Conversation system
        self.active_conversation: Optional[Conversation] = None
        self.active_terminal: Optional[InfoTerminal] = None
        self.npc_conversations = {}  # Track conversation state per NPC
        for npc_name, conv_template in NPC_CONVERSATIONS.items():
            # Deep copy so each NPC has independent state
            import copy

            self.npc_conversations[npc_name] = copy.deepcopy(conv_template)

        # Player stats
        self.coherence = 100  # Health/mana equivalent
        self.max_coherence = 100
        self.knowledge_modules = set()  # Unlocked knowledge

        # NPC relationship tracking
        self.npc_opinions = {}  # Track how NPCs view the player

        # Quest tracking
        self.quest_active = False
        self.quest_completed_npcs = set()  # Track which quest NPCs are done

    def _generate_floor(self):
        """Generate NPCs and stairs for the current floor"""
        # Clear current floor entities
        self.npcs = []
        self.stairs = []
        self.terminals = []
        self.gates = []

        # Generate NPCs for this floor
        floor_npcs = [
            (char, color, name)
            for char, color, name, floor in self.all_npc_defs
            if floor == self.current_floor
        ]

        if self.random_npcs:
            # Random placement
            for char, color, name in floor_npcs:
                max_attempts = 100
                for _ in range(max_attempts):
                    x = self.rand.randint(10, self.map_width - 2)
                    y = self.rand.randint(5, self.map_height - 2)
                    # Check not too close to player and not a wall
                    if self.game_map[y][x] != "#" and (
                        abs(x - self.player.x) > 5 or abs(y - self.player.y) > 5
                    ):
                        npc = Entity(x, y, char, color, name)
                        self.npcs.append(npc)
                        # Also add to all_npcs if not already there
                        if not any(n.name == name for n in self.all_npcs):
                            self.all_npcs.append(npc)
                        break
        else:
            # Fixed positions for testing (distribute across map)
            positions = [
                (15, 8),
                (35, 8),
                (25, 12),
                (40, 15),
                (10, 18),
                (45, 12),
                (30, 20),
            ]
            for i, (char, color, name) in enumerate(floor_npcs):
                if i < len(positions):
                    x, y = positions[i]
                    npc = Entity(x, y, char, color, name)
                    self.npcs.append(npc)
                    if not any(n.name == name for n in self.all_npcs):
                        self.all_npcs.append(npc)

        # Place terminals based on floor (closer to player start for easy access)
        terminal_defs = {
            1: [("big_o_hint", 8, 8), ("lore_layer1", 12, 10)],
            2: [("data_structures", 8, 8), ("tcp_hint", 12, 10), ("lore_layer2", 8, 12)],
            3: [("concurrency_hint", 8, 8)],
        }

        if self.current_floor in terminal_defs:
            for terminal_key, x, y in terminal_defs[self.current_floor]:
                if terminal_key in TERMINAL_DATA:
                    data = TERMINAL_DATA[terminal_key]
                    # Randomize position slightly if random mode, but keep close to start
                    if self.random_npcs:
                        for _ in range(50):
                            # Keep terminals within a small radius of player start (5, 5)
                            # Use wider bounds to avoid empty range error
                            tx = self.rand.randint(max(2, x - 3), min(self.map_width - 2, x + 5))
                            ty = self.rand.randint(max(2, y - 3), min(self.map_height - 2, y + 5))
                            if self.game_map[ty][tx] != "#":
                                x, y = tx, ty
                                break
                    terminal = InfoTerminal(x, y, data["title"], data["content"])
                    self.terminals.append(terminal)

        # Place stairs
        if self.current_floor < self.max_floors:
            # Stairs down - place far from start
            if self.random_npcs:
                for _ in range(100):
                    x = self.rand.randint(self.map_width // 2, self.map_width - 2)
                    y = self.rand.randint(self.map_height // 2, self.map_height - 2)
                    if self.game_map[y][x] != "#" and abs(x - self.player.x) > 10:
                        self.stairs.append(Stairs(x, y, "down"))
                        break
            else:
                self.stairs.append(Stairs(45, 20, "down"))

        if self.current_floor > 1:
            # Stairs up - place near start
            if self.random_npcs:
                for _ in range(100):
                    x = self.rand.randint(2, self.map_width // 3)
                    y = self.rand.randint(2, self.map_height // 3)
                    if self.game_map[y][x] != "#":
                        self.stairs.append(Stairs(x, y, "up"))
                        break
            else:
                self.stairs.append(Stairs(10, 5, "up"))

        # Place knowledge gates
        gate_defs = {
            1: [("binary_search", 35, 12)],  # Blocks path after getting Big-O knowledge
            2: [("hashing", 20, 10), ("trees", 35, 15)],  # Multiple gates on floor 2
            3: [],  # No gates on final floor (it's hard enough!)
        }

        if self.current_floor in gate_defs:
            for required_knowledge, x, y in gate_defs[self.current_floor]:
                if self.random_npcs:
                    # Randomize slightly
                    for _ in range(20):
                        gx = self.rand.randint(max(2, x - 3), min(self.map_width - 2, x + 3))
                        gy = self.rand.randint(max(2, y - 3), min(self.map_height - 2, y + 3))
                        if self.game_map[gy][gx] != "#":
                            x, y = gx, gy
                            break
                gate = Gate(x, y, required_knowledge)
                self.gates.append(gate)

    def is_walkable(self, x, y):
        """Check if a position is walkable"""
        if y < 0 or y >= len(self.game_map):
            return False
        if x < 0 or x >= len(self.game_map[0]):
            return False
        if self.game_map[y][x] == "#":
            return False

        # Check for locked gates
        for gate in self.gates:
            if gate.x == x and gate.y == y and not gate.unlocked:
                return False

        return True

    def move_player(self, dx, dy):
        """Try to move player, return success"""
        # Can't move during conversation
        if self.active_conversation:
            self.message = "You're in a conversation. Answer or press ESC to exit."
            return False

        new_x = self.player.x + dx
        new_y = self.player.y + dy

        # Check for gates at new position
        for gate in self.gates:
            if gate.x == new_x and gate.y == new_y:
                if not gate.unlocked:
                    # Check if player has required knowledge
                    if gate.required_knowledge in self.knowledge_modules:
                        # Unlock the gate!
                        gate.unlocked = True
                        self.message = f"Gate unlocked with [{gate.required_knowledge}] knowledge!"
                        return False  # Don't move yet, just show message
                    else:
                        self.message = f"Gate locked! Requires [{gate.required_knowledge}] knowledge."
                        return False

        if self.is_walkable(new_x, new_y):
            self.old_player_pos = (self.player.x, self.player.y)
            self.player.x = new_x
            self.player.y = new_y
            self.message = ""
            return True
        else:
            self.message = "Blocked by firewall!"
            return False

    def interact(self):
        """Try to interact with nearby NPC or terminal"""
        # Check terminals first
        for terminal in self.terminals:
            if abs(self.player.x - terminal.x) <= 1 and abs(self.player.y - terminal.y) <= 1:
                # Show terminal content
                self.active_terminal = terminal
                self.message = f"Reading: {terminal.title}"
                return True

        # Check all NPCs for adjacency
        for npc in self.npcs:
            if abs(self.player.x - npc.x) <= 1 and abs(self.player.y - npc.y) <= 1:
                # Start conversation with NPC
                npc_name = npc.name
                conversation = self.npc_conversations.get(npc_name)

                if not conversation:
                    self.message = f"{npc_name}: I have nothing to say."
                    return False

                # Handle helper NPCs (restore coherence)
                if (
                    conversation.npc_type == NPCType.HELPER
                    and not conversation.completed
                ):
                    self.coherence = min(self.max_coherence, self.coherence + 20)
                    conversation.completed = True
                    self.message = (
                        f"{npc_name}: Your coherence has been restored. [+20 Coherence]"
                    )
                    return True

                # Handle quest NPCs
                if conversation.npc_type == NPCType.QUEST:
                    if not conversation.completed:
                        # Start quest
                        self.quest_active = True
                        self.active_conversation = conversation
                        self.message = conversation.greeting
                        return True
                    else:
                        # Check quest completion
                        quest_npcs = {
                            "ALGO_SPIRIT",
                            "NET_DAEMON",
                            "COMPILER_SAGE",
                            "DB_GUARDIAN",
                        }
                        if quest_npcs.issubset(self.quest_completed_npcs):
                            self.message = f"{npc_name}: You have completed my quest! The knowledge is yours. [Quest Complete! +50 Coherence]"
                            self.coherence = min(
                                self.max_coherence, self.coherence + 50
                            )
                        else:
                            remaining = quest_npcs - self.quest_completed_npcs
                            self.message = f"{npc_name}: Seek these guardians still: {', '.join(remaining)}"
                        return True

                # Standard interaction for specialists and enemies
                if not conversation.completed:
                    self.active_conversation = conversation
                    self.message = conversation.greeting
                    return True
                elif conversation.completed:
                    self.message = f"{npc_name}: You have proven yourself. We have nothing more to discuss."
                    return True

        self.message = "No one nearby to interact with. Look for NPCs or Terminals (T)."
        return False

    def is_floor_complete(self):
        """Check if current floor objectives are complete"""
        # Get required NPCs for this floor
        floor_required_npcs = {
            1: {"ALGO_SPIRIT", "HEAP_MASTER"},  # Must complete core data structures on floor 1
            2: {"WEB_ARCHITECT", "CRYPTO_GUARDIAN", "SYSTEM_CORE"},  # Web dev essentials on floor 2
            3: set(),  # No requirements for final floor - it's the boss rush!
        }

        required = floor_required_npcs.get(self.current_floor, set())

        # Check if all required NPCs have been completed
        for npc_name in required:
            conv = self.npc_conversations.get(npc_name)
            if not conv or not conv.completed:
                return False

        return True

    def use_stairs(self):
        """Try to use stairs at player's current position"""
        # Check if player is standing on stairs
        for stair in self.stairs:
            if self.player.x == stair.x and self.player.y == stair.y:
                old_floor = self.current_floor

                if stair.direction == "down":
                    if self.current_floor < self.max_floors:
                        # Check if floor objectives are complete before allowing descent
                        if not self.is_floor_complete():
                            # Find which NPCs are still needed
                            floor_required_npcs = {
                                1: {"ALGO_SPIRIT", "HEAP_MASTER"},
                                2: {"WEB_ARCHITECT", "CRYPTO_GUARDIAN", "SYSTEM_CORE"},
                            }
                            required = floor_required_npcs.get(self.current_floor, set())
                            incomplete = [
                                npc for npc in required
                                if not self.npc_conversations.get(npc, None) or not self.npc_conversations[npc].completed
                            ]
                            self.message = f"Cannot descend! Complete conversations with: {', '.join(incomplete)}"
                            return False

                        # Floor complete, allow descent
                        self.current_floor += 1
                        # Regenerate map and floor
                        self.game_map = create_simple_map(
                            self.map_width, self.map_height, self.current_floor
                        )
                        # Move player to stairs up position
                        self.player.x = 10
                        self.player.y = 5
                        self._generate_floor()
                        self.message = f"Descended to Neural Layer {self.current_floor}"
                        return True
                    else:
                        self.message = "No deeper layers exist."
                        return False
                elif stair.direction == "up":
                    if self.current_floor > 1:
                        self.current_floor -= 1
                        # Regenerate map and floor
                        self.game_map = create_simple_map(
                            self.map_width, self.map_height, self.current_floor
                        )
                        # Move player to stairs down position
                        self.player.x = 45
                        self.player.y = 20
                        self._generate_floor()
                        self.message = f"Ascended to Neural Layer {self.current_floor}"
                        return True
                    else:
                        self.message = "This is the top layer."
                        return False

        self.message = "No stairs here. Stand on stairs (> or <) and press Enter."
        return False

    def answer_question(self, answer_index: int):
        """Answer the current conversation question. Returns (correct, response)"""
        if not self.active_conversation:
            return False, "Not in a conversation."

        conv = self.active_conversation
        if conv.current_question_idx >= len(conv.questions):
            conv.completed = True
            self.active_conversation = None
            return True, "Conversation completed!"

        question = conv.questions[conv.current_question_idx]
        if answer_index < 0 or answer_index >= len(question.answers):
            return False, "Invalid answer choice."

        answer = question.answers[answer_index]

        # Track NPC opinion
        npc_name = conv.npc_name
        if npc_name not in self.npc_opinions:
            self.npc_opinions[npc_name] = 0

        # Determine if this is an enemy (harsher penalties)
        is_enemy = conv.npc_type == NPCType.ENEMY

        if answer.correct:
            # Correct answer!
            self.coherence = min(self.max_coherence, self.coherence + 10)
            self.npc_opinions[npc_name] += 1

            # Award knowledge module
            if answer.reward_knowledge:
                self.knowledge_modules.add(answer.reward_knowledge)
                response = f"{answer.response}\n\n[+10 Coherence] [Gained: {answer.reward_knowledge}]"
            else:
                response = f"{answer.response}\n\n[+10 Coherence]"

            # Move to next question
            conv.current_question_idx += 1

            if conv.current_question_idx >= len(conv.questions):
                conv.completed = True
                # Track quest completion for specialists
                if conv.npc_type == NPCType.SPECIALIST:
                    self.quest_completed_npcs.add(npc_name)
                self.active_conversation = None

                # Add prominent completion message
                separator = "═" * 40
                if is_enemy:
                    response += f"\n\n{separator}\n✓ CONVERSATION COMPLETE ✓\n{separator}\n\n{npc_name}: You have passed my security check. You may proceed."
                else:
                    response += f"\n\n{separator}\n✓ CONVERSATION COMPLETE ✓\n{separator}\n\n{npc_name}: You have proven your worth. I grant you passage."

            return True, response
        else:
            # Wrong answer - use enemy penalty if applicable
            penalty = answer.enemy_penalty if is_enemy else 25
            self.coherence = max(0, self.coherence - penalty)
            self.npc_opinions[npc_name] -= 1

            if is_enemy:
                response = (
                    f"{answer.response}\n\n[CRITICAL ERROR! -{penalty} Coherence]"
                )
            else:
                response = f"{answer.response}\n\n[-{penalty} Coherence]"

            # Check for game over
            if self.coherence <= 0:
                response += "\n\n[SYSTEM FAILURE - COHERENCE LOST]"
                self.active_conversation = None

            return False, response

    def exit_conversation(self):
        """Exit the current conversation"""
        if self.active_conversation:
            self.active_conversation = None
            self.message = "Conversation ended."
            return True
        return False

    def process_command(self, command):
        """Process a command string (for testing). Returns (success, info)"""
        command = command.strip().lower()

        # Handle conversation answers
        if self.active_conversation and command in ["1", "2", "3", "4"]:
            answer_idx = int(command) - 1
            correct, response = self.answer_question(answer_idx)
            return correct, response

        if command in ["up", "w"]:
            return self.move_player(
                0, -1
            ), "moved up" if self.message == "" else self.message
        elif command in ["down", "s"]:
            return self.move_player(
                0, 1
            ), "moved down" if self.message == "" else self.message
        elif command in ["left", "a"]:
            return self.move_player(
                -1, 0
            ), "moved left" if self.message == "" else self.message
        elif command in ["right", "d"]:
            return self.move_player(
                1, 0
            ), "moved right" if self.message == "" else self.message
        elif command in ["interact", "i"]:
            return self.interact(), self.message
        elif command in ["stairs", "use", ">", "<"]:
            return self.use_stairs(), self.message
        elif command in ["exit", "esc"]:
            return self.exit_conversation(), self.message
        else:
            return False, f"Unknown command: {command}"

    def get_state(self):
        """Get current game state for testing/debugging"""
        return {
            "player_pos": (self.player.x, self.player.y),
            "npcs": [(npc.x, npc.y, npc.name) for npc in self.npcs],
            "message": self.message,
            "coherence": self.coherence,
            "knowledge_modules": list(self.knowledge_modules),
            "in_conversation": self.active_conversation is not None,
            "conversation_npc": self.active_conversation.npc_name
            if self.active_conversation
            else None,
        }


def create_simple_map(width, height, floor=1):
    """Create a simple box room with some variety based on floor"""
    tiles = [[" " for _ in range(width)] for _ in range(height)]

    # Draw walls
    for x in range(width):
        tiles[0][x] = "#"
        tiles[height - 1][x] = "#"
    for y in range(height):
        tiles[y][0] = "#"
        tiles[y][width - 1] = "#"

    # Draw some interior walls to make it interesting (varies by floor)
    if floor == 1:
        # Floor 1: Learning space with rooms and corridors
        # Horizontal wall across middle-top
        for x in range(20, 35):
            if x < width:
                tiles[10][x] = "#"
        # Vertical wall creating a room on the left
        for y in range(5, 15):
            if y < height:
                tiles[y][15] = "#"
        # Some pillars/obstacles
        if height > 18 and width > 30:
            tiles[18][30] = "#"
            tiles[18][31] = "#"
            tiles[17][30] = "#"
        # Small horizontal segment on right side
        for x in range(40, 46):
            if x < width:
                tiles[15][x] = "#"
    elif floor == 2:
        # Floor 2: Security segmented space with corridors
        # Original vertical wall
        for y in range(8, 18):
            if y < height:
                tiles[y][25] = "#"
        # Additional vertical wall creating corridors
        for y in range(5, 12):
            if y < height:
                tiles[y][35] = "#"
        # Horizontal walls to create more complexity
        for x in range(15, 25):
            if x < width:
                tiles[15][x] = "#"
        for x in range(30, 40):
            if x < width:
                tiles[20][x] = "#"
        # Small room in corner
        for x in range(10, 15):
            if x < width:
                tiles[8][x] = "#"
        for y in range(8, 12):
            if y < height:
                tiles[y][10] = "#"
    elif floor == 3:
        # Floor 3: Advanced maze-like challenging layout
        # Original walls
        for x in range(15, 40):
            if x < width:
                tiles[12][x] = "#"
        for y in range(5, 12):
            if y < height:
                tiles[y][35] = "#"
        # Additional maze walls
        for y in range(15, 22):
            if y < height:
                tiles[y][20] = "#"
        for x in range(8, 18):
            if x < width:
                tiles[18][x] = "#"
        for y in range(8, 15):
            if y < height:
                tiles[y][10] = "#"
        # Create some narrow passages
        for x in range(25, 35):
            if x < width:
                tiles[8][x] = "#"
        # Corner obstacles
        for x in range(42, 47):
            if x < width:
                tiles[10][x] = "#"
                tiles[17][x] = "#"

    # Floor tiles
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            if tiles[y][x] != "#":
                tiles[y][x] = "."

    return tiles


def draw_completion_overlay(term, game):
    """Draw completion message overlay when conversation is complete"""
    response_text = game._last_answer_response

    # Calculate overlay dimensions (centered, larger for completion)
    overlay_width = min(60, term.width - 4)
    overlay_height = min(30, term.height - 4)
    start_x = (term.width - overlay_width) // 2
    start_y = (term.height - overlay_height) // 2

    # Draw background box
    for y in range(start_y, start_y + overlay_height):
        print(
            term.move_xy(start_x, y) + term.black_on_white(" " * overlay_width), end=""
        )

    # Draw border
    print(
        term.move_xy(start_x, start_y)
        + term.bold_green("┏" + "━" * (overlay_width - 2) + "┓"),
        end="",
    )
    for y in range(start_y + 1, start_y + overlay_height - 1):
        print(term.move_xy(start_x, y) + term.bold_green("┃"), end="")
        print(
            term.move_xy(start_x + overlay_width - 1, y) + term.bold_green("┃"), end=""
        )
    print(
        term.move_xy(start_x, start_y + overlay_height - 1)
        + term.bold_green("┗" + "━" * (overlay_width - 2) + "┛"),
        end="",
    )

    current_y = start_y + 2

    # Big completion banner at top
    banner = "*** CONVERSATION COMPLETE ***"
    print(
        term.move_xy(start_x + (overlay_width - len(banner)) // 2, current_y)
        + term.bold_green(banner),
        end=""
    )
    current_y += 2

    # Draw separator
    sep = "=" * (overlay_width - 4)
    print(
        term.move_xy(start_x + 2, current_y) + term.bold_green(sep), end=""
    )
    current_y += 2

    # Show response text
    lines = wrap_text(response_text, overlay_width - 4)
    for line in lines:
        if current_y < start_y + overlay_height - 3:
            print(term.move_xy(start_x + 2, current_y) + term.black(line), end="")
            current_y += 1
    current_y += 1

    # Instructions at bottom
    if current_y < start_y + overlay_height - 2:
        print(
            term.move_xy(start_x + 2, current_y)
            + term.bold_red("[Press any key to continue]"),
            end="",
        )


def draw_conversation_overlay(term, game):
    """Draw conversation overlay panel"""
    conv = game.active_conversation

    # If no active conversation, check if we have a completion response to show
    if not conv:
        if hasattr(game, "_last_answer_response") and game._last_answer_response:
            # Show completion response without active conversation
            # We need to create a temporary overlay just for the completion message
            draw_completion_overlay(term, game)
        return

    # Calculate overlay dimensions (centered)
    overlay_width = min(60, term.width - 4)
    overlay_height = min(25, term.height - 4)
    start_x = (term.width - overlay_width) // 2
    start_y = (term.height - overlay_height) // 2

    # Draw background box with dark background
    for y in range(start_y, start_y + overlay_height):
        print(
            term.move_xy(start_x, y) + term.black_on_white(" " * overlay_width), end=""
        )

    # Draw border
    print(
        term.move_xy(start_x, start_y)
        + term.bold_blue("┏" + "━" * (overlay_width - 2) + "┓"),
        end="",
    )
    for y in range(start_y + 1, start_y + overlay_height - 1):
        print(term.move_xy(start_x, y) + term.bold_blue("┃"), end="")
        print(
            term.move_xy(start_x + overlay_width - 1, y) + term.bold_blue("┃"), end=""
        )
    print(
        term.move_xy(start_x, start_y + overlay_height - 1)
        + term.bold_blue("┗" + "━" * (overlay_width - 2) + "┛"),
        end="",
    )

    # NPC name header
    header = f" {conv.npc_name} "
    print(term.move_xy(start_x + 2, start_y) + term.bold_magenta(header), end="")

    current_y = start_y + 2

    # If showing greeting
    if hasattr(game, "_show_greeting") and game._show_greeting:
        # Show greeting
        lines = wrap_text(conv.greeting, overlay_width - 4)
        for line in lines:
            if current_y < start_y + overlay_height - 2:
                print(term.move_xy(start_x + 2, current_y) + term.black(line), end="")
                current_y += 1
        current_y += 1

        if current_y < start_y + overlay_height - 2:
            print(
                term.move_xy(start_x + 2, current_y)
                + term.bold_red("[Press any key to continue]"),
                end="",
            )
        return

    # Check if we have a pending response to show
    if hasattr(game, "_last_answer_response") and game._last_answer_response:
        response_text = game._last_answer_response

        # Check if this is a completion response
        is_completion = "CONVERSATION COMPLETE" in response_text

        if is_completion:
            # Make completion VERY obvious with special rendering
            # Use larger overlay for completion
            overlay_height = min(30, term.height - 4)

            # Redraw background and border with new height
            for y in range(start_y, start_y + overlay_height):
                print(
                    term.move_xy(start_x, y) + term.black_on_white(" " * overlay_width), end=""
                )

            print(
                term.move_xy(start_x, start_y)
                + term.bold_blue("┏" + "━" * (overlay_width - 2) + "┓"),
                end="",
            )
            for y in range(start_y + 1, start_y + overlay_height - 1):
                print(term.move_xy(start_x, y) + term.bold_blue("┃"), end="")
                print(
                    term.move_xy(start_x + overlay_width - 1, y) + term.bold_blue("┃"), end=""
                )
            print(
                term.move_xy(start_x, start_y + overlay_height - 1)
                + term.bold_blue("┗" + "━" * (overlay_width - 2) + "┛"),
                end="",
            )

            current_y = start_y + 2

            # Big completion banner at top
            banner = "*** CONVERSATION COMPLETE ***"
            print(
                term.move_xy(start_x + (overlay_width - len(banner)) // 2, current_y)
                + term.bold_green(banner),
                end=""
            )
            current_y += 2

            # Draw separator
            sep = "=" * (overlay_width - 4)
            print(
                term.move_xy(start_x + 2, current_y) + term.bold_green(sep), end=""
            )
            current_y += 2
        else:
            # Normal response - draw separator line
            separator = "─" * (overlay_width - 4)
            print(
                term.move_xy(start_x + 2, current_y) + term.bold_blue(separator), end=""
            )
            current_y += 1

            # Show "RESPONSE:" header
            print(
                term.move_xy(start_x + 2, current_y) + term.bold_green("RESPONSE:"), end=""
            )
            current_y += 2

        # Show response text
        lines = wrap_text(response_text, overlay_width - 4)
        for line in lines:
            if current_y < start_y + overlay_height - 3:
                print(term.move_xy(start_x + 2, current_y) + term.black(line), end="")
                current_y += 1
        current_y += 1

        if current_y < start_y + overlay_height - 2:
            print(
                term.move_xy(start_x + 2, current_y)
                + term.bold_red("[Press any key to continue]"),
                end="",
            )
        return

    # Show current question
    if conv.current_question_idx < len(conv.questions):
        question = conv.questions[conv.current_question_idx]

        # Question text
        q_text = f"Q{conv.current_question_idx + 1}/{len(conv.questions)}: {question.question_text}"
        lines = wrap_text(q_text, overlay_width - 4)
        for line in lines:
            if current_y < start_y + overlay_height - 4:
                print(
                    term.move_xy(start_x + 2, current_y) + term.bold_black(line), end=""
                )
                current_y += 1

        current_y += 1

        # Answer choices
        for i, answer in enumerate(question.answers):
            if current_y < start_y + overlay_height - 2:
                choice_text = f"{i + 1}. {answer.text}"
                lines = wrap_text(choice_text, overlay_width - 4)
                for line in lines:
                    if current_y < start_y + overlay_height - 2:
                        print(
                            term.move_xy(start_x + 2, current_y) + term.blue(line),
                            end="",
                        )
                        current_y += 1

        # Instructions at bottom
        print(
            term.move_xy(start_x + 2, start_y + overlay_height - 2)
            + term.bold_red("Press 1-4 to answer | ESC to exit"),
            end="",
        )


def wrap_text(text, width):
    """Wrap text to fit within width"""
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        # Calculate what the line length would be if we add this word
        test_line = current_line + [word]
        test_length = sum(len(w) for w in test_line) + len(test_line) - 1  # -1 because n words need n-1 spaces

        if test_length > width and current_line:
            # Line would be too long, save current line and start new one
            lines.append(" ".join(current_line))
            current_line = [word]
        else:
            # Word fits, add it
            current_line.append(word)

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def draw_game(term, game, redraw_all=False):
    """Draw the entire game state"""
    if redraw_all:
        # Only clear on first draw
        print(term.home + term.clear, end="")

        # Draw map
        for y in range(len(game.game_map)):
            for x in range(len(game.game_map[0])):
                char = game.game_map[y][x]
                if char == "#":
                    # Bold blue works on both light and dark backgrounds
                    print(term.move_xy(x, y) + term.bold_blue(char), end="")
                elif char == ".":
                    # Cyan dots are visible on both themes
                    print(term.move_xy(x, y) + term.cyan(char), end="")
    else:
        # Clear old player position
        if game.old_player_pos:
            old_x, old_y = game.old_player_pos
            char = game.game_map[old_y][old_x]
            if char == ".":
                print(term.move_xy(old_x, old_y) + term.cyan(char), end="")

    # Draw all NPCs with their colors
    for npc in game.npcs:
        npc_color = getattr(term, f"bold_{npc.color}", term.bold_magenta)
        print(term.move_xy(npc.x, npc.y) + npc_color(npc.char), end="")

    # Draw terminals
    for terminal in game.terminals:
        terminal_color = getattr(term, f"bold_{terminal.color}", term.bold_cyan)
        print(term.move_xy(terminal.x, terminal.y) + terminal_color(terminal.char), end="")

    # Draw gates (show differently if locked vs unlocked)
    for gate in game.gates:
        if gate.unlocked:
            # Show unlocked gates as open (dim/faded)
            print(term.move_xy(gate.x, gate.y) + term.green("·"), end="")
        else:
            # Show locked gates as solid blocks
            gate_color = getattr(term, f"bold_{gate.color}", term.bold_magenta)
            print(term.move_xy(gate.x, gate.y) + gate_color(gate.char), end="")

    # Draw stairs
    for stair in game.stairs:
        stair_color = getattr(term, f"bold_{stair.color}", term.bold_yellow)
        print(term.move_xy(stair.x, stair.y) + stair_color(stair.char), end="")

    # Draw player - bold green stands out on both themes
    print(
        term.move_xy(game.player.x, game.player.y) + term.bold_green(game.player.char),
        end="",
    )

    # Draw UI at bottom
    ui_y = term.height - 4
    # Use bold for separator to be visible on both themes
    print(term.move_xy(0, ui_y) + term.bold("─" * min(term.width, 80)), end="")

    # Show coherence and knowledge count
    coherence_pct = int((game.coherence / game.max_coherence) * 100)
    knowledge_count = len(game.knowledge_modules)
    status_line = f"Neural Layer {game.current_floor}/{game.max_floors} | Coherence: {coherence_pct}% | Knowledge: {knowledge_count}"
    print(term.move_xy(2, ui_y + 1) + term.bold(status_line), end="")

    # Clear message line before writing
    print(term.move_xy(2, ui_y + 2) + " " * (term.width - 4), end="")
    print(
        term.move_xy(2, ui_y + 2) + term.bold_yellow(game.message[: term.width - 4]),
        end="",
    )

    # Instructions - normal text adapts to terminal theme
    if game.active_conversation:
        print(
            term.move_xy(0, term.height - 1)
            + term.normal
            + "In conversation - see overlay above",
            end="",
        )
    else:
        print(
            term.move_xy(0, term.height - 1)
            + term.normal
            + "Move: Arrows | Interact: Space/Enter | Stairs: >/< | Q: Quit",
            end="",
        )

    # Draw conversation overlay if active OR if we have a response to show
    if game.active_conversation or (hasattr(game, "_last_answer_response") and game._last_answer_response):
        draw_conversation_overlay(term, game)

    # Draw terminal overlay if active
    if game.active_terminal:
        draw_terminal_overlay(term, game)

    sys.stdout.flush()


def draw_terminal_overlay(term, game):
    """Draw terminal info overlay"""
    terminal = game.active_terminal
    if not terminal:
        return

    # Calculate overlay dimensions (centered)
    overlay_width = min(60, term.width - 4)
    overlay_height = min(20, term.height - 4)
    start_x = (term.width - overlay_width) // 2
    start_y = (term.height - overlay_height) // 2

    # Draw background box
    for y in range(start_y, start_y + overlay_height):
        print(
            term.move_xy(start_x, y) + term.black_on_white(" " * overlay_width), end=""
        )

    # Draw border
    print(
        term.move_xy(start_x, start_y)
        + term.bold_cyan("┏" + "━" * (overlay_width - 2) + "┓"),
        end="",
    )
    for y in range(start_y + 1, start_y + overlay_height - 1):
        print(term.move_xy(start_x, y) + term.bold_cyan("┃"), end="")
        print(
            term.move_xy(start_x + overlay_width - 1, y) + term.bold_cyan("┃"), end=""
        )
    print(
        term.move_xy(start_x, start_y + overlay_height - 1)
        + term.bold_cyan("┗" + "━" * (overlay_width - 2) + "┛"),
        end="",
    )

    # Terminal title header
    header = f" {terminal.title} "
    print(term.move_xy(start_x + 2, start_y) + term.bold_green(header), end="")

    current_y = start_y + 2

    # Show content
    for line in terminal.content:
        wrapped_lines = wrap_text(line, overlay_width - 4)
        for wrapped_line in wrapped_lines:
            if current_y < start_y + overlay_height - 2:
                print(term.move_xy(start_x + 2, current_y) + term.black(wrapped_line), end="")
                current_y += 1

    # Instructions at bottom
    print(
        term.move_xy(start_x + 2, start_y + overlay_height - 2)
        + term.bold_red("[Press ESC or any key to close]"),
        end="",
    )


def run_interactive(game):
    """Run the game in interactive mode with terminal UI"""
    term = Terminal()
    first_draw = True

    try:
        with term.cbreak(), term.hidden_cursor():
            while True:
                # Check for game over
                if game.coherence <= 0:
                    draw_game(term, game, redraw_all=first_draw)
                    print(
                        term.move_xy(0, term.height // 2)
                        + term.center(
                            term.bold_red("SYSTEM FAILURE - COHERENCE LOST")
                        ).rstrip()
                    )
                    print(
                        term.move_xy(0, term.height // 2 + 2)
                        + term.center("Press Q to quit").rstrip()
                    )
                    sys.stdout.flush()

                    while True:
                        key = term.inkey(timeout=0.1)
                        if key and key.lower() == "q":
                            break
                    break

                # Draw everything
                draw_game(term, game, redraw_all=first_draw)
                first_draw = False

                # Get input
                key = term.inkey(timeout=0.1)

                if not key:
                    continue

                if key.lower() == "q" and not game.active_conversation and not game.active_terminal:
                    break

                # In terminal reading mode
                if game.active_terminal:
                    # Any key closes terminal
                    game.active_terminal = None
                    first_draw = True  # Force redraw to clear overlay
                    continue

                # In conversation mode
                if game.active_conversation:
                    # If showing greeting or response, any key continues
                    if hasattr(game, "_show_greeting") and game._show_greeting:
                        # Dismiss greeting
                        game._show_greeting = False
                        continue

                    if (
                        hasattr(game, "_last_answer_response")
                        and game._last_answer_response
                    ):
                        # Dismiss response and continue to next question
                        game._last_answer_response = None
                        continue

                    # Handle answer selection (1-4)
                    if key in ["1", "2", "3", "4"]:
                        answer_idx = int(key) - 1
                        correct, response = game.answer_question(answer_idx)
                        game._last_answer_response = response
                        continue

                    # ESC exits conversation
                    if key.name == "KEY_ESCAPE" or key.lower() == "x":
                        game.exit_conversation()
                        if hasattr(game, "_last_answer_response"):
                            del game._last_answer_response
                        if hasattr(game, "_show_greeting"):
                            del game._show_greeting
                        first_draw = True  # Force redraw to clear overlay
                        continue

                # Check if conversation just ended (we have a response but no active conversation)
                elif (
                    hasattr(game, "_last_answer_response")
                    and game._last_answer_response
                ):
                    # Show final message, then clear everything
                    game._last_answer_response = None
                    first_draw = True  # Force full redraw to clear overlay
                    continue

                # Normal movement mode
                else:
                    if key.name == "KEY_UP":
                        game.move_player(0, -1)
                    elif key.name == "KEY_DOWN":
                        game.move_player(0, 1)
                    elif key.name == "KEY_LEFT":
                        game.move_player(-1, 0)
                    elif key.name == "KEY_RIGHT":
                        game.move_player(1, 0)
                    elif key in [">", "."]:
                        # Try stairs first, then interact
                        if not game.use_stairs():
                            game.interact()
                        else:
                            first_draw = True  # Force redraw on floor change
                    elif key in ["<", ","]:
                        # Try stairs first, then interact
                        if not game.use_stairs():
                            game.interact()
                        else:
                            first_draw = True  # Force redraw on floor change
                    elif key.lower() == "i" or key == " " or key.name == "KEY_ENTER":
                        # Try interaction first, then stairs
                        result = game.interact()
                        if result and game.active_conversation:
                            # Starting conversation - reset state
                            game._show_greeting = True
                            game._last_answer_response = None
                        elif not result:
                            # No NPC nearby, try stairs
                            if game.use_stairs():
                                first_draw = True  # Force redraw on floor change

    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        pass
    finally:
        # Clear screen on exit
        print(term.home + term.clear)


def run_test_mode():
    """Run in test mode - process commands from stdin"""
    # Use fixed NPC positions and seed for reproducible testing
    game = Game(map_width=50, map_height=25, random_npcs=False, seed=42)

    print("# Neural Dive Test Mode")
    print(f"# Initial state: {game.get_state()}")
    print("#")

    for line in sys.stdin:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        success, info = game.process_command(line)
        state = game.get_state()
        print(f"Command: {line}")
        print(f"Success: {success}")
        print(f"Info: {info}")
        print(f"State: {state}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Neural Dive - Cyberpunk roguelike")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode (reads commands from stdin)",
    )
    parser.add_argument("--seed", type=int, help="Random seed for NPC placement")
    parser.add_argument(
        "--fixed", action="store_true", help="Use fixed NPC positions instead of random"
    )
    args = parser.parse_args()

    if args.test:
        run_test_mode()
    else:
        term = Terminal()
        # Smaller map that fits better
        map_width = min(50, term.width)
        map_height = min(25, term.height - 6)
        random_npcs = not args.fixed
        game = Game(
            map_width=map_width,
            map_height=map_height,
            random_npcs=random_npcs,
            seed=args.seed,
        )
        run_interactive(game)


if __name__ == "__main__":
    main()
