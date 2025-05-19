import unittest

from Tool import Tool
from ToolManagement import ToolManagement


class TestToolManaggement(unittest.TestCase):

    def setUp(self):
        self.t1 = Tool(life=3, replacement_duration=10)
        self.t2 = Tool(life=5, replacement_duration=50)
        self.tm = ToolManagement([self.t1, self.t2])

    def test_shortest_life(self):
        expected = 3
        actual = self.tm.get_shortest_life()
        self.assertEqual(expected, actual, "Shortest life failed")

    def test_get_tools(self):
        expected = [Tool(life=3, replacement_duration=10),Tool(life=5, replacement_duration=50)]
        actual = self.tm.get_tools()
        self.assert_tool_lists_equal(expected, actual)


    def test_tool_update(self ):
        expected = [Tool(life=2, replacement_duration=10), Tool(life=4, replacement_duration=50)]
        actual = self.tm.get_tools()
        self.tm.tool_update()
        self.assert_tool_lists_equal(expected, actual)

    def test_replace_correct_tool(self):
        expected = [Tool(life=3, replacement_duration=10), Tool(life=2, replacement_duration=50)]
        self.tm.tool_update()
        self.tm.tool_update()
        self.tm.tool_update()
        self.tm.tool_replacement()
        actual = self.tm.get_tools()
        self.assert_tool_lists_equal(expected, actual)

    def test_set_tools(self):
        expected = [Tool(life=13, replacement_duration=10), Tool(life=12, replacement_duration=50)]
        self.tm.set_tools(expected)
        actual = self.tm.get_tools()
        self.assert_tool_lists_equal(expected, actual)

    def test_tool_replacement_duration_is_correct_one_tool(self):
        expected = 10
        tool_list = [Tool(life=1, replacement_duration=expected), Tool(life=12, replacement_duration=50)]
        self.tm.set_tools(tool_list)
        self.tm.tool_update()
        actual = self.tm.tool_replacement()
        self.assertEqual(expected, actual, "One tool replacement time is failed")

    def test_tool_replacement_duration_is_correct_for_several_tools(self):
        t1= 10
        t2 = 50
        expected = t1 + t2
        tool_list = [Tool(life=1, replacement_duration=t1), Tool(life=1, replacement_duration=t2)]
        self.tm.set_tools(tool_list)
        self.tm.tool_update()
        actual = self.tm.tool_replacement()
        self.assertEqual(expected, actual, "One tool replacement duration is incorrect")

    def test_tool_replacement_when_no_tool_worn(self):
        expected = 0
        actual = self.tm.tool_replacement()
        self.assertEqual(expected, actual, "Tool replacement called but there are no tool worn duration failed")


    def assert_tool_lists_equal(self, expected_list, actual_list):
        if len(expected_list) != len(actual_list):
            self.fail(f"List lengths differ: expected {len(expected_list)}, got {len(actual_list)}")

        for i in range(len(expected_list)):
            exp = expected_list[i]
            act = actual_list[i]
            if exp.get_life() != act.get_life():
                self.fail(f"Mismatch at index {i}: expected life {exp.get_life()}, got {act.get_life()}")
            if exp.get_replacement_duration() != act.get_replacement_duration():
                self.fail(f"Mismatch at index {i}: expected replacement duration {exp.get_replacement_duration()}, got {act.get_replacement_duration()}")

if __name__ == '__main__':
    unittest.main()
