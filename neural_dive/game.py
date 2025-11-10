"""
Game logic and state management for Neural Dive.

This module contains the main Game class that manages:
- Game state (player, NPCs, map, floors)
- Player movement and interactions
- Conversation system
- Floor progression
- Knowledge and quest systems
"""

import random
import copy
from typing import Optional, Dict, Set, List, Tuple

from neural_dive.config import (
    DEFAULT_MAP_WIDTH,
    DEFAULT_MAP_HEIGHT,
    MAX_FLOORS,
    STARTING_COHERENCE,
    MAX_COHERENCE,
    CORRECT_ANSWER_COHERENCE_GAIN,
    WRONG_ANSWER_COHERENCE_PENALTY,
    ENEMY_WRONG_ANSWER_PENALTY,
    HELPER_COHERENCE_RESTORE,
    QUEST_COMPLETION_COHERENCE_BONUS,
    PLAYER_START_X,
    PLAYER_START_Y,
    STAIRS_DOWN_DEFAULT_X,
    STAIRS_DOWN_DEFAULT_Y,
    STAIRS_UP_DEFAULT_X,
    STAIRS_UP_DEFAULT_Y,
    NPC_MIN_DISTANCE_FROM_PLAYER,
    NPC_PLACEMENT_ATTEMPTS,
    TERMINAL_PLACEMENT_ATTEMPTS,
    TERMINAL_X_OFFSET,
    TERMINAL_Y_OFFSET,
    TERMINAL_X_BONUS,
    TERMINAL_Y_BONUS,
    GATE_PLACEMENT_ATTEMPTS,
    GATE_X_OFFSET,
    GATE_Y_OFFSET,
    FLOOR_REQUIRED_NPCS,
    QUEST_TARGET_NPCS,
)
from neural_dive.entities import Entity, Stairs, InfoTerminal, Gate
from neural_dive.models import Conversation, Question, Answer
from neural_dive.enums import NPCType
from neural_dive.map_generation import create_map
from neural_dive.data_loader import load_all_game_data
from neural_dive.conversation import create_randomized_conversation


