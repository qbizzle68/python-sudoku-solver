import unittest

from cell import Cell
from exceptions import CellValueContradiction, CellValueNotPossible


class TestCell(unittest.TestCase):

    def testInitialization(self):
        cell = Cell()
        self.assertListEqual(cell.candidates, [True] * 9)
        self.assertEqual(cell.value, 0)
        self.assertEqual(cell.count, 9)

        cell2 = Cell(0)
        self.assertEqual(hash(cell), hash(cell2))

        cell = Cell(5)
        self.assertListEqual(cell.candidates, [False] * 9)
        self.assertEqual(cell.value, 5)
        self.assertEqual(cell.count, 0)

    def testChangePossibilities(self):
        cell = Cell()
        for number in (1, 2, 5, 6, 9):
            cell[number] = False

        self.assertListEqual(cell.candidates, [False, False, True, True, False, False, True, True, False])
        self.assertEqual(cell.count, 4)
        self.assertEqual(cell.value, 0)

        cell[1] = True
        self.assertListEqual(cell.candidates, [True, False, True, True, False, False, True, True, False])
        self.assertEqual(cell.count, 5)
        self.assertEqual(cell.value, 0)

    def testCompleteCell(self):
        cell = Cell(1)
        cell[2] = True

        self.assertListEqual(cell.candidates, [False] * 9)
        self.assertEqual(cell.count, 0)
        self.assertEqual(cell.value, 1)

        cell = Cell()
        for i in range(1, 8):
            cell[i] = False

        cell[8] = False
        self.assertListEqual(cell.candidates, [False] * 9)
        self.assertEqual(cell.count, 0)
        self.assertEqual(cell.value, 9)

    def testValueBranches(self):
        cell = Cell(1)
        cell.value = 1
        self.assertEqual(cell.value, 1)

        with self.assertRaises(CellValueContradiction):
            cell.value = 2

        cell = Cell()
        cell[5] = False
        with self.assertRaises(CellValueNotPossible):
            cell.value = 5
