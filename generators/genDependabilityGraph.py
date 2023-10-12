import sys
import random

mx = int(sys.argv[1])
prob = int(sys.argv[2])
#set_count = int(sys.argv[3])
#prob_sets = int(sys.argv[4])

assert(prob >= 0)
assert(prob <= 100)

#assert(prob_sets >= 0)
#assert(prob_sets <= 100)

#assert(set_count >= 1)
assert(mx >= 1)

vertices = []
edges = []
sets = []

for i in range(1,mx):
    vertices.append(f"vertex({i}).")

    #vertex_in_set = random.randint(1,set_count)

    #sets.append(f"set({i},{vertex_in_set}).")

    for j in range(1,mx):
        if random.randint(0,100) <= prob:
            edges.append("edge({0},{1}).".format(i,j))

for vertex in vertices:
    print(vertex)

for edge in edges:
    print(edge)

"""
for set_ in sets:
    print(set_)
"""

