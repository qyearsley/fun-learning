% ============================================================================
% MANSION ESCAPE - A Text Adventure Game in Prolog
% ============================================================================
% This is a literate program demonstrating Prolog game development.
%
% HOW TO PLAY:
%   1. Install SWI-Prolog: brew install swi-prolog
%   2. Run: swipl mansion_escape.pl
%   3. The game starts automatically
%   4. Type commands followed by a period, e.g.: go(north).
%
% PROLOG BASICS:
% - Prolog is a logic programming language based on facts and rules
% - Programs consist of clauses (facts and rules) that define relationships
% - The Prolog engine tries to prove queries by matching against facts/rules
% - Variables start with uppercase (X, Location), atoms are lowercase (foyer)
% ============================================================================

% ----------------------------------------------------------------------------
% DYNAMIC PREDICATES
% ----------------------------------------------------------------------------
% In Prolog, predicates are normally static (defined at compile-time).
% The :- dynamic declaration allows us to add/remove facts at runtime.
% This is essential for tracking game state that changes as you play.

:- dynamic current_location/1.  % Tracks where the player currently is
:- dynamic inventory/1.          % Tracks items the player is carrying
:- dynamic game_state/1.         % Tracks overall game state (playing/won)

% ----------------------------------------------------------------------------
% GAME INITIALIZATION
% ----------------------------------------------------------------------------
% This rule sets up the initial game state. When called, it:
% 1. Removes any existing game state (retractall)
% 2. Sets the starting location to 'foyer'
% 3. Sets the game state to 'playing'

init_game :-
    % retractall removes ALL facts matching the pattern from the database
    retractall(current_location(_)),
    retractall(inventory(_)),
    retractall(game_state(_)),

    % assertz adds a new fact to the END of the database
    assertz(current_location(foyer)),
    assertz(game_state(playing)).

% ----------------------------------------------------------------------------
% ROOM DEFINITIONS (Facts)
% ----------------------------------------------------------------------------
% Each room is defined as a fact: room(ID, Name, Description)
% These are static facts - they don't change during gameplay.
% Think of these as a database of room information.

room(foyer, 'Grand Foyer',
     'You stand in a dusty foyer. A grand staircase leads up. Doors lead north and east.').

room(library, 'Library',
     'Shelves of ancient books surround you. A particular book catches your eye.').

room(kitchen, 'Kitchen',
     'A grim kitchen with old appliances. You see a rusty key on the counter.').

room(upstairs_hall, 'Upstairs Hallway',
     'A dark hallway. The master bedroom door is locked. Stairs lead down.').

room(master_bedroom, 'Master Bedroom',
     'The master bedroom. An open window offers escape!').

% ----------------------------------------------------------------------------
% ROOM CONNECTIONS (Facts and Rules)
% ----------------------------------------------------------------------------
% The connected/3 predicate defines how rooms are linked together.
% Format: connected(FromRoom, Direction, ToRoom)
%
% Most connections are simple facts, but note the last one is a RULE:
% It only succeeds if the player has the key in their inventory.
% This demonstrates Prolog's power: logic is built into the world structure!

connected(foyer, north, library).
connected(foyer, east, kitchen).
connected(foyer, up, upstairs_hall).
connected(library, south, foyer).
connected(kitchen, west, foyer).
connected(upstairs_hall, down, foyer).

% This is a RULE, not just a fact. The :- means "if"
% Read as: "foyer is connected north to master_bedroom IF inventory(key) is true"
connected(upstairs_hall, north, master_bedroom) :-
    inventory(key).  % This condition must be satisfied

% ----------------------------------------------------------------------------
% ITEM LOCATIONS (Facts)
% ----------------------------------------------------------------------------
% Defines where items start in the game world.
% Format: item_in_room(ItemID, RoomID)

item_in_room(book, library).
item_in_room(key, kitchen).

% ----------------------------------------------------------------------------
% START COMMAND (Entry Point)
% ----------------------------------------------------------------------------
% This is the main entry point of the game. When the player types 'start.',
% this rule executes, initializing the game and showing the welcome message.

