
class ToolManagement:
    def __init__(self, tools):
        """
               Description:
                   Initializes the ToolManagement class with a list of Tool objects.

               Input:
                   tools (list): A list of Tool instances.

               Output:
                   Initializes internal state with the given tools.

               Example of use:
                   tools = [Tool(5, 10), Tool(10, 5)]
                   manager = ToolManagement(tools)
               """
        self.tools = tools

    def get_shortest_life(self):
        """
                Description:
                    Returns the lowest remaining life among all tools.

                Input:
                    None

                Output:
                    int: The shortest current life among the tools.
                    Raises ValueError if the tools list is empty.

                Example of use:
                    shortest = manager.get_shortest_life()
                """
        if self.tools == []:
            raise ValueError('There are no tools int the list')
        return min(tool.get_life() for tool in self.tools)

    def tool_update(self):
        """
                Description:
                    Applies one usage cycle to all tools (reduces current life by 1).
                    Raises an exception if a tool is already worn out.

                Input:
                    None

                Output:
                    Modifies tool states in-place by decrementing their current life.
                    May raise ValueError from Tool.use() if a tool is already worn out.

                Example of use:
                    manager.tool_update()
                """
        for tool in self.tools:
            tool.use()

    def tool_replacement(self):
        """
                Description:
                    Replaces all worn-out tools and accumulates their replacement duration.

                Input:
                    None

                Output:
                    int: Total time needed to replace all worn-out tools.

                Example of use:
                    downtime = manager.tool_replacement()
                """
        duration = 0
        for tool in self.tools:
            if tool.is_worn_out():
                tool.replace()
                duration += tool.get_replacement_duration()
        return duration

    def get_tools(self):
        """
               Description:
                   Returns the current list of tools.

               Input:
                   None

               Output:
                   list: The list of Tool instances managed.

               Example of use:
                   tool_list = manager.get_tools()
               """
        return self.tools

    def set_tools(self, tools):
        """
               Description:
                   Replaces the current tool list with a new list.

               Input:
                   tools (list): A new list of Tool instances.

               Output:
                   Replaces internal tool list.

               Example of use:
                   manager.set_tools([Tool(10, 5)])
               """
        self.tools = tools

    def __str__(self):
        tool_list = "[ "
        for tool in self.tools:
            tool_list += str(tool) + " "
        tool_list += "]"
        return tool_list
