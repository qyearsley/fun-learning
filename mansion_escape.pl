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
%   5. Type help for the full command list
%
% THE PUZZLE:
% The way out is a cellar door held by three levers. Notes hidden around the
% mansion each state one constraint on how the levers must sit. Work it out
% yourself, or type deduce and watch the program solve its own puzzle - using
% only the notes you have actually read.
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
:- dynamic known_constraint/1.   % Which notes the player has read
:- dynamic lever_position/2.     % lever_position(Lever, up) or (Lever, down)

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
    retractall(known_constraint(_)),
    retractall(lever_position(_, _)),

    % assertz adds a new fact to the END of the database
    assertz(current_location(foyer)),
    assertz(game_state(playing)),

    % Every lever starts down. forall/2 is "for each solution of the first
    % goal, the second must succeed" - a loop written as a logical claim.
    forall(lever(Lever), assertz(lever_position(Lever, down))).

% ----------------------------------------------------------------------------
% ROOM DEFINITIONS (Facts)
% ----------------------------------------------------------------------------
% Each room is defined as a fact: room(ID, Name, Description)
% These are static facts - they don't change during gameplay.
% Think of these as a database of room information.

room(foyer, 'Grand Foyer',
     'You stand in a dusty foyer. A grand staircase leads up, and a narrow stair descends into darkness. Doors lead north and east.').

room(library, 'Library',
     'Shelves of ancient books surround you. A particular book catches your eye. A note is pinned to the shelf.').

room(kitchen, 'Kitchen',
     'A grim kitchen with old appliances. You see a rusty key on the counter, and a note stuck to the icebox.').

room(upstairs_hall, 'Upstairs Hallway',
     'A dark hallway. The master bedroom door is locked. An oil lamp sits on a side table. Stairs lead down.').

room(master_bedroom, 'Master Bedroom',
     'The master bedroom. The window is barred. A note is nailed to the frame.').

room(cellar, 'Cellar',
     'A damp cellar. A heavy door leads out to the grounds, held shut by three levers set into the wall: brass, iron and copper.').

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
connected(foyer, down, cellar).
connected(library, south, foyer).
connected(kitchen, west, foyer).
connected(upstairs_hall, down, foyer).
connected(cellar, up, foyer).

% This is a RULE, not just a fact. The :- means "if"
% Read as: "foyer is connected north to master_bedroom IF inventory(key) is true"
connected(upstairs_hall, north, master_bedroom) :-
    inventory(key).  % This condition must be satisfied

connected(master_bedroom, south, upstairs_hall).

% ----------------------------------------------------------------------------
% DARKNESS (Two Clauses Meaning "Or")
% ----------------------------------------------------------------------------
% The locked door above is an AND: you may pass IF you hold the key. This is
% the other half of the idea. can_see/0 has two clauses, and Prolog tries them
% in turn, so the predicate succeeds if EITHER holds: the room is lit, or you
% are carrying the lamp. Multiple clauses are Prolog's "or".

dark(cellar).

can_see :-
    current_location(Room),
    \+ dark(Room).

can_see :-
    inventory(lamp).

% ----------------------------------------------------------------------------
% ITEM LOCATIONS AND ADJECTIVES (Facts)
% ----------------------------------------------------------------------------
% Defines where items start in the game world, and what the player is allowed
% to call them.
% Format: item_in_room(ItemID, RoomID)

item_in_room(book, library).
item_in_room(key, kitchen).
item_in_room(lamp, upstairs_hall).

% Adjectives the player is allowed to use for each item, so that
% "take the rusty key" works as well as "take key". The parser at the bottom
% of this file checks typed adjectives against these facts.
% Format: adjective(ItemID, Word)

adjective(book, ancient).
adjective(book, old).
adjective(key, rusty).
adjective(key, old).
adjective(lamp, oil).
adjective(lamp, old).

% What you get for examining a thing. Scenery is allowed here too, which is why
% these are separate from item_in_room/2.
% Format: description(Thing, Text)