start :-
    init_game,  % Reset game state

    % Write output to the console
    write('========================================'), nl,  % nl = newline
    write('     MANSION ESCAPE'), nl,
    write('========================================'), nl,
    nl,
    write('You wake up in a mysterious mansion.'), nl,
    write('Find a way to escape!'), nl,
    nl,
    write('Commands: look, go(Direction), take(Item), inventory, help, quit'), nl,
    nl,

    % Show the starting room description
    look.

% ----------------------------------------------------------------------------
% HELP COMMAND
% ----------------------------------------------------------------------------
% Displays available commands. Simple output rule.

help :-
    nl,
    write('Available commands:'), nl,
    write('  look          - Look around the current room'), nl,
    write('  go(Direction) - Move in a direction (north, south, east, west, up, down)'), nl,
    write('  take(Item)    - Pick up an item'), nl,
    write('  inventory     - Check your inventory'), nl,
    write('  help          - Show this help'), nl,
    write('  quit          - Exit the game'), nl,
    nl.

% ----------------------------------------------------------------------------
% LOOK COMMAND
% ----------------------------------------------------------------------------
% Displays the current room's description, items, and exits.
% This demonstrates Prolog's pattern matching and query system.

look :-
    % First, check that the game is still being played
    game_state(playing),

    % Get the current location (pattern matching against the database)
    current_location(Location),

    % Query the room database for this location's info
    room(Location, Name, Description),

    % Display the information
    nl,
    write('*** '), write(Name), write(' ***'), nl,
    write(Description), nl,

    % Call helper predicates to show items and exits
    list_items_here,
    list_exits,
    nl.

% ----------------------------------------------------------------------------
% LIST ITEMS (Helper Predicate)
% ----------------------------------------------------------------------------
% Uses findall/3, one of Prolog's most powerful built-in predicates.
% findall(Template, Goal, ResultList) finds ALL solutions to Goal.
%
% Here we find all items that are:
%   1. In the current room (item_in_room(Item, Location))
%   2. NOT in the player's inventory (\+ inventory(Item))

list_items_here :-
    current_location(Location),

    % findall collects all matching Items into a list
    findall(Item,
            (item_in_room(Item, Location), \+ inventory(Item)),  % \+ means "not"
            Items),

    % Conditional logic: -> is "then", ; is "else"
    (   Items = []              % If the list is empty
    ->  true                    % Do nothing
    ;   write('You see: '),     % Otherwise
        write_list(Items),       % Display the items
        nl
    ).

% ----------------------------------------------------------------------------
% LIST EXITS (Helper Predicate)
% ----------------------------------------------------------------------------
% Similar to list_items_here, uses findall to collect all valid exits.

list_exits :-
    current_location(Location),

    % Find all directions you can go from here
    % The _ (underscore) is an anonymous variable - we don't care about the destination
    findall(Direction, connected(Location, Direction, _), Exits),

    (   Exits = []
    ->  write('There are no obvious exits.')
    ;   write('Exits: '),
        write_list(Exits)
    ),
    nl.

% ----------------------------------------------------------------------------
% WRITE LIST (Utility Predicate)
% ----------------------------------------------------------------------------
% Recursive predicate to display a list with comma separation.
% This demonstrates Prolog's recursive pattern matching style.

write_list([]) :- !.  % Base case: empty list. The ! is a "cut" - stops backtracking

write_list([X]) :-     % Single item: just write it
    write(X), !.

write_list([X|Rest]) :- % Multiple items: write first, then rest
    write(X),
    write(', '),
    write_list(Rest).   % Recursive call with the tail of the list

% ----------------------------------------------------------------------------
% GO COMMAND (Movement)
% ----------------------------------------------------------------------------
% Handles player movement. This is the most complex rule in the game.
% It demonstrates multiple Prolog concepts:
%   - Pattern matching
%   - Conditional logic with guards
%   - Database modification (retract/assert)
%   - Backtracking and the cut operator

