% Tests for the lever puzzle and the map.
%
%   swipl -g run_tests -t halt mansion_escape/tests.pl
%
% Everything here is a pure predicate: `holds/2`, `candidate/1`, `satisfies/2`
% and `route/4` take their inputs as arguments and touch no game state, so the
% tests need no player and no input. The mutable half of the game is
% deliberately not exercised; that is the interactive part, and it is checked by
% playing.
%
% The one test worth the whole file is `exactly_one_solution`. The game's
% premise is that reading all three notes pins the levers down to a single
% setting, and nothing in `world.pl` says so: it falls out of three separate
% constraint rules. Loosen any one of them and `deduce` starts offering the
% player two answers, with no error anywhere.
%
% `world.pl`, `commands.pl` and `parser.pl` are loaded directly rather than
% through `mansion_escape.pl`, because that file carries
% `:- initialization(play, main)`
% and loading it starts the game. What it also carries is the five `:- dynamic`
% declarations, and `route/4` reads one of them (`inventory/1`, for the locked
% bedroom door), so this file re-declares the ones it needs. That is the one
% place the game's "every mutable predicate is declared in mansion_escape.pl"
% rule is bent, and this comment is the price of bending it: if a sixth dynamic
% predicate appears there and a test needs it, it has to be added here too.

:- dynamic inventory/1.
:- dynamic lever_position/2.

:- ensure_loaded('world.pl').
:- ensure_loaded('commands.pl').
:- ensure_loaded('parser.pl').

:- begin_tests(levers).

% ---------------------------------------------------------------------------
% The setting space
% ---------------------------------------------------------------------------

test(three_levers_give_eight_settings) :-
    findall(S, candidate(S), Settings),
    length(Settings, 8).

test(every_setting_is_distinct) :-
    findall(S, candidate(S), Settings),
    sort(Settings, Sorted),
    length(Sorted, 8).

test(every_setting_names_every_lever) :-
    forall(candidate(Setting),
           forall(lever(Lever), memberchk(Lever-_, Setting))).

test(every_lever_holds_a_real_position) :-
    forall(( candidate(Setting), member(_-Position, Setting) ),
           position(Position)).

% ---------------------------------------------------------------------------
% The three notes, one at a time
% ---------------------------------------------------------------------------

% Note 1: the brass and iron levers never sit the same way.
test(note_one_rejects_matching_brass_and_iron) :-
    \+ holds(1, [brass-up, iron-up, copper-down]),
    \+ holds(1, [brass-down, iron-down, copper-up]).

test(note_one_accepts_opposed_brass_and_iron) :-
    holds(1, [brass-up, iron-down, copper-up]),
    holds(1, [brass-down, iron-up, copper-down]).

% Note 2: if brass is up, copper is down. An implication, so it says nothing
% at all when brass is down -- which is the half a reader is most likely to
% get wrong.
test(note_two_rejects_brass_up_with_copper_up) :-
    \+ holds(2, [brass-up, iron-down, copper-up]).

test(note_two_accepts_brass_up_with_copper_down) :-
    holds(2, [brass-up, iron-down, copper-down]).

test(note_two_says_nothing_when_brass_is_down) :-
    holds(2, [brass-down, iron-up, copper-up]),
    holds(2, [brass-down, iron-up, copper-down]).

% Note 3: at least two levers are up.
test(note_three_counts_the_levers_that_are_up) :-
    holds(3, [brass-up, iron-up, copper-up]),
    holds(3, [brass-up, iron-up, copper-down]),
    \+ holds(3, [brass-up, iron-down, copper-down]),
    \+ holds(3, [brass-down, iron-down, copper-down]).

test(every_note_has_text) :-
    forall(constraint_text(Id, Text),
           ( integer(Id), Text \== '' )).

test(every_note_in_the_world_has_a_rule_and_some_text) :-
    forall(note(_Room, Id),
           ( constraint_text(Id, _),
             % A rule that no setting satisfies would make the puzzle
             % unsolvable, and a rule every setting satisfies would make the
             % note pointless. Both are caught by asking for one of each.
             once(( candidate(Yes), holds(Id, Yes) )),
             once(( candidate(No), \+ holds(Id, No) )) )).

test(every_note_is_findable_in_a_real_room) :-
    forall(note(Room, _Id), room(Room, _, _)).

% ---------------------------------------------------------------------------
% All three together -- the puzzle itself
% ---------------------------------------------------------------------------

test(exactly_one_solution) :-
    findall(Id, constraint_text(Id, _), Ids),
    findall(S, ( candidate(S), satisfies(Ids, S) ), Survivors),
    length(Survivors, 1).

test(the_solution_is_the_expected_one) :-
    findall(Id, constraint_text(Id, _), Ids),
    findall(S, ( candidate(S), satisfies(Ids, S) ), [Solution]),
    msort(Solution, Sorted),
    % Brass down forces iron up (note 1), and note 3 then needs copper up too.
    % Brass up would force copper down (note 2) and iron down (note 1), which
    % leaves only one lever up and fails note 3.
    Sorted == [brass-down, copper-up, iron-up].

