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
%
% THE FILES, IN READING ORDER:
%   world.pl     The mansion itself: rooms, connections, items, the notes, and
%                the lever mechanism. Nearly all facts, and the place to start -
%                the puzzle is visible in the data.
%   commands.pl  What the player can do: look, go, take, examine, pull, deduce,
%                go to. The bulk of the code.
%   parser.pl    The definite clause grammar that turns "take the rusty key"
%                into take(key).
%   this file    Mutable state, initialization, and the read-parse-run loop.
%
% None of these declare a module, so every predicate lives in `user` and any
% file can call any other without an export list. That is deliberate: modules
% would be one more thing to explain, and the subject here is Prolog, not
% packaging.
% ============================================================================

% ----------------------------------------------------------------------------
% DYNAMIC PREDICATES
% ----------------------------------------------------------------------------
% In Prolog, predicates are normally static (defined at compile-time).
% The :- dynamic declaration allows us to add/remove facts at runtime.
% This is essential for tracking game state that changes as you play.
%
% Every predicate that changes during play is declared here, in one place, so
% there is a single list of what counts as mutable state. The clauses in the
% other three files are all static - commands.pl asserts and retracts against
% these five predicates, but declares none of its own.

:- dynamic current_location/1.  % Tracks where the player currently is
:- dynamic inventory/1.          % Tracks items the player is carrying
:- dynamic game_state/1.         % Tracks overall game state (playing/won)
:- dynamic known_constraint/1.   % Which notes the player has read
:- dynamic lever_position/2.     % lever_position(Lever, up) or (Lever, down)

% ----------------------------------------------------------------------------
% LOADING THE REST OF THE PROGRAM
% ----------------------------------------------------------------------------
% ensure_loaded/1 resolves a relative name against the directory of the file
% holding the directive, so these are found however the game is started.
%
% The order does not matter. Prolog reads every clause in all four files before
% any of it runs, so a predicate may be called from a file loaded before the
% one that defines it - which is why init_game/0 below can call lever/1 from
% world.pl.

:- ensure_loaded(world).
:- ensure_loaded(commands).
:- ensure_loaded(parser).

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
% - Add more rooms to the room/3 facts in world.pl
% - Add more items to item_in_room/2, adjective/2 and description/2, also in
%   world.pl
% - Add verbs, synonyms, or whole command forms to the DCG rules in parser.pl,
%   with the goal they produce defined in commands.pl
% - Add a fourth note: one note/2 fact, one constraint_text/2 fact and one
%   holds/2 clause, all in world.pl. deduce/0 needs no changes at all
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
