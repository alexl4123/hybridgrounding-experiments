import sys
import random

def gen_graph(mx, prob):
    assert(prob >= 0)
    assert(prob <= 100)

    vertices = []
    edges = []

    for i in range(1,mx + 1):
        vertices.append(f"vertex({i}).")
        for j in range(1,mx + 1):
            if i == j:
                continue

            if random.randint(0,100) <= prob:
                edges.append("edge({0},{1}).".format(i,j))

    return (vertices, edges)

if __name__ == '__main__':

    number_vertices = int(sys.argv[1])
    prob = int(sys.argv[2])
    seed = int(sys.argv[3])
    repetition = int(sys.argv[4])

    random.seed(seed)

    vertices, edges = gen_graph(number_vertices, prob)

    print(f"seed({seed}).")
    print(f"num_vertices({number_vertices}).")
    print(f"edge_probability({prob}).")
    print(f"repetition({repetition}).")

    for vertex in vertices:
        print(vertex)

    for edge in edges:
        print(edge)


