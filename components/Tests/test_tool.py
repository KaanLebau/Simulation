import unittest

from Tool import Tool

class TestTool(unittest.TestCase):


    def test_initial_life(self):
        expected = 5
        tool= Tool(life=expected, replacement_duration=10)
        actual = tool.get_life()
        self.assertEqual(expected,actual,"Tool life failed")

    def test_initial_replacement_duration(self):
        expected = 10
        tool= Tool(life=5, replacement_duration=expected)
        actual = tool.get_replacement_duration()
        self.assertEqual(expected,actual, "Tool replacement duration failed")


    def test_initial_with_current(self):
        expected = 5
        tool= Tool(life=10, replacement_duration=10,current=expected)
        actual = tool.get_life()
        self.assertEqual(expected,actual,"Tool creation with current  failed")

    def test_use_tool(self):
        expected = 5
        tool = Tool(life=6, replacement_duration=10)
        tool.use()
        actual = tool.get_life()
        self.assertEqual(expected,actual,"Tool usage failed")


    def test_is_worn_out_false(self):
        tool= Tool(life=6, replacement_duration=10)
        actual = tool.is_worn_out()
        self.assertFalse(actual,"Tool life is Not worn out failed")

    def test_is_worn_out_true(self):
        tool= Tool(life=1, replacement_duration=10)
        tool.use()
        actual = tool.is_worn_out()
        self.assertTrue(actual,"Tool life is worn out failed")

    def test_replace_without_need(self):
        expected = 5
        tool=Tool(life=5, replacement_duration=10)
        tool.replace()
        actual = tool.get_life()
        self.assertEqual(expected,actual,"Tool replacement failed")


    def test_replaceent_working(self):
        expected = 5
        tool=Tool(life=expected,replacement_duration=10,current=1)
        tool.use()
        tool.replace()
        actual = tool.get_life()
        self.assertEqual(expected,actual,"Tool replacement failed")

    def test_tool_life_never_less_tahn_0(self):
        tool= Tool(life=1, replacement_duration=10)
        tool.use()
        with self.assertRaises(ValueError):
            tool.use()

    def test_tool_usage_after_toolreplacement(self):
        expected = 5
        tool=Tool(life=expected,replacement_duration=10,current=1)
        tool.use()
        tool.replace()
        tool.use()
        actual = tool.get_life() + 1
        self.assertEqual(expected,actual,"Tool usage after replacement failed")

if __name__ == '__main__':
    unittest.main()
