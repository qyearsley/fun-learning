% ============================================================================
% PARSING PLAYER INPUT (Definite Clause Grammars)
% ============================================================================
% world.pl and commands.pl are the game. This file turns a typed line of
% English into one of the goals in commands.pl, so the player types "go north"
% rather than "go(north).".
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
% a sentence has two readings, the findall/3 in handle/1 (mansion_escape.pl)
% collects both.
% ============================================================================

% Top-level command forms. Each produces a goal defined in commands.pl.
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
% guard, which checks the fact in world.pl, is what keeps "pull the lever" from
% parsing two ways, with "the" and "lever" each able to fill a bare slot.
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