go(Direction) :-
    game_state(playing),
    current_location(CurrentLocation),

    % Try to find a connection in the given direction
    % The -> ; construct is if-then-else
    (   connected(CurrentLocation, Direction, NewLocation)
    ->  % SUCCESS: Valid connection found
        retract(current_location(CurrentLocation)),  % Remove old location
        assertz(current_location(NewLocation)),      % Add new location
        look,                                        % Show new room
        check_win_condition                          % Check if player won

    ;   % ELSE: Check if it's a locked door (player tried north without key)
        Direction = north, \+ connected(CurrentLocation, Direction, _)
    ->  nl,
        write('The door is locked. You need to find a key.'),
        nl, nl

    ;   % ELSE: Invalid direction
        nl,
        write('You cannot go that way.'),
        nl, nl
    ).

% ----------------------------------------------------------------------------
% TAKE COMMAND (Pick Up Items)
% ----------------------------------------------------------------------------
% Allows the player to pick up items from the current room.
% Demonstrates conditional logic and providing context-specific feedback.

take(Item) :-
    game_state(playing),
    current_location(Location),

    % Check if the item is here and not already taken
    (   item_in_room(Item, Location), \+ inventory(Item)
    ->  % Add item to inventory
        assertz(inventory(Item)),
        nl,
        write('You take the '), write(Item), write('.'), nl,

        % Provide item-specific hints (nested conditionals)
        (   Item = book
        ->  write('The book reveals a clue: "The key to freedom lies in the kitchen."'), nl
        ;   Item = key
        ->  write('This key might unlock something...'), nl
        ;   true  % No special message for other items
        ),
        nl

    ;   % Already have it?
        inventory(Item)
    ->  nl,
        write('You already have the '), write(Item), write('.'),
        nl, nl

    ;   % Not here
        nl,
        write('There is no '), write(Item), write(' here.'),
        nl, nl
    ).

% ----------------------------------------------------------------------------
% INVENTORY COMMAND
% ----------------------------------------------------------------------------
% Shows what the player is carrying.

inventory :-
    nl,
    write('You are carrying: '),

    % Collect all items in the player's inventory
    findall(Item, inventory(Item), Items),

    (   Items = []
    ->  write('nothing')
    ;   write_list(Items)
    ),
    nl, nl.

% ----------------------------------------------------------------------------
% WIN CONDITION CHECK
% ----------------------------------------------------------------------------
% Called after each movement. If the player reaches the master bedroom,
% they've won! Changes game_state from 'playing' to 'won'.

check_win_condition :-
    current_location(master_bedroom),
    nl,
    write('========================================'), nl,
    write('You climb through the window and escape!'), nl,
    write('*** YOU WIN! ***'), nl,
    write('========================================'), nl,
    nl,

    % Update game state (replace 'playing' with 'won')
    retract(game_state(playing)),
    assertz(game_state(won)).

% ----------------------------------------------------------------------------
% QUIT COMMAND
% ----------------------------------------------------------------------------
% Exits the game gracefully.

quit :-
    nl,
    write('Thanks for playing!'), nl,
    halt.  % Built-in predicate to exit SWI-Prolog

% ----------------------------------------------------------------------------
% AUTO-START
% ----------------------------------------------------------------------------
% The initialization directive runs automatically when the file is loaded.
% This makes the game start immediately when you run: swipl mansion_escape.pl

:- initialization(start).

% ============================================================================
% END OF PROGRAM
%
% EXTENDING THIS GAME:
% - Add more rooms to the room/3 facts
% - Add more items to item_in_room/2
% - Create more complex puzzles with additional game_state facts
% - Add NPCs with their own facts and interaction rules
% - Add a combat system with dynamic health tracking
% - Save/load game state to files
%
% PROLOG CONCEPTS DEMONSTRATED:
% - Facts and rules
% - Pattern matching and unification
% - Recursive predicates
% - Dynamic database (assert/retract)
% - Backtracking and the cut operator (!)
% - List processing with findall
% - Conditional logic (-> and ;)
% - Logic as structure (the locked door rule)
% ============================================================================
