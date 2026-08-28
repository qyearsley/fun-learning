#!/usr/bin/env swipl
% ============================================================================
% MANSION ESCAPE - A Text Adventure Game in Prolog
% ============================================================================
% This is a literate program demonstrating Prolog game development.
%
% HOW TO PLAY:
%   1. Install SWI-Prolog: brew install swi-prolog
%   2. Run: swipl mansion_escape.pl
%   3. The game starts automatically
%   4. Type commands in plain English, e.g.: go north
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
% ITEM LOCATIONS AND ADJECTIVES (Facts)
% ----------------------------------------------------------------------------
% Defines where items start in the game world, and what the player is allowed
% to call them.
% Format: item_in_room(ItemID, RoomID)

item_in_room(book, library).
item_in_room(key, kitchen).

% Adjectives the player is allowed to use for each item, so that
% "take the rusty key" works as well as "take key". The parser at the bottom
% of this file checks typed adjectives against these facts.
% Format: adjective(ItemID, Word)

adjective(book, ancient).
adjective(book, old).
adjective(key, rusty).
adjective(key, old).

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
    write('Commands: look, go <direction>, take <item>, inventory, help, quit'), nl,
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
    write('  look             - Look around the current room'), nl,
    write('  go <direction>   - Move (north, south, east, west, up, down)'), nl,
    write('  take <item>      - Pick up an item'), nl,
    write('  inventory        - Check your inventory'), nl,
    write('  help             - Show this help'), nl,
    write('  restart          - Start over'), nl,
    write('  quit             - Exit the game'), nl,
    nl,
    write('Articles and adjectives are optional, directions can be'), nl,
    write('abbreviated, and most verbs have synonyms. All of these work:'), nl,
    write('  go north  /  walk n  /  north'), nl,
    write('  take the rusty key  /  pick up key  /  get key'), nl,
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
%
% Note the if-then-else: the "else" branch is just true. Without it this
% predicate would FAIL on every ordinary move, and because go/1 calls it last,
% go/1 would fail too — after having already moved the player and printed the
% room. A predicate that means "check whether X happened" has to succeed when
% X did not happen.

check_win_condition :-
    (   current_location(master_bedroom)
    ->  nl,
        write('========================================'), nl,
        write('You climb through the window and escape!'), nl,
        write('*** YOU WIN! ***'), nl,
        write('========================================'), nl,
        nl,

        % Update game state (replace 'playing' with 'won')
        retract(game_state(playing)),
        assertz(game_state(won))

    ;   true  % Not in the bedroom yet: nothing to do, but still succeed
    ).

% ----------------------------------------------------------------------------
% QUIT COMMAND
% ----------------------------------------------------------------------------
% Exits the game gracefully.

quit :-
    nl,
    write('Thanks for playing!'), nl,
    halt.  % Built-in predicate to exit SWI-Prolog

% ----------------------------------------------------------------------------
% PARSING PLAYER INPUT (Definite Clause Grammars)
% ----------------------------------------------------------------------------
% Everything above is the game. Everything below turns a typed line of English
% into one of the goals above, so the player types "go north" rather than
% "go(north).".
%
% A DCG rule uses --> instead of :- and describes a sequence of tokens.
% Terminals go in a list; nonterminals are bare; {...} holds ordinary Prolog
% that must also hold. So this rule:
%
%     command(go(Dir)) --> go_verb, opt_article, direction(Dir).
%
% is compiled by Prolog into an ordinary predicate with two extra arguments:
%
%     command(go(Dir), S0, S) :-
%         go_verb(S0, S1), opt_article(S1, S2), direction(Dir, S2, S).
%
% S0 is the list of words coming in, S is whatever is left over. Each
% nonterminal consumes a prefix and hands the rest along. That pairing of
% "list in, remainder out" is a DIFFERENCE LIST, and it is the whole trick:
% --> is not a parser generator, it is syntax for threading a list through a
% chain of predicates. phrase(command(C), Words) calls command(C, Words, []),
% i.e. "parse Words and leave nothing over".
%
% Because these are just predicates, parsing backtracks like anything else. If
% a sentence has two readings, findall/3 below collects both.

% Top-level command forms. Each produces a goal that already exists above.
command(look)       --> look_verb.
command(inventory)  --> inv_verb.
command(help)       --> help_verb.
command(quit)       --> quit_verb.
command(start)      --> [restart].
command(go(Dir))    --> go_verb, opt_article, direction(Dir).
command(take(Item)) --> take_verb, noun_phrase(Item).

% Verb vocabulary. Adding a synonym is one line, not a parser change.
look_verb --> [look].
look_verb --> [look, around].
look_verb --> [l].

inv_verb --> [inventory].
inv_verb --> [inv].
inv_verb --> [i].

help_verb --> [help].
help_verb --> [h].
help_verb --> [commands].

quit_verb --> [quit].
quit_verb --> [exit].
quit_verb --> [q].