description(book, 'A leather tome. A margin note reads: "The key to freedom lies in the kitchen."').
description(key, 'A small rusty key. It looks like it fits an interior door.').
description(lamp, 'An oil lamp, still half full. It would light a dark room.').
description(window, 'Iron bars, set deep into the stone. Not that way.').

% ----------------------------------------------------------------------------
% THE NOTES AND WHAT THEY SAY (Facts)
% ----------------------------------------------------------------------------
% Each note carries one constraint on the lever mechanism in the cellar.
% Reading a note asserts known_constraint/1, and deduce/0 reasons only from the
% constraints you have actually found - so the solver knows exactly what you
% know, no more.
% Format: note(RoomID, ConstraintID) and constraint_text(ConstraintID, Text)

note(library, 1).
note(kitchen, 2).
note(master_bedroom, 3).

constraint_text(1, 'The brass and iron levers never sit the same way.').
constraint_text(2, 'If the brass lever is up, the copper lever is down.').
constraint_text(3, 'At least two levers are up.').

% ----------------------------------------------------------------------------
% THE LEVER MECHANISM (Constraints as Rules)
% ----------------------------------------------------------------------------
% Three levers, each up or down, so eight possible settings. A setting is
% written as a list of Lever-Position pairs, e.g. [brass-down, iron-up,
% copper-up]. The - is just a term, not subtraction; Prolog uses it as a
% general-purpose pairing operator.
%
% holds(Id, Setting) says whether the constraint from note Id is satisfied by a
% setting. Each is a plain rule, which is why adding a fourth note means adding
% one clause here and one constraint_text/2 fact - deduce/0 keeps working.

lever(brass).
lever(iron).
lever(copper).

position(up).
position(down).

holds(1, Setting) :-
    setting_of(brass, Setting, Brass),
    setting_of(iron, Setting, Iron),
    Brass \== Iron.

holds(2, Setting) :-
    (   setting_of(brass, Setting, up)
    ->  setting_of(copper, Setting, down)
    ;   true  % Brass is down, so the note says nothing
    ).

holds(3, Setting) :-
    findall(Lever, member(Lever-up, Setting), Up),
    length(Up, Count),
    Count >= 2.

setting_of(Lever, Setting, Position) :-
    memberchk(Lever-Position, Setting).

% Every possible setting. Backtracking over position/1 generates all eight.
candidate([brass-Brass, iron-Iron, copper-Copper]) :-
    position(Brass),
    position(Iron),
    position(Copper).

% The setting the levers are actually in right now.
current_setting([brass-Brass, iron-Iron, copper-Copper]) :-
    lever_position(brass, Brass),
    lever_position(iron, Iron),
    lever_position(copper, Copper).

satisfies(Ids, Setting) :-
    forall(member(Id, Ids), holds(Id, Setting)).

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
    write('Commands: look, examine, go <direction>, take <item>, deduce, help, quit'), nl,
    nl,

    % Show the starting room description
    look.

% ----------------------------------------------------------------------------
% HELP COMMAND
% ----------------------------------------------------------------------------
% The help text is facts rather than a run of write/1 calls. Data beats code:
% adding a command means adding a fact, and nothing about help/0 changes.

help_line('Available commands:').
help_line('  look             - Look around the current room').
help_line('  examine <thing>  - Look closely at something (also: read <thing>)').
help_line('  go <direction>   - Move (north, south, east, west, up, down)').
help_line('  go to <room>     - Walk there, if a route exists').
help_line('  take <item>      - Pick up an item').
help_line('  pull <lever>     - Flip a lever in the cellar').
help_line('  deduce           - Reason about the levers from what you have read').
help_line('  inventory        - Check your inventory').
help_line('  restart          - Start over').
help_line('  quit             - Exit the game').
help_line('').
help_line('Articles and adjectives are optional, directions can be').
help_line('abbreviated, and most verbs have synonyms. All of these work:').
help_line('  go north  /  walk n  /  north  /  go to the cellar').
help_line('  take the rusty key  /  pick up key  /  get key').
help_line('  read the note  /  look at book  /  examine levers').

