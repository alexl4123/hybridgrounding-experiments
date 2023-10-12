
c(1) :- 2 <= #count{A,B,C: f(A,B), f(B,C), f(C,D), f(D,E), f(E,F), f(F,G), f(G,A), A != B, A != C, A != D, A != E, A != F, A != G, B != C, B != C, B != D, B != E, B != F, B != G, C != D, C != E, C != F, C != G, D != E, D != F, D != G, E != F, E != G, F != G}.
:- c(1).

