% ============================================================================
% THE WORLD
% ============================================================================
% The mansion itself: which rooms exist, how they join up, what is lying
% around, what the notes say, and how the lever mechanism works.
%
% This is the best place to start reading. The map, the items and the notes are
% plain facts; the lever mechanism at the bottom is rules. Two of those rules
% are small, and between them they make the whole argument for writing a game
% this way:
%
%   connected(upstairs_hall, north, master_bedroom) :- inventory(key).
%   can_see, with two clauses.
%
% The first is an AND - you may pass IF you hold the key. The second is an OR -
% you can see if the room is lit, OR you are carrying the lamp. Neither the
% movement code nor the path planner in commands.pl knows anything about keys
% or lamps; the puzzle lives in the shape of the world.
% ============================================================================

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
% "take the rusty key" works as well as "take key". The parser in parser.pl
% checks typed adjectives against these facts.
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