help :-
    nl,
    forall(help_line(Line), (write(Line), nl)),
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

    nl,
    (   can_see
    ->  % Query the room database for this location's info
        room(Location, Name, Description),

        % Display the information
        write('*** '), write(Name), write(' ***'), nl,
        write(Description), nl,

        % Call helper predicates to show items and exits
        list_items_here,
        list_exits

    ;   write('Pitch dark. You can feel a stair behind you, going up.'), nl
    ),
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
        look                                         % Show new room

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
        ;   Item = lamp
        ->  write('It is lit. Somewhere in this house is a room that needs it.'), nl
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
% Called after each lever is pulled. The door opens when the levers satisfy all
% three constraints - whether or not the player has read the notes that state
% them. The mechanism does not care what you know; only deduce/0 does.
%
% Note the if-then-else: the "else" branch is just true. Without it this
% predicate would FAIL whenever the player has not won, and any caller that
% runs it last would fail too, after having already done its work. A predicate
% that means "check whether X happened" has to succeed when X did not happen.

check_win_condition :-
    (   current_location(cellar),
        current_setting(Setting),
        satisfies([1, 2, 3], Setting)

    ->  nl,
        write('========================================'), nl,
        write('The levers seat with a heavy clunk and the'), nl,
        write('cellar door swings open onto wet grass.'), nl,
        write('*** YOU ESCAPE! ***'), nl,
        write('========================================'), nl,
        nl,

        % Update game state (replace 'playing' with 'won')
        retract(game_state(playing)),
        assertz(game_state(won))

    ;   true  % Not out yet: nothing to do, but still succeed
    ).

% ----------------------------------------------------------------------------
% EXAMINE COMMAND
% ----------------------------------------------------------------------------
% Looking closely at one thing, rather than at the room. Notes are the reason
% this exists: reading one is how a constraint enters the knowledge base.

examine(note) :-
    game_state(playing), !,
    current_location(Location),
    nl,
    (   \+ can_see
    ->  write('Too dark to read anything.')

    ;   note(Location, Id)
    ->  constraint_text(Id, Text),
        write('The note reads: "'), write(Text), write('"'), nl,
        (   known_constraint(Id)
        ->  write('You had already read this one.')
        ;   assertz(known_constraint(Id)),
            write('You commit it to memory.')
        )

    ;   write('There is no note here.')
    ),
    nl, nl.

examine(levers) :-
    game_state(playing), !,
    show_levers.

% A lever by name shows the whole panel; asking about one is asking about all.
examine(Thing) :-
    game_state(playing),
    lever(Thing), !,
    show_levers.

examine(Thing) :-
    game_state(playing),
    nl,
    (   \+ can_see
    ->  write('Too dark to see anything.')

    ;   description(Thing, Text),
        thing_at_hand(Thing)
    ->  write(Text)

    ;   write('You see nothing special about the '), write(Thing), write('.')
    ),
    nl, nl.

% A thing is at hand if you are carrying it or it is in this room.
thing_at_hand(Thing) :-
    inventory(Thing).

thing_at_hand(Thing) :-
    current_location(Location),
    item_in_room(Thing, Location).

thing_at_hand(window) :-
    current_location(master_bedroom).

show_levers :-
    nl,
    (   \+ current_location(cellar)
    ->  write('There are no levers here.'), nl

    ;   \+ can_see
    ->  write('Too dark to find them.'), nl

    ;   forall(lever_position(Lever, Position),
               (   write('  '), write(Lever), write(' is '), write(Position), nl ))
    ),
    nl.

% ----------------------------------------------------------------------------
% PULL COMMAND (Flipping a Lever)
% ----------------------------------------------------------------------------

pull(Lever) :-
    game_state(playing),
    nl,
    (   \+ current_location(cellar)
    ->  write('The levers are down in the cellar.'), nl, nl

    ;   \+ can_see
    ->  write('You grope at the wall but cannot find the levers in the dark.'), nl, nl

    ;   retract(lever_position(Lever, Old)),
        opposite(Old, New),
        assertz(lever_position(Lever, New)),
        write('The '), write(Lever), write(' lever is now '), write(New), write('.'),
        nl, nl,
        check_win_condition
    ).

