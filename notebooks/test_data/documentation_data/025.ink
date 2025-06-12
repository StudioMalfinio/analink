-> start
=== start ===
You're standing at a crossroads. Where would you like to go?

* [Go to Paris] -> paris
* [Go to Rome] -> rome

=== paris ===
You arrive in beautiful Paris! The Eiffel Tower gleams in the distance.
+ [Return to crossroads] -> crossroads_again

=== rome ===
Welcome to Rome! The Colosseum stands majestically before you.
+ [Return to crossroads] -> crossroads_again

=== crossroads_again ===
You're back at the crossroads, but now you have some travel experience.

* {not paris} [Go to Paris] -> paris
* {not rome} [Go to Rome] -> rome
+ {paris} [Return to Paris] -> paris
+ {rome} [Return to Rome] -> rome
* {paris AND rome} [You've been everywhere! Time to go home] -> END