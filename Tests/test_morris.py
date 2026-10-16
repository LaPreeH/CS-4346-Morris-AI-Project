import unittest
from morris_engine import NEIGHBORS, MILLS, close_mill, legal_moves, search

class MorrisTests(unittest.TestCase):
    def test_neighbour_graph_symmetric(self):
        for i, adj in enumerate(NEIGHBORS):
            for j in adj:
                self.assertIn(i, NEIGHBORS[j])

    def test_mill_0(self):
        b = ['x']*23
        for i in (0,1,2): b[i]='W'
        self.assertTrue(close_mill(''.join(b), 0))

    def test_opening(self):
        self.assertEqual(len(legal_moves('x'*23,'W','opening')),23)

    def test_capture(self):
        b = ['x']*23
        for i in (0,1,5): b[i]='W'
        for i in (12,13): b[i]='B'
        result = legal_moves(''.join(b),'W','opening')
        capture = [p for p in result if p[2]=='W']
        self.assertEqual(len(capture),2)
        self.assertTrue(all(p.count('B')==1 for p in capture))

    def test_hopping(self):
        b = ['x']*23
        for i in (0,1,2): b[i]='W'
        for i in (8,9,10,11): b[i]='B'
        moves = legal_moves(''.join(b),'W','game')
        self.assertTrue(any(m[0]=='x' and m[22]=='W' for m in moves))

    def test_alpha_beta_matches_minimax(self):
        for board,phase,depth in [('x'*23,'opening',2),('xxxxxBxWWWWWBBBBxxxxxxx','game',2)]:
            minimax = search(board,depth,phase)
            alphabeta = search(board,depth,phase,alpha_beta=True)
            self.assertEqual((minimax.board,minimax.score),(alphabeta.board,alphabeta.score))
            self.assertLessEqual(alphabeta.evaluations,minimax.evaluations)

if __name__ == '__main__': unittest.main()