% "pull the lever" is ambiguous in English, so say so rather than guessing.
pull_which :-
    game_state(playing),
    nl,
    write('Which lever? There are three: brass, iron and copper.'),
    nl, nl.

opposite(up, down).
opposite(down, up).

% ----------------------------------------------------------------------------
% DEDUCE COMMAND (The Game Solves Its Own Puzzle)
% ----------------------------------------------------------------------------
% Generate and test: produce all eight settings, keep the ones consistent with
% every constraint the player has read, and narrate the eliminations.
%
% The interesting part is that this reasons from known_constraint/1, not from
% the full set. Read one note and most settings survive; read all three and one
% does. The player's knowledge IS the program's premises.

deduce :-
    game_state(playing),
    findall(Id, known_constraint(Id), Known0),
    msort(Known0, Known),
    nl,
    (   Known == []
    ->  write('You know nothing about the levers yet. Find the notes.'), nl, nl

    ;   write('What you know:'), nl,
        forall(member(Id, Known),
               (   constraint_text(Id, Text),
                   write('  - '), write(Text), nl )),
        nl,
        forall(candidate(Setting), report_candidate(Known, Setting)),
        nl,
        findall(S, (candidate(S), satisfies(Known, S)), Survivors),
        report_survivors(Survivors)
    ).

% Print one candidate setting and the first constraint it violates, if any.
report_candidate(Known, Setting) :-
    forall(member(Lever-Position, Setting),
           format("  ~w=~w", [Lever, Position])),
    (   first_failure(Known, Setting, Id)
    ->  constraint_text(Id, Text),
        format("   -- ruled out by: ~w~n", [Text])
    ;   format("   -- consistent~n")
    ).

first_failure(Known, Setting, Id) :-
    member(Id, Known),
    \+ holds(Id, Setting),
    !.  % Only report the first violation, not all of them

report_survivors([]) :-
    format("Nothing satisfies all of that. Something is wrong.~n~n").

report_survivors([Setting]) :-
    write('Only one setting survives: '),
    forall(member(Lever-Position, Setting), format("~w ~w   ", [Lever, Position])),
    nl, nl.

report_survivors([_, _|Rest]) :-
    length(Rest, N),
    Count is N + 2,
    format("~w settings still fit. Find another note.~n~n", [Count]).

% ----------------------------------------------------------------------------
% GO TO COMMAND (A Path Planner Over connected/3)
% ----------------------------------------------------------------------------
% Depth-first search for a route, then walk it. The visited list is what stops
% it looping back through rooms it has already tried.
%
% Note what is NOT here: any mention of the key. connected/3 has a rule in it,
% so a route through the bedroom simply does not exist until the key is in
% inventory, and the planner inherits the puzzle for free. The puzzle was never
% in the movement code - it is in the world.
%
% This takes the first route it finds, not the shortest. On this map they
% happen to be the same for every pair of rooms; add rooms and that may stop
% being true, at which point wrapping the call in length/2 to grow the path
% bound turns it into iterative deepening.

route(Room, Room, _, []).

route(From, To, Visited, [Direction|Rest]) :-
    connected(From, Direction, Next),
    \+ memberchk(Next, Visited),
    route(Next, To, [Next|Visited], Rest).

% The grammar only ever produces real room atoms, so there is no "no such
% place" case to handle here - an unknown name fails to parse instead.
goto(Room) :-
    game_state(playing),
    current_location(Here),
    (   Room == Here
    ->  nl, write('You are already here.'), nl, nl

    ;   route(Here, Room, [Here], Path)
    ->  walk(Path)

    ;   nl, write('You cannot see a way there from here.'), nl, nl
    ).

% Walk a route one step at a time, so each room is described on the way.
walk([]).

walk([Direction|Rest]) :-
    go(Direction),
    walk(Rest).

