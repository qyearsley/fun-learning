% ============================================================================
% COMMANDS
% ============================================================================
% One predicate per thing the player can do. parser.pl turns a typed line into
% a call to one of these; mansion_escape.pl runs it. Nothing here reads input
% or does any parsing.
%
% Two of them are worth reading even if you skip the rest:
%
%   deduce/0 solves the lever puzzle by generate and test, reasoning only from
%   the notes the player has actually read.
%   goto/1, whose planner route/4 searches connected/3 and inherits the key
%   puzzle for free, because connected/3 has a rule in it.
% ============================================================================

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