class Game:
    """
    Main game state and logic manager.

    Handles all game state including player position, NPCs, conversations,
    floor progression, and game mechanics like knowledge modules and quests.
    """

    def __init__(
        self,
        map_width: int = DEFAULT_MAP_WIDTH,
        map_height: int = DEFAULT_MAP_HEIGHT,
        random_npcs: bool = True,
        seed: Optional[int] = None,
        max_floors: int = MAX_FLOORS,
    ):
        """
        Initialize a new game.

        Args:
            map_width: Width of the game map in tiles
            map_height: Height of the game map in tiles
            random_npcs: Whether to randomize NPC and entity positions
            seed: Random seed for reproducibility (None for random)
            max_floors: Maximum number of floors/layers in the game
        """
        # Set up randomization
        if seed is not None:
            random.seed(seed)
        self.rand = random

        # Game dimensions and settings
        self.map_width = map_width
        self.map_height = map_height
        self.max_floors = max_floors
        self.current_floor = 1
        self.random_npcs = random_npcs

        # Load all game data from JSON files
        self.questions, self.npc_data, self.terminal_data = load_all_game_data()

        # Initialize game map
        self.game_map = create_map(map_width, map_height, self.current_floor)

        # Create player entity
        self.player = Entity(PLAYER_START_X, PLAYER_START_Y, "@", "cyan", "Data Runner")
        self.old_player_pos: Optional[Tuple[int, int]] = None

        # Current floor entities
        self.npcs: List[Entity] = []
        self.stairs: List[Stairs] = []
        self.terminals: List[InfoTerminal] = []
        self.gates: List[Gate] = []

        # All NPCs across all floors (for persistence)
        self.all_npcs: List[Entity] = []

        # Initialize conversation system
        self.active_conversation: Optional[Conversation] = None
        self.active_terminal: Optional[InfoTerminal] = None
        self.npc_conversations: Dict[str, Conversation] = {}

        # Initialize NPC conversations with randomization
        for npc_name, npc_info in self.npc_data.items():
            conv_template = npc_info["conversation"]
            # Create randomized copy for each NPC
            self.npc_conversations[npc_name] = create_randomized_conversation(
                conv_template,
                randomize_question_order=True,
                randomize_answer_order=True,
            )

        # Player stats
        self.coherence = STARTING_COHERENCE
        self.max_coherence = MAX_COHERENCE
        self.knowledge_modules: Set[str] = set()

        # NPC relationship tracking
        self.npc_opinions: Dict[str, int] = {}

        # Quest system
        self.quest_active = False
        self.quest_completed_npcs: Set[str] = set()

        # UI message
        self.message = (
            f"Welcome to Neural Dive! Descend through {max_floors} neural layers. "
            "Beware the Virus Hunter on Layer 3!"
        )

        # Generate the first floor
        self._generate_floor()

    def _generate_floor(self):
        """
        Generate all entities (NPCs, terminals, stairs, gates) for the current floor.

        This method is called when entering a new floor or starting the game.
        It clears existing floor entities and creates new ones based on the current floor.
        """
        # Clear current floor entities
        self.npcs = []
        self.stairs = []
        self.terminals = []
        self.gates = []

        # Generate NPCs for this floor
        self._generate_npcs()

        # Generate terminals for this floor
        self._generate_terminals()

        # Generate stairs
        self._generate_stairs()

        # Generate knowledge gates
        self._generate_gates()

    def _generate_npcs(self):
        """Generate and place NPCs for the current floor."""
        # Get NPCs for this floor
        floor_npcs = [
            (npc_name, npc_info)
            for npc_name, npc_info in self.npc_data.items()
            if npc_info["floor"] == self.current_floor
        ]

        if self.random_npcs:
            # Random placement
            for npc_name, npc_info in floor_npcs:
                for _ in range(NPC_PLACEMENT_ATTEMPTS):
                    x = self.rand.randint(10, self.map_width - 2)
                    y = self.rand.randint(5, self.map_height - 2)

                    # Check not too close to player and not a wall
                    if (
                        self.game_map[y][x] != "#"
                        and (
                            abs(x - self.player.x) > NPC_MIN_DISTANCE_FROM_PLAYER
                            or abs(y - self.player.y) > NPC_MIN_DISTANCE_FROM_PLAYER
                        )
                    ):
                        npc = Entity(
                            x, y,
                            npc_info["char"],
                            npc_info["color"],
                            npc_name
                        )
                        self.npcs.append(npc)

                        # Add to all_npcs if not already there
                        if not any(n.name == npc_name for n in self.all_npcs):
                            self.all_npcs.append(npc)
                        break
        else:
            # Fixed positions for testing
            positions = [
                (15, 8), (35, 8), (25, 12), (40, 15),
                (10, 18), (45, 12), (30, 20),
            ]

            for i, (npc_name, npc_info) in enumerate(floor_npcs):
                if i < len(positions):
                    x, y = positions[i]
                    npc = Entity(
                        x, y,
                        npc_info["char"],
                        npc_info["color"],
                        npc_name
                    )
                    self.npcs.append(npc)

                    if not any(n.name == npc_name for n in self.all_npcs):
                        self.all_npcs.append(npc)

    def _generate_terminals(self):
        """Generate and place info terminals for the current floor."""
        # Terminal definitions by floor
        terminal_defs = {
            1: [("big_o_hint", 8, 8), ("lore_layer1", 12, 10)],
            2: [("data_structures", 8, 8), ("tcp_hint", 12, 10), ("lore_layer2", 8, 12)],
            3: [("concurrency_hint", 8, 8)],
        }

        if self.current_floor not in terminal_defs:
            return

        for terminal_key, x, y in terminal_defs[self.current_floor]:
            if terminal_key not in self.terminal_data:
                continue

            data = self.terminal_data[terminal_key]

            # Randomize position slightly if random mode
            if self.random_npcs:
                for _ in range(TERMINAL_PLACEMENT_ATTEMPTS):
                    # Keep terminals close to start area
                    tx = self.rand.randint(
                        max(2, x - TERMINAL_X_OFFSET),
                        min(self.map_width - 2, x + TERMINAL_X_BONUS)
                    )
                    ty = self.rand.randint(
                        max(2, y - TERMINAL_Y_OFFSET),
                        min(self.map_height - 2, y + TERMINAL_Y_BONUS)
                    )
                    if self.game_map[ty][tx] != "#":
                        x, y = tx, ty
                        break

            terminal = InfoTerminal(x, y, data["title"], data["content"])
            self.terminals.append(terminal)

    def _generate_stairs(self):
        """Generate stairs up and/or down based on current floor."""
        # Stairs down (if not on bottom floor)
        if self.current_floor < self.max_floors:
            if self.random_npcs:
                for _ in range(NPC_PLACEMENT_ATTEMPTS):
                    x = self.rand.randint(self.map_width // 2, self.map_width - 2)
                    y = self.rand.randint(self.map_height // 2, self.map_height - 2)
                    if self.game_map[y][x] != "#" and abs(x - self.player.x) > 10:
                        self.stairs.append(Stairs(x, y, "down"))
                        break
            else:
                self.stairs.append(
                    Stairs(STAIRS_DOWN_DEFAULT_X, STAIRS_DOWN_DEFAULT_Y, "down")
                )

        # Stairs up (if not on top floor)
        if self.current_floor > 1:
            if self.random_npcs:
                for _ in range(NPC_PLACEMENT_ATTEMPTS):
                    x = self.rand.randint(2, self.map_width // 3)
                    y = self.rand.randint(2, self.map_height // 3)
                    if self.game_map[y][x] != "#":
                        self.stairs.append(Stairs(x, y, "up"))
                        break
            else:
                self.stairs.append(
                    Stairs(STAIRS_UP_DEFAULT_X, STAIRS_UP_DEFAULT_Y, "up")
                )

    def _generate_gates(self):
        """Generate knowledge-locked gates for the current floor."""
        # Gate definitions by floor
        gate_defs = {
            1: [("binary_search", 35, 12)],
            2: [("hashing", 20, 10), ("trees", 35, 15)],
            3: [],  # No gates on final floor
        }

        if self.current_floor not in gate_defs:
            return

        for required_knowledge, x, y in gate_defs[self.current_floor]:
            # Randomize position slightly if random mode
            if self.random_npcs:
                for _ in range(GATE_PLACEMENT_ATTEMPTS):
                    gx = self.rand.randint(
                        max(2, x - GATE_X_OFFSET),
                        min(self.map_width - 2, x + GATE_X_OFFSET)
                    )
                    gy = self.rand.randint(
                        max(2, y - GATE_Y_OFFSET),
                        min(self.map_height - 2, y + GATE_Y_OFFSET)
                    )
                    if self.game_map[gy][gx] != "#":
                        x, y = gx, gy
                        break

            gate = Gate(x, y, required_knowledge)
            self.gates.append(gate)

    def is_walkable(self, x: int, y: int) -> bool:
        """
        Check if a position is walkable.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            True if the position can be walked on, False otherwise
        """
        # Check bounds
        if y < 0 or y >= len(self.game_map):
            return False
        if x < 0 or x >= len(self.game_map[0]):
            return False

        # Check for walls
        if self.game_map[y][x] == "#":
            return False

        # Check for locked gates
        for gate in self.gates:
            if gate.x == x and gate.y == y and not gate.unlocked:
                return False

        return True

    def move_player(self, dx: int, dy: int) -> bool:
        """
        Attempt to move the player by a delta.

        Args:
            dx: Change in x position
            dy: Change in y position

        Returns:
            True if movement was successful, False otherwise
        """
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
                        self.message = (
                            f"Gate unlocked with [{gate.required_knowledge}] knowledge!"
                        )
                        return False  # Don't move yet, just show message
                    else:
                        self.message = (
                            f"Gate locked! Requires [{gate.required_knowledge}] knowledge."
                        )
                        return False

        # Try to move
        if self.is_walkable(new_x, new_y):
            self.old_player_pos = (self.player.x, self.player.y)
            self.player.x = new_x
            self.player.y = new_y
            self.message = ""
            return True
        else:
            self.message = "Blocked by firewall!"
            return False

    def interact(self) -> bool:
        """
        Attempt to interact with nearby entity (terminal or NPC).

        Returns:
            True if interaction was successful, False otherwise
        """
        # Check terminals first
        for terminal in self.terminals:
            if (
                abs(self.player.x - terminal.x) <= 1
                and abs(self.player.y - terminal.y) <= 1
            ):
                # Show terminal content
                self.active_terminal = terminal
                self.message = f"Reading: {terminal.title}"
                return True

        # Check NPCs
        for npc in self.npcs:
            if (
                abs(self.player.x - npc.x) <= 1
                and abs(self.player.y - npc.y) <= 1
            ):
                return self._interact_with_npc(npc)

        self.message = "No one nearby to interact with. Look for NPCs or Terminals (T)."
        return False

    def _interact_with_npc(self, npc: Entity) -> bool:
        """
        Handle interaction with a specific NPC.

        Args:
            npc: The NPC entity to interact with

        Returns:
            True if interaction occurred, False otherwise
        """
        npc_name = npc.name
        conversation = self.npc_conversations.get(npc_name)

        if not conversation:
            self.message = f"{npc_name}: I have nothing to say."
            return False

        # Handle helper NPCs (restore coherence)
        if conversation.npc_type == NPCType.HELPER and not conversation.completed:
            self.coherence = min(self.max_coherence, self.coherence + HELPER_COHERENCE_RESTORE)
            conversation.completed = True
            self.message = (
                f"{npc_name}: Your coherence has been restored. "
                f"[+{HELPER_COHERENCE_RESTORE} Coherence]"
            )
            return True

        # Handle quest NPCs
        if conversation.npc_type == NPCType.QUEST:
            return self._handle_quest_npc(npc_name, conversation)

        # Standard interaction for specialists and enemies
        if not conversation.completed:
            self.active_conversation = conversation
            self.message = conversation.greeting
            return True
        else:
            self.message = (
                f"{npc_name}: You have proven yourself. "
                "We have nothing more to discuss."
            )
            return True

    def _handle_quest_npc(self, npc_name: str, conversation: Conversation) -> bool:
        """
        Handle interaction with a quest-giving NPC.

        Args:
            npc_name: Name of the quest NPC
            conversation: The NPC's conversation

        Returns:
            True if interaction occurred
        """
        if not conversation.completed:
            # Start quest
            self.quest_active = True
            self.active_conversation = conversation
            self.message = conversation.greeting
            return True
        else:
            # Check quest completion
            if QUEST_TARGET_NPCS.issubset(self.quest_completed_npcs):
                self.message = (
                    f"{npc_name}: You have completed my quest! "
                    f"The knowledge is yours. [Quest Complete! "
                    f"+{QUEST_COMPLETION_COHERENCE_BONUS} Coherence]"
                )
                self.coherence = min(
                    self.max_coherence,
                    self.coherence + QUEST_COMPLETION_COHERENCE_BONUS
                )
            else:
                remaining = QUEST_TARGET_NPCS - self.quest_completed_npcs
                self.message = (
                    f"{npc_name}: Seek these guardians still: {', '.join(remaining)}"
                )
            return True

    def is_floor_complete(self) -> bool:
        """
        Check if the current floor's objectives are complete.

        Returns:
            True if all required NPCs have been talked to, False otherwise
        """
        required = FLOOR_REQUIRED_NPCS.get(self.current_floor, set())

        # Check if all required NPCs have been completed
        for npc_name in required:
            conv = self.npc_conversations.get(npc_name)
            if not conv or not conv.completed:
                return False

        return True

    def use_stairs(self) -> bool:
        """
        Attempt to use stairs at the player's current position.

        Returns:
            True if stairs were used successfully, False otherwise
        """
        # Check if player is standing on stairs
        for stair in self.stairs:
            if self.player.x == stair.x and self.player.y == stair.y:
                if stair.direction == "down":
                    return self._descend_stairs()
                elif stair.direction == "up":
                    return self._ascend_stairs()

        self.message = "No stairs here. Stand on stairs (> or <) and press Enter."
        return False

    def _descend_stairs(self) -> bool:
        """
        Descend to the next floor.

        Returns:
            True if descent was successful, False otherwise
        """
        if self.current_floor >= self.max_floors:
            self.message = "No deeper layers exist."
            return False

        # Check if floor objectives are complete
        if not self.is_floor_complete():
            required = FLOOR_REQUIRED_NPCS.get(self.current_floor, set())
            incomplete = [
                npc
                for npc in required
                if not self.npc_conversations.get(npc) or not self.npc_conversations[npc].completed
            ]
            self.message = (
                f"Cannot descend! Complete conversations with: {', '.join(incomplete)}"
            )
            return False

        # Descend
        self.current_floor += 1
        self.game_map = create_map(self.map_width, self.map_height, self.current_floor)
        self.player.x = STAIRS_UP_DEFAULT_X
        self.player.y = STAIRS_UP_DEFAULT_Y
        self._generate_floor()
        self.message = f"Descended to Neural Layer {self.current_floor}"
        return True

    def _ascend_stairs(self) -> bool:
        """
        Ascend to the previous floor.

        Returns:
            True if ascent was successful, False otherwise
        """
        if self.current_floor <= 1:
            self.message = "This is the top layer."
            return False

        # Ascend
        self.current_floor -= 1
        self.game_map = create_map(self.map_width, self.map_height, self.current_floor)
        self.player.x = STAIRS_DOWN_DEFAULT_X
        self.player.y = STAIRS_DOWN_DEFAULT_Y
        self._generate_floor()
        self.message = f"Ascended to Neural Layer {self.current_floor}"
        return True

    def answer_question(self, answer_index: int) -> Tuple[bool, str]:
        """
        Answer the current conversation question.

        Args:
            answer_index: Index of the selected answer (0-based)

        Returns:
            Tuple of (correct, response_message)
        """
        if not self.active_conversation:
            return False, "Not in a conversation."

        conv = self.active_conversation

        # Check if conversation is already complete
        if conv.current_question_idx >= len(conv.questions):
            conv.completed = True
            self.active_conversation = None
            return True, "Conversation completed!"

        # Get current question
        question = conv.questions[conv.current_question_idx]

        # Validate answer index
        if answer_index < 0 or answer_index >= len(question.answers):
            return False, "Invalid answer choice."

        answer = question.answers[answer_index]

        # Track NPC opinion
        npc_name = conv.npc_name
        if npc_name not in self.npc_opinions:
            self.npc_opinions[npc_name] = 0

        # Check if this is an enemy (harsher penalties)
        is_enemy = conv.npc_type == NPCType.ENEMY

        if answer.correct:
            return self._handle_correct_answer(conv, answer, npc_name, is_enemy)
        else:
            return self._handle_wrong_answer(conv, answer, npc_name, is_enemy)

    def _handle_correct_answer(
        self,
        conv: Conversation,
        answer: Answer,
        npc_name: str,
        is_enemy: bool
    ) -> Tuple[bool, str]:
        """
        Handle a correct answer.

        Args:
            conv: The conversation
            answer: The correct answer
            npc_name: Name of the NPC
            is_enemy: Whether the NPC is an enemy

        Returns:
            Tuple of (True, response_message)
        """
        # Update stats
        self.coherence = min(
            self.max_coherence,
            self.coherence + CORRECT_ANSWER_COHERENCE_GAIN
        )
        self.npc_opinions[npc_name] += 1

        # Build response
        response = answer.response

        # Award knowledge module
        if answer.reward_knowledge:
            self.knowledge_modules.add(answer.reward_knowledge)
            response += (
                f"\n\n[+{CORRECT_ANSWER_COHERENCE_GAIN} Coherence] "
                f"[Gained: {answer.reward_knowledge}]"
            )
        else:
            response += f"\n\n[+{CORRECT_ANSWER_COHERENCE_GAIN} Coherence]"

        # Move to next question
        conv.current_question_idx += 1

        # Check if conversation is complete
        if conv.current_question_idx >= len(conv.questions):
            conv.completed = True

            # Track quest completion for specialists
            if conv.npc_type == NPCType.SPECIALIST:
                self.quest_completed_npcs.add(npc_name)

            self.active_conversation = None

            # Add completion banner
            separator = "═" * 40
            if is_enemy:
                response += (
                    f"\n\n{separator}\n✓ CONVERSATION COMPLETE ✓\n{separator}\n\n"
                    f"{npc_name}: You have passed my security check. You may proceed."
                )
            else:
                response += (
                    f"\n\n{separator}\n✓ CONVERSATION COMPLETE ✓\n{separator}\n\n"
                    f"{npc_name}: You have proven your worth. I grant you passage."
                )

        return True, response

    def _handle_wrong_answer(
        self,
        conv: Conversation,
        answer: Answer,
        npc_name: str,
        is_enemy: bool
    ) -> Tuple[bool, str]:
        """
        Handle a wrong answer.

        Args:
            conv: The conversation
            answer: The wrong answer
            npc_name: Name of the NPC
            is_enemy: Whether the NPC is an enemy

        Returns:
            Tuple of (False, response_message)
        """
        # Calculate penalty
        penalty = answer.enemy_penalty if is_enemy else WRONG_ANSWER_COHERENCE_PENALTY

        # Update stats
        self.coherence = max(0, self.coherence - penalty)
        self.npc_opinions[npc_name] -= 1

        # Build response
        if is_enemy:
            response = f"{answer.response}\n\n[CRITICAL ERROR! -{penalty} Coherence]"
        else:
            response = f"{answer.response}\n\n[-{penalty} Coherence]"

        # Check for game over
        if self.coherence <= 0:
            response += "\n\n[SYSTEM FAILURE - COHERENCE LOST]"
            self.active_conversation = None

        return False, response

    def exit_conversation(self) -> bool:
        """
        Exit the current conversation.

        Returns:
            True if a conversation was exited, False otherwise
        """
        if self.active_conversation:
            self.active_conversation = None
            self.message = "Conversation ended."
            return True
        return False

    def process_command(self, command: str) -> Tuple[bool, str]:
        """
        Process a text command (primarily for testing).

        Args:
            command: The command string to process

        Returns:
            Tuple of (success, info_message)
        """
        command = command.strip().lower()

        # Handle conversation answers
        if self.active_conversation and command in ["1", "2", "3", "4"]:
            answer_idx = int(command) - 1
            correct, response = self.answer_question(answer_idx)
            return correct, response

        # Handle movement
        if command in ["up", "w"]:
            success = self.move_player(0, -1)
            return success, "moved up" if self.message == "" else self.message
        elif command in ["down", "s"]:
            success = self.move_player(0, 1)
            return success, "moved down" if self.message == "" else self.message
        elif command in ["left", "a"]:
            success = self.move_player(-1, 0)
            return success, "moved left" if self.message == "" else self.message
        elif command in ["right", "d"]:
            success = self.move_player(1, 0)
            return success, "moved right" if self.message == "" else self.message

        # Handle interactions
        elif command in ["interact", "i"]:
            return self.interact(), self.message
        elif command in ["stairs", "use", ">", "<"]:
            return self.use_stairs(), self.message
        elif command in ["exit", "esc"]:
            return self.exit_conversation(), self.message

        return False, f"Unknown command: {command}"

    def get_state(self) -> Dict:
        """
        Get current game state for testing/debugging.

        Returns:
            Dictionary containing current game state
        """
        return {
            "player_pos": (self.player.x, self.player.y),
            "npcs": [(npc.x, npc.y, npc.name) for npc in self.npcs],
            "message": self.message,
            "coherence": self.coherence,
            "knowledge_modules": list(self.knowledge_modules),
            "in_conversation": self.active_conversation is not None,
            "conversation_npc": (
                self.active_conversation.npc_name
                if self.active_conversation
                else None
            ),
            "current_floor": self.current_floor,
            "quest_active": self.quest_active,
            "quest_completed_npcs": list(self.quest_completed_npcs),
        }