go_verb --> [go].
go_verb --> [walk].
go_verb --> [move].
go_verb --> [head].
go_verb --> [].  % Empty: lets a bare "north" mean "go north"

take_verb --> [take].
take_verb --> [get].
take_verb --> [grab].
take_verb --> [pick, up].

% Directions, with abbreviations. The head argument is the atom the game uses,
% so several spellings can map to one direction.
direction(north) --> [north].
direction(north) --> [n].
direction(south) --> [south].
direction(south) --> [s].
direction(east)  --> [east].
direction(east)  --> [e].
direction(west)  --> [west].
direction(west)  --> [w].
direction(up)    --> [up].
direction(up)    --> [u].
direction(up)    --> [upstairs].
direction(down)  --> [down].
direction(down)  --> [d].
direction(down)  --> [downstairs].

% An article is optional, which is expressed as a rule that matches nothing.
opt_article --> [the].
opt_article --> [a].
opt_article --> [an].
opt_article --> [].

% "the rusty key" -> key. Any words between the article and the final noun are
% treated as adjectives, and the {...} guard demands that they actually apply
% to that item, so "take the rusty key" is accepted and "take the brass key"
% is not.
noun_phrase(Item) -->
    opt_article,
    adjectives(Adjectives),
    [Item],
    { adjectives_match(Item, Adjectives) }.

adjectives([Word|Rest]) --> [Word], adjectives(Rest).
adjectives([])          --> [].

adjectives_match(Item, Adjectives) :-
    forall(member(Adjective, Adjectives), adjective(Item, Adjective)).

% ----------------------------------------------------------------------------
% READING A LINE OF INPUT
% ----------------------------------------------------------------------------
% Lowercase the line, split it on spaces while discarding trailing punctuation,
% and convert the pieces to atoms so the grammar's terminals can match them.
% Fails at end of input (Ctrl-D), which the game loop treats as quitting.

read_words(Words) :-
    read_line_to_string(user_input, Line),
    Line \== end_of_file,
    string_lower(Line, Lowered),

    % split_string(String, Separators, Padding, Pieces) - padding characters
    % are trimmed from each piece, which is how the trailing period goes away
    split_string(Lowered, " \t", " \t.,!?", Pieces),
    strings_to_words(Pieces, Words).

% Consecutive separators leave empty strings behind, so skip those.
strings_to_words([], []).

strings_to_words([""|Rest], Words) :- !,
    strings_to_words(Rest, Words).

strings_to_words([Piece|Rest], [Word|Words]) :-
    atom_string(Word, Piece),
    strings_to_words(Rest, Words).

% ----------------------------------------------------------------------------
% THE GAME LOOP
% ----------------------------------------------------------------------------
% Prompt, read, parse, run, repeat. This replaces the SWI-Prolog top level,
% which used to serve as the game's prompt.

play :-
    start,
    game_loop.

game_loop :-
    write('> '),
    flush_output,  % Prompts are buffered otherwise, so force it out

    (   read_words(Words)
    ->  handle(Words)
    ;   nl, quit  % End of input
    ),
    game_loop.

% Blank line: just prompt again.
handle([]) :- !.

handle(Words) :-
    % findall collects every parse of the line. sort/2 removes duplicates, so
    % what is left is the set of distinct readings.
    findall(Command, phrase(command(Command), Words), Parses),
    sort(Parses, Commands),

    (   Commands = [Command]
    ->  run(Command)

    ;   Commands = []
    ->  nl,
        write('I do not understand that. Type help for a list of commands.'),
        nl, nl

    ;   % More than one reading. Unreachable with the current two items, but
        % this is what makes adding a second key cheap: the grammar reports
        % the ambiguity instead of silently guessing.
        nl,
        write('That could mean several things. Try being more specific.'),
        nl, nl
    ).

% Commands guard themselves with game_state(playing), so they fail once the
% game is won rather than doing something inappropriate.
run(Command) :-
    (   call(Command)
    ->  true

    ;   game_state(won)
    ->  nl,
        write('You have already escaped. Type restart or quit.'),
        nl, nl

    ;   nl,
        write('Nothing happens.'),
        nl, nl
    ).

% ----------------------------------------------------------------------------
% AUTO-START
% ----------------------------------------------------------------------------
% The initialization directive runs automatically when the file is loaded.
% This makes the game start immediately when you run: swipl mansion_escape.pl
%
% The second argument, main, declares play/0 to be the program's entry point
% rather than a goal run alongside the interactive top level. That is what
% makes it legal for quit/0 to call halt/0 without SWI-Prolog complaining.

:- initialization(play, main).

% ============================================================================
% END OF PROGRAM
%
% EXTENDING THIS GAME:
% - Add more rooms to the room/3 facts
% - Add more items to item_in_room/2 and adjective/2
% - Add verbs, synonyms, or whole command forms to the DCG rules
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
% - Definite clause grammars and difference lists (the parser)
% ============================================================================