test(fewer_notes_leave_more_than_one_answer) :-
    % The whole point of `deduce`: the player's knowledge is the premise set,
    % so a partly-explored mansion narrows the field without closing it.
    findall(S, ( candidate(S), satisfies([1], S) ), OneNote),
    findall(S, ( candidate(S), satisfies([1, 2], S) ), TwoNotes),
    length(OneNote, First),
    length(TwoNotes, Second),
    First > Second,
    Second > 1.

test(knowing_nothing_rules_nothing_out) :-
    findall(S, ( candidate(S), satisfies([], S) ), Survivors),
    length(Survivors, 8).

test(satisfies_agrees_with_holds_on_every_setting) :-
    findall(Id, constraint_text(Id, _), Ids),
    forall(candidate(Setting),
           ( satisfies(Ids, Setting)
           ->  forall(member(Id, Ids), holds(Id, Setting))
           ;   once(( member(Id, Ids), \+ holds(Id, Setting) )) )).

:- end_tests(levers).

:- begin_tests(map).

% `route/4` is what `go to <room>` walks. The mansion is small enough to check
% exhaustively, which is the cheapest way to catch a one-way corridor added by
% accident.

test(every_room_reachable_from_the_foyer) :-
    % Except the master bedroom, which is locked behind the key -- its
    % `connected/3` clause has a body, and the key is not in the inventory
    % here. That exception is the puzzle, so it is named rather than skipped.
    forall(( room(Room, _, _), Room \== foyer, Room \== master_bedroom ),
           route(foyer, Room, [foyer], _)).

test(the_master_bedroom_is_shut_without_the_key) :-
    \+ route(foyer, master_bedroom, [foyer], _).

test(a_room_is_a_zero_step_route_to_itself) :-
    once(route(library, library, [library], Path)),
    Path == [].

test(every_connection_leads_to_a_real_room) :-
    forall(clause(connected(From, _Direction, To), _),
           ( room(From, _, _), room(To, _, _) )).

test(routes_do_not_revisit_a_room) :-
    % The `Visited` list is what stops `route/4` looping forever on the
    % foyer-library-foyer cycle.
    findall(Path, route(foyer, cellar, [foyer], Path), Paths),
    forall(member(Path, Paths), ( length(Path, Len), Len =< 4 )).

:- end_tests(map).

:- begin_tests(world).

test(every_room_has_a_name_and_a_description) :-
    forall(room(_Id, Name, Description),
           ( Name \== '', Description \== '' )).

test(every_item_starts_in_a_real_room) :-
    forall(item_in_room(_Item, Room), room(Room, _, _)).

test(room_ids_are_unique) :-
    findall(Id, room(Id, _, _), Ids),
    sort(Ids, Sorted),
    length(Ids, Count),
    length(Sorted, Count).

:- end_tests(world).

:- begin_tests(parser).

% `phrase(command(C), Words)` is the grammar's own entry point (see
% parser.pl), so these drive it the same way mansion_escape.pl does, on
% cases pulled from the grammar's own rules: an adjective that disambiguates
% a noun phrase, the empty `go_verb` that lets a bare direction stand alone,
% `goto`'s literal "to", a lever named and left unnamed, a synonym on each of
% `start` and `quit`, and a line the grammar has no rule for at all.
%
% Each is wrapped in once/1: a phrase/2 goal leaves a choicepoint (there is
% usually a second, failing way to split the words), and plunit warns about
% that unless the test resolves it itself.

test(take_with_adjective) :-
    once(phrase(command(C), [take, the, rusty, key])),
    C == take(key).

test(bare_direction_shorthand) :-
    % go_verb --> [] lets "n" alone mean "go north".
    once(phrase(command(C), [n])),
    C == go(north).

test(go_to_room) :-
    once(phrase(command(C), [go, to, the, cellar])),
    C == goto(cellar).

test(pull_named_lever) :-
    once(phrase(command(C), [pull, the, brass, lever])),
    C == pull(brass).

test(pull_named_lever_without_the_word_lever) :-
    once(phrase(command(C), [pull, brass])),
    C == pull(brass).

test(pull_with_no_name_asks_which) :-
    % "lever" is not itself a lever/1 fact, so lever_name/1 fails and this
    % falls through to the pull_which rule instead.
    once(phrase(command(C), [pull, the, lever])),
    C == pull_which.

test(restart_synonym) :-
    once(phrase(command(C), [restart])),
    C == start.

test(quit_synonym) :-
    once(phrase(command(C), [exit])),
    C == quit.

test(examine_synonym_look_at) :-
    once(phrase(command(C), [look, at, the, old, book])),
    C == examine(book).

test(unknown_input_fails) :-
    \+ phrase(command(_), [flibbertigibbet]).

:- end_tests(parser).