% ----------------------------------------------------------------------------
% USE COMMAND
% ----------------------------------------------------------------------------
% No mechanics behind this one. "use key" is a natural thing to type, and being
% told how the key works beats being told the sentence was not understood.

use_text(key,  'No keyhole to work at. Carrying the key is enough - the bedroom door gives way when you have it on you.').
use_text(lamp, 'It is already lit. Carry it somewhere dark.').
use_text(book, 'You read it again. The margin note has not changed.').

use(Thing) :-
    game_state(playing),
    nl,
    (   \+ thing_at_hand(Thing)
    ->  write('You do not have that.')
    ;   use_text(Thing, Text)
    ->  write(Text)
    ;   write('You turn it over in your hands to no particular effect.')
    ),
    nl, nl.

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
command(look)          --> look_verb.
command(inventory)     --> inv_verb.
command(help)          --> help_verb.
command(quit)          --> quit_verb.
command(deduce)        --> deduce_verb.
command(start)         --> [restart].
command(goto(Room))    --> go_verb, [to], opt_article, room_name(Room).
command(go(Dir))       --> go_verb, opt_article, direction(Dir).
command(take(Item))    --> take_verb, noun_phrase(Item).
command(examine(Item)) --> examine_verb, noun_phrase(Item).
command(use(Item))     --> use_verb, noun_phrase(Item).
command(pull(Lever))   --> pull_verb, opt_article, lever_name(Lever), opt_lever_word.
command(pull_which)    --> pull_verb, opt_article, [lever].

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

deduce_verb --> [deduce].
deduce_verb --> [think].
deduce_verb --> [reason].
deduce_verb --> [solve].

go_verb --> [go].
go_verb --> [walk].
go_verb --> [move].
go_verb --> [head].
go_verb --> [].  % Empty: lets a bare "north" mean "go north"

take_verb --> [take].
take_verb --> [get].
take_verb --> [grab].
take_verb --> [pick, up].

examine_verb --> [examine].
examine_verb --> [inspect].
examine_verb --> [read].
examine_verb --> [look, at].
examine_verb --> [x].

use_verb --> [use].
use_verb --> [unlock].

pull_verb --> [pull].
pull_verb --> [flip].
pull_verb --> [toggle].

% "pull the brass lever" and "pull brass" should both work. The {lever(Name)}
% guard is what keeps "pull the lever" from parsing two ways, with "the" and
% "lever" each able to fill a bare slot.
lever_name(Name) --> [Name], { lever(Name) }.

opt_lever_word --> [lever].
opt_lever_word --> [].

% Room names for the planner, so "go to the hall" maps to the room's atom.
room_name(foyer)          --> [foyer].
room_name(library)        --> [library].
room_name(kitchen)        --> [kitchen].
room_name(upstairs_hall)  --> [hall].
room_name(upstairs_hall)  --> [upstairs].
room_name(upstairs_hall)  --> [upstairs, hall].
room_name(master_bedroom) --> [bedroom].
room_name(master_bedroom) --> [master, bedroom].
room_name(cellar)         --> [cellar].

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
% - Add more items to item_in_room/2, adjective/2 and description/2
% - Add verbs, synonyms, or whole command forms to the DCG rules
% - Add a fourth note: one note/2 fact, one constraint_text/2 fact and one
%   holds/2 clause. deduce/0 needs no changes at all
% - Add NPCs with their own facts and interaction rules
% - Save/load game state to files
%
% PROLOG CONCEPTS DEMONSTRATED:
% - Facts and rules
% - Pattern matching and unification
% - Recursive predicates
% - Dynamic database (assert/retract)
% - Backtracking and the cut operator (!)
% - List processing with findall and forall
% - Conditional logic (-> and ;)
% - Logic as structure (the locked door rule: clause bodies as AND)
% - Multiple clauses as disjunction (can_see/0: clauses as OR)
% - Generate and test (candidate/1 with holds/2: the whole of deduce/0)
% - Search over a fact base (route/4 planning across connected/3)
% - Definite clause grammars and difference lists (the parser)
% ============================================================================
