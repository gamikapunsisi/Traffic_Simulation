import unittest
from maxflow import edmonds_karp, dinic

class TestMaxFlowAlgorithms(unittest.TestCase):
    def test_simple_graph(self):
        # Simple known graph
        g = {
            "A": {"B": 3, "C": 2},
            "B": {"C": 1, "T": 2},
            "C": {"T": 3},
            "T": {}
        }
        ek = edmonds_karp(g, "A", "T")
        dn = dinic(g, "A", "T")
        self.assertEqual(ek, dn)
        self.assertEqual(ek, 4)  # expected max flow is 4

    def test_bottleneck(self):
        g = {
            "A":{"B":5},
            "B":{"C":3},
            "C":{"T":4},
            "T":{}
        }
        ek = edmonds_karp(g, "A", "T")
        dn = dinic(g, "A", "T")
        self.assertEqual(ek, dn)
        self.assertEqual(ek, 3)

if __name__ == "__main__":
    unittest.main()