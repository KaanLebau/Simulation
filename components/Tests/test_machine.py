import unittest


from Machine import Machine
from MachineStates import MachineState
from Tool import Tool
import simpy

class TestMachine(unittest.TestCase):
    def setUp(self):
        self.env = simpy.Environment()

    def test_machine_environment(self):
        expected = self.env
        machine = Machine(env=self.env,machine_data={})
        actual = machine.env
        self.assertEqual(expected, actual, "Machine environment assignment failed")
    def test_machine_base(self):
        expected_name = 'MC1'
        expected_state = MachineState.IDLE
        expected_output_size = 1
        machine = Machine(env=self.env,machine_data={'name' : expected_name})
        actual_name = machine.name
        actual_state = machine.state
        actual_output_size = machine.output_size
        self.assertEqual(expected_output_size, actual_output_size, "Machine setting output size failed")
        self.assertEqual(expected_name, actual_name, "Machine setting name is failed")
        self.assertEqual(expected_state, actual_state, "Machine setting state is failed")
    def test_machine_types(self):
        for machine_type in ['input', 'output', 'inline', None]:
            with self.subTest(machine_type=machine_type):
                expected_type = machine_type if machine_type else "inline"
                machine = Machine(env=self.env, machine_data={'type': machine_type})
                actual_type = machine.type
                self.assertEqual(
                    actual_type,
                    expected_type,
                    f"Machine setting type '{machine_type if machine_type else 'empty'}' is failed"
                )
    def test_machine_ct(self):
        for ct in [100, None]:
            with self.subTest(ct=ct):
                expected_ct = ct if ct else 0
                machine = Machine(env=self.env, machine_data={'ct': ct})
                actual_ct = machine.ct
                self.assertEqual(
                    actual_ct,
                    expected_ct,
                    f"Machine setting type '{ct if ct else 'empty'}' is failed"
                )
    def test_machine_default_values(self):
        expected_defaults = {
            'name': "",
            'ct': 0,
            'type': "inline",
            'output_size': 1,
            'threshold': 10,
            'tool_warning': False,
            'quality_control_required': False,
            'output_buffer': 0,
            'buffer_utilization': 0,
            'quality_interval': 20,
            'quality_counter': 0,
            'quality_duration': 100,
            'ready_to_unload': False,
            'state': MachineState.IDLE,
        }
        machine = Machine(env=self.env, machine_data={})

        for attr, expected in expected_defaults.items():
            with self.subTest(attribute=attr):
                actual = getattr(machine, attr)
                self.assertEqual(actual, expected, f"Default value for '{attr}' is incorrect")
    def test_machine_tooling_empty(self):
        machine = Machine(env=self.env, machine_data={})
        self.assertEqual([], machine.tools.get_tools(),"Machine tools are empty")
    def test_machine_tooling_initial(self):
        expected_tools = [Tool(life=20, replacement_duration=5),
                 Tool(life=20, replacement_duration=5)]
        expected_threshold = 10
        machine_data= {'tools': expected_tools,'threshold': expected_threshold}
        machine = Machine(env=self.env, machine_data=machine_data)
        actual_tool_threshold = machine.threshold
        actual_tools = machine.tools.get_tools()
        self.assertFalse(machine.tool_warning, "Machine has correct tool warning signal")
        self.assertFalse(machine.quality_control_required, "Machine has correct tool replaced signal")
        self.assertEqual(expected_tools, actual_tools, "Machine initiate tools failed")
        self.assertEqual(expected_threshold, actual_tool_threshold, "Machine tool threshold failed")
    def test_machine_updates_tools(self):
        expected_tools = [Tool(life=2, current= 1, replacement_duration=5),
                          Tool(life=2, current= 1, replacement_duration=5)]
        initial_tools= [Tool(life=2, replacement_duration=5),
                          Tool(life=2, replacement_duration=5)]
        expected_threshold = 10
        machine_data = {'tools': initial_tools, 'threshold': expected_threshold}
        machine = Machine(env=self.env, machine_data=machine_data)
        machine.update_tooling()
        actual_tools = machine.tools.get_tools()
        self.assertEqual(expected_tools, actual_tools, "Machine update tools failed")
    def test_machine_tool_edge_case(self):
        expected_tools = [Tool(life=1, current=0, replacement_duration=5),
                          Tool(life=1, current=0, replacement_duration=5)]
        initial_tools = [Tool(life=1, replacement_duration=5),
                         Tool(life=1, replacement_duration=5)]
        expected_threshold = 10
        machine_data = {'tools': initial_tools, 'threshold': expected_threshold}
        machine = Machine(env=self.env, machine_data=machine_data)
        machine.update_tooling()
        actual_tools = machine.tools.get_tools()
        self.assertEqual(expected_tools, actual_tools, "Machine update tools failed")
        with self.assertRaises(ValueError):
            machine.update_tooling()
    def test_machine_tool_check(self):
        initial_tools = [Tool(life=11, replacement_duration=5),
                         Tool(life=11, replacement_duration=5)]
        threshold = 10
        machine_data = {'tools': initial_tools, 'threshold': threshold}
        machine = Machine(env=self.env, machine_data=machine_data)
        expected_state = MachineState.IDLE
        machine.tool_check()
        actual_state = machine.state
        self.assertFalse(machine.tool_warning, "Machine has correct toll warning signal")
        self.assertEqual(expected_state, actual_state, "Tool check checking with threshold is failed")
        initial_tools = [Tool(life=1, replacement_duration=5),
                         Tool(life=1, replacement_duration=5)]
        machine_data = {'tools': initial_tools, 'threshold': threshold}
        machine = Machine(env=self.env, machine_data=machine_data)
        expected_state = MachineState.WARNING
        machine.tool_check()
        actual_state = machine.state
        self.assertTrue(machine.tool_warning, "Machine has correct toll warning signal")
        self.assertTrue(machine.tool_warning, "Tool check sets tool signal failed")
        self.assertEqual(expected_state, actual_state, "Tool check setting Warning state failed")
        machine.update_tooling()
        expected_state = MachineState.STOPPED
        machine.tool_check()
        actual_state = machine.state
        self.assertEqual(expected_state, actual_state, "Tool check setting  Stopped state failed")
    def test_machine_tool_replacement(self):
        initial_tools = [Tool(life=11, replacement_duration=5, current=0),Tool(life=11, replacement_duration=5, current=0)]
        expected_duration = 10
        machine_data = {'tools': initial_tools, 'threshold': 10}
        machine = Machine(env=self.env, machine_data=machine_data)
        machine.tool_check()
        expected_state = MachineState.STOPPED
        actual_state = machine.state
        self.assertEqual(expected_state, actual_state, "Machine state before tool replacement  is not Stopped ")
        actual_duration = machine.replace_tooling()
        self.assertTrue(machine.quality_control_required, "Machine register tool replacement signal correct")
        self.assertEqual(expected_duration, actual_duration, "Machine do not return replacement duration correctly")
        expected_tools = [Tool(life=11, replacement_duration=5),Tool(life=11, replacement_duration=5)]
        actual_tools = machine.tools.get_tools()
        self.assertEqual(expected_tools, actual_tools, "Machine do not reset tool life ")
    def test_buffer_utilization(self):
        expected_output_size = 10
        expected_buffer_utilization = 0
        expected_output_buffer = 0
        machine = Machine(env=self.env, machine_data={"output_size": expected_output_size})
        actual_output_size = machine.output_size
        self.assertEqual(expected_output_size, actual_output_size, "Machine setting up output size incorrect")
        self.assertEqual(expected_output_buffer, machine.output_buffer, "Machine output buffer initially incorrect")
        self.assertEqual(expected_buffer_utilization, machine.buffer_utilization,"Machine buffer utilization incorrect")
        expected_buffer_utilization_increase = 3
        machine.output_buffer = expected_buffer_utilization_increase
        machine.update_buffer_utilization()
        self.assertEqual(expected_buffer_utilization_increase, machine.buffer_utilization, "Machine buffer utilization incorrect")
        expected_buffer_utilization_increase = 7
        machine.output_buffer = expected_buffer_utilization_increase
        machine.update_buffer_utilization()
        self.assertEqual(expected_buffer_utilization_increase, machine.buffer_utilization,"Machine buffer utilization incorrect")
        machine.output_buffer  = 4
        machine.update_buffer_utilization()
        self.assertEqual(expected_buffer_utilization_increase, machine.buffer_utilization,"Machine buffer utilization incorrect")
    def test_machine_update_buffer(self):
        machine = Machine(env=self.env, machine_data={"output_size": 10})
        expected_output_buffer = 4
        machine.output_buffer = expected_output_buffer
        self.assertEqual(expected_output_buffer, machine.output_buffer, "Machine initial output buffer incorrect")
        expected_updated_buffer = expected_output_buffer+1
        machine.load_buffer()
        self.assertEqual(expected_updated_buffer, machine.output_buffer, "Machine updates output buffer incorrect")
    def test_machine_load_spc_behavior(self):
        operator = simpy.Resource(self.env, capacity=1)
        machine_data = {
            "name": "MC1",
            "quality_duration": 2,
            "operator": operator
        }
        machine = Machine(env=self.env, machine_data=machine_data)

        # Start SPC load
        self.env.process(machine.load_spc())

        # t = 0.01: after start
        self.env.run(until=0.01)
        self.assertTrue(machine.spc.pending, "SPC should be pending immediately after loading")

        # t = 2.1: after duration
        self.env.run(until=2.1)
        self.assertFalse(machine.spc.pending, "SPC should not be pending after duration")
        self.assertTrue(machine.spc.is_ready_to_unload, "SPC should be ready to unload")
        self.assertTrue(machine.spc.occupied, "SPC should be occupied after duration")
    def test_machine_base_quality_configuration(self):
        expected_quality_duration = 100
        expected_quality_interval = 20
        machine = Machine(env=self.env, machine_data={"output_size": 10})
        self.assertEqual(expected_quality_duration, machine.quality_duration, "Machine quality configuration duration incorrect")
        self.assertEqual(expected_quality_interval, machine.quality_interval, "Machine quality configuration interval incorrect")
    def test_machine_quality_configuration(self):
        expected_quality_duration = 500
        expected_quality_interval = 10
        expected_quality_counter = 0
        machine_data = {'quality_interval': expected_quality_interval, 'quality_duration': expected_quality_duration}
        machine = Machine(env=self.env, machine_data=machine_data)
        self.assertEqual(expected_quality_duration, machine.quality_duration, "Machine quality configuration duration incorrect")
        self.assertEqual(expected_quality_interval, machine.quality_interval, "Machine quality configuration interval incorrect")
        self.assertEqual(expected_quality_counter, machine.quality_counter, "Machine quality configuration counter incorrect")
    def test_machine_spc_initialization(self):
        expected_quality_duration = 123
        expected_env = self.env
        machine = Machine(env=expected_env, machine_data={"quality_duration": expected_quality_duration})
        self.assertFalse(machine.spc.is_ready_to_unload, "Machine spc ready to unload initialization incorrect")
        self.assertIs(machine.spc.env, expected_env, "Spc environment was not set correctly")
        self.assertEqual(machine.spc.duration, expected_quality_duration, "Machine quality duration  and spc quality duration differs")
    def test_machine_equality(self):
        m1 = Machine(env=self.env, machine_data={"name": 'MC1'})
        m2 = Machine(env=self.env, machine_data={"name": 'MC1'})
        m3 = Machine(env=self.env, machine_data={"name": 'MC2'})

        self.assertTrue(m1.__eq__(m2),"Same machine result in False in comparison")
        self.assertFalse(m1.__eq__(m3),"Same machine result in True in comparison")
    def test_machine_setting_input_source(self):
        m1 = Machine(env=self.env, machine_data={"name": 'MC1'})
        m2 = Machine(env=self.env, machine_data={"name": 'MC2'})
        m3 = Machine(env=self.env, machine_data={"name": 'MC3'})

        self.assertIsNone(m1.input_source, "Machine with no input source failed")
        m1.set_input_source(None)
        self.assertIsNone(m1.input_source, "Machine with no input source failed")
        m1.set_input_source(m2)
        self.assertTrue(m1.input_source.__eq__(m2), "Machine with input source set incorrect")
        self.assertFalse(m1.input_source.__eq__(m3), "Machine with input source set incorrect")
    def test_machine_load(self):
        machine = Machine(env=self.env, machine_data={"name": 'MC1'})
        expected_part_state= ""
        self.assertFalse(machine.occupied, "Empty Machine is occupied  incorrect")
        self.assertFalse(machine.ready_to_unload, "Machine is ready to unload incorrect")
        self.assertEqual(expected_part_state, machine.part, "Initial part state is incorrect")
        machine.load_machine()
        expected_part_state= "processing"
        self.assertEqual(expected_part_state, machine.part, "Part state after loading is incorrect")
        self.assertTrue(machine.occupied, "Loaded Machine is occupied incorrect")
    def test_machine_unload_resets_state(self):
        machine = Machine(env=self.env, machine_data={"name": "MC1", "tools": [Tool(life=11, replacement_duration=2),
                      Tool(life=11, replacement_duration=1)],})
        machine.occupied = True
        machine.part = "processed"

        machine.unload_machine()

        self.assertFalse(machine.occupied, "Unload should reset occupied to False")
        self.assertEqual(machine.part, "raw", "Unload should set part state to 'raw'")
    @unittest.skip("Not implemented")
    def test_machine_is_ready(self):
        machine = Machine(env=self.env, machine_data={"name": "MC1", "output_buffer": 0})
        self.assertTrue(machine.is_ready(), "Empty machine send is ready signal incorrect")
        machine.load_machine()
        self.assertFalse(machine.is_ready(), "Machine is loaded part is in  processing state sends is ready signal incorrect")
        machine.part = "processed"
        self.assertTrue(machine.is_ready(), "Machine with processed part  send is ready signal incorrect")
    def test_machine_process_part(self):
        expected_tools = [Tool(life=20, replacement_duration=5),
                          Tool(life=20, replacement_duration=5)]
        expected_threshold = 10
        machine_data = {'tools': expected_tools, 'threshold': expected_threshold,"name": "MC1", "output_buffer": 0}
        machine = Machine(env=self.env, machine_data=machine_data)
        machine.load_machine()
        machine.process_part()
        expected_part_state= "processed"
        self.assertEqual(expected_part_state, machine.part, "Processed part state is incorrect")
        self.assertEqual(machine.number_of_parts, 1, "Processed part state is incorrect")
        self.assertEqual(machine.quality_counter, 1, "Processed part state is incorrect")
    def test_machine_quality_part(self):
        machine = Machine(env=self.env, machine_data={"name": "MC1", "output_buffer": 0})
        machine.quality_counter = 2
        self.assertFalse(machine.quality_check_part(), "Quality counter less than quality interval quality check failed")
        machine.quality_counter = 20
        self.assertTrue(machine.quality_check_part(), "Quality counter equal quality interval quality check failed")
        machine.quality_counter_reset()
        self.assertEqual(machine.quality_counter, 0, "Quality counter reset failed")
        self.assertFalse(machine.quality_check_part(), "Quality chak part  failed after resetting quality counter")
    def test_machine_run_triggers_process_part(self):
        initial_tools = [Tool(life=2, replacement_duration=5),
                         Tool(life=2, replacement_duration=5)]
        operator = simpy.Resource(self.env, capacity=1)
        threshold = 10
        machine_data = {
            "name": "mc1",
            "type": "input",
            "ct": 1,
            "tools":  initial_tools,
            "threshold": threshold,
            "output_size": 2,
            "operator": operator,
        }
        machine = Machine(env=self.env, machine_data=machine_data)
        #self.assertTrue(machine.is_ready(), "Empty machine send is ready signal incorrect")

        machine.load_machine()
        machine.start_signal.succeed()

        self.env.run(until=self.env.now + 1.1)

        self.assertTrue(machine.ready_to_unload, "Machine ready to unload incorrect")



        machine.unload_machine()
        machine.start_signal.succeed()
        self.env.run(until=self.env.now + 0.1)


        self.assertTrue(machine.tool_warning,"Machine tool warning")
    def test_machine_perform_tool_replacement_and_signals(self):
        initial_tools = [Tool(life=1, replacement_duration=1),
                         Tool(life=1, replacement_duration=2)]
        threshold = 10
        operator = simpy.Resource(self.env, capacity=1)
        expected_tool_replacement_duration = 3
        machine_data = {
            "name": "mc1",
            "type": "input",
            "ct": 1,
            "tools": initial_tools,
            "threshold": threshold,
            "output_size": 2,
            "operator": operator,
        }
        machine = Machine(env=self.env, machine_data=machine_data)

        machine.load_machine()

        self.assertEqual(machine.state, MachineState.IDLE, "Machine should be idle at the start")
        self.assertFalse(machine.quality_control_required, "Tool replacement signal should be False at the beginning")
        #self.assertFalse(machine.is_ready(), "Machine should be not ready during processing")
        self.assertEqual(machine.scrapped_part, 0, "Machine should scrap first part after tool replacement")

        machine.start_signal.succeed()
        self.env.run(until=self.env.now + machine.ct + 0.1)

        machine.unload_machine()
        machine.start_signal.succeed()

        self.env.run(until=self.env.now + 0.1)

        self.assertEqual(machine.state, MachineState.STOPPED, "Machine should enter 'Stopped' state before tool replacement")

        self.env.run(until=self.env.now + expected_tool_replacement_duration + 0.1)

        self.assertFalse(machine.tool_warning, "Machine should NOt have tool warning signal after tool replacement")
        self.assertEqual(machine.state, MachineState.IDLE, "Machine should be idle after tool replacement")
        self.assertTrue(machine.quality_control_required, "Tool replacement signal should be set")
        #self.assertTrue(machine.is_ready(), "Machine should be ready after tool replacement")

        machine.load_machine()
        machine.start_signal.succeed()
        self.env.run(until=self.env.now + machine.ct + machine.quality_duration + 0.1)

        self.assertFalse(machine.tool_warning, "Machine should NOt have tool warning signal after tool replacement")
        self.assertEqual(machine.scrapped_part, 1, "Machine should scrap first part after tool replacement")
        self.assertFalse(machine.quality_control_required, "quality_control_required should reset after quality delay")
        self.assertTrue(machine.ready_to_unload, "Machine should be ready to unload after processing")
    def test_machine_waits_operator_for_tool_replacement(self):

        operator = simpy.Resource(self.env, capacity=1)
        mc1 = Machine(env=self.env, machine_data={
            "name": "mc1",
            "tools": [Tool(life=11, replacement_duration=2, current=1),Tool(life=11, replacement_duration=1,current=1)],
            "ct": 1,
            "quality_duration" : 1,
            "output_size": 2,
            "operator": operator,
            },)
        mc2 = Machine(env=self.env, machine_data={
            "name": "mc2",
            "tools": [Tool(life=1, replacement_duration=1), Tool(life=1, replacement_duration=1)],
            "ct": 2,
            "quality_duration" : 1,
            "output_size": 2,
            "operator": operator,
        }, )

        mc1.load_machine()
        mc2.load_machine()
        mc1.start_signal.succeed()
        mc2.start_signal.succeed()
        self.env.run(until=self.env.now + 0.1)
        # t = 0.1
        with self.subTest("t = 0.1 - initial state "):
            self.assertEqual(0, mc1.scrapped_part,  "mc1 should 0 scrap part")
            self.assertEqual(0, mc2.scrapped_part,  "mc2 should 0 scrap part")
            self.assertTrue(mc1.occupied, "mc1 should occupied after loaded part")
            self.assertTrue(mc2.occupied, "mc2 should occupied after loaded part")
            self.assertEqual(mc1.part, "processing", "MC1 part should be in processing state after load")
            self.assertEqual(mc2.part, "processing", "MC2 part should be in processing state after load")
            self.assertEqual(MachineState.WORKING,mc1.state, "mc1 should be working at the start")
            self.assertEqual( MachineState.WORKING,mc2.state,  "mc2 should be working at the start")
            self.assertFalse(mc1.ready_to_unload, "mc1 should NOT be ready to unload during processing")
            self.assertFalse(mc2.ready_to_unload, "mc2 should NOT be ready to unload during processing")

        self.env.run(until=self.env.now + 1)
        # t = 1.1
        with self.subTest("t = 1.2  before mc1 unloading"):
            self.assertEqual(0, mc1.scrapped_part, "mc1 should 0 scrap part after first cycle")
            self.assertEqual(0, mc2.scrapped_part, "mc2 should 0 scrap part after first cycle")
            self.assertEqual(MachineState.IDLE, mc1.state, "mc1 should be idle at the start")
            self.assertEqual(MachineState.WORKING, mc2.state, "mc2 should be working at the start")
            self.assertTrue(mc1.ready_to_unload, "mc1 should be ready to unload after processing")
            self.assertFalse(mc2.ready_to_unload, "mc2 should NOT be ready to unload during processing")
        mc1.unload_machine()
        mc1.start_signal.succeed()
        with self.subTest("t = 1.2  after unloading"):
            self.assertEqual(MachineState.STOPPED, mc1.state, "mc1 should be stopped after unload at the start")
            self.assertEqual(MachineState.WORKING, mc2.state, "mc2 should be working at the start")
            self.assertFalse(mc1.ready_to_unload, "mc1 should NOT be ready to unload during tool change")
            self.assertFalse(mc2.ready_to_unload, "mc2 should NOT be ready to unload during processing")
            self.assertEqual(1, mc1.number_of_parts, "mc1 should be 1 part after unload")
            self.assertEqual(1, mc1.quality_counter, "mc1 should be 1 part after unload")

        self.env.run(until=self.env.now + 1)
        # t = 2.1
        with self.subTest("t = 2.1  before mc2 unloading"):
            self.assertEqual(MachineState.STOPPED, mc1.state, "mc1 should be stopped after unload at the start")
            self.assertEqual(MachineState.IDLE, mc2.state, "mc2 should be idle before unload")
            self.assertFalse(mc1.ready_to_unload, "mc1 should NOT be ready to unload during tool change")
            self.assertTrue(mc2.ready_to_unload, "mc2 should be ready to unload during after first cycle")
        mc2.unload_machine()
        mc2.start_signal.succeed()
        with self.subTest("t = 2.1  after mc2 unloading"):
            self.assertEqual(MachineState.STOPPED, mc1.state, "mc1 should be stopped during tool change")
            self.assertEqual(MachineState.STOPPED, mc2.state, "mc2 should be stopped waiting operator")
            self.assertFalse(mc1.ready_to_unload, "mc1 should NOT be ready to unload during tool change")
            self.assertFalse(mc2.ready_to_unload, "mc2 should NOt be ready to unload waiting operator")
            self.assertEqual(0, mc2.scrapped_part, "mc2 should 0 scrap part before tool change task done")
            self.assertEqual(0, mc1.scrapped_part, "mc1 should 0 scrap part before tool change task done")
            self.assertEqual(1, mc1.number_of_parts, "mc1 should have produces 1 part ")
            self.assertEqual(1, mc2.number_of_parts, "mc2 should have produces 1 part ")


        # t4
        self.env.run(until=self.env.now + 2.01)
        # t = 4.11
        with self.subTest("t = 4.11  operator shift from mc1 to mc2"):
            self.assertEqual(MachineState.IDLE, mc1.state, "mc1 should be Idle  after tool change and before a part is loaded")
            self.assertEqual(MachineState.STOPPED, mc2.state, "mc2 should be Stopped during tool change ")
        mc1.load_machine()
        mc1.start_signal.succeed()
        self.env.run(until=self.env.now + 0.01)
        # t = 4.12
        with self.subTest("t = 4.12  MC1 processing mc2 under tool change task "):
            self.assertEqual(MachineState.WORKING, mc1.state, "mc1 should be Working state for first part after tool change")
            self.assertTrue(mc1.quality_control_required, "mc1 should be indicates tools replaced")
            self.assertFalse(mc1.ready_to_unload, "mc1 should not to be ready to unload during processing")
            self.assertFalse(mc1.tool_warning, "mc1 should not send tool waring after tool change")
            self.assertEqual(MachineState.STOPPED, mc2.state, "mc2 should be Stopped during tool change")

        self.env.run(until=self.env.now + 1)
        # t = 5.12
        with self.subTest("t = 5.12 mc1 stopped for quality check waiting operator"):
            self.assertEqual(MachineState.STOPPED, mc1.state, "mc1 should be Stopped and wait quality check ")
            self.assertEqual(MachineState.STOPPED, mc2.state, "mc2 should be Stopped and still tool change is active")

        self.env.run(until=self.env.now + 1)
        # t = 6.12
        with self.subTest("t = 6.12 mc2 waiting part after tool change"):
            self.assertEqual(MachineState.IDLE, mc2.state, "mc2 should be Idle  after tool change and before a part is loaded")
        mc2.load_machine()
        mc2.start_signal.succeed()
        self.env.run(until=self.env.now + 0.01)
        #t = 6.13
        with self.subTest("t = 6.13 mc2 signal after tool change"):
            self.assertEqual(MachineState.WORKING, mc2.state, "mc2 should be Working state for first part after tool change")
            self.assertTrue(mc2.quality_control_required, "mc2 should be indicates tools replaced")
        self.env.run(until=self.env.now + 1)
        #t = 7.13
        with self.subTest("t = 7.13"):
            self.assertEqual(MachineState.IDLE,mc1.state, "mc1 should be Idle after tool change and before a part is loaded")
        mc1.unload_machine()
        mc1.load_machine()
        mc1.start_signal.succeed()
        self.env.run(until=self.env.now + 0.01)
        # t = 7.14
        with self.subTest("t = 7.14 "):
            self.assertEqual(MachineState.WORKING, mc1.state, "mc1 should be Working state for first part after tool change")
            self.assertEqual(MachineState.WORKING, mc2.state, "mc2 should be Working state for first part after tool change")

        self.env.run(until=self.env.now + 2)
        #t = 9.14
        with self.subTest("t = 9.14 "):
            self.assertEqual(MachineState.IDLE, mc2.state, "mc2 produces one part and waiting automation")
        with self.subTest("produced parts after test"):
            self.assertEqual(1, mc1.scrapped_part, "mc1 should 1 scrap part after tool change task done")
            self.assertEqual(1, mc2.scrapped_part, "mc2 should 1 scrap part after tool change task done")
            self.assertEqual(3, mc1.number_of_parts, "mc1 should have produces 2 parts")
            self.assertEqual(3, mc1.quality_counter, "mc1 quality counter should have produces 2 parts")
            self.assertEqual(2, mc2.quality_counter, "mc2 quality counter should have produces 2 parts")
    def test_machine_buffer_load(self):
        operator = simpy.Resource(self.env, capacity=2)
        mc1 = Machine(env=self.env, machine_data={
            "name": "mc1",
            "tools": [Tool(life=11, replacement_duration=2, current=1),
                      Tool(life=11, replacement_duration=1, current=1)],
            "ct": 1,
            "quality_duration": 1,
            "output_size": 2,
            "operator": operator,
        }, )

        self.assertEqual(0,mc1.output_buffer,"Machine buffer should be empty at the beginning")
        mc1.load_buffer()
        self.assertEqual(1,mc1.output_buffer,"Machine buffer should be 1 after loading ")
        mc1.load_buffer()
        self.assertEqual(2,mc1.output_buffer,"Machine buffer should be 2 after loading ")
        with self.assertRaises(ValueError):
            mc1.load_buffer()
    def test_machine_total_up_time(self):
        machine = self.get_machine()
        machine.load_machine()
        machine.start_signal.succeed()
        self.env.run(until=self.env.now + 1.1)
        self.assertEqual(1, machine.total_uptime, "machine.total_up_time should be 1")
        self.assertEqual(1, machine.number_of_parts, "machine.number_of_parts should be 1")
        machine.unload_machine()
        machine.load_machine()
        machine.start_signal.succeed()
        self.env.run(until=self.env.now + 1.1)
        self.assertEqual(2, machine.total_uptime, "machine.total_up_time should be 2")
        self.assertEqual(2, machine.number_of_parts, "machine.number_of_parts should be 2")
    def test_machine_total_downtime(self):
        machine = self.get_machine(tools=[Tool(life=2, replacement_duration=1, current=1), Tool(life=2, replacement_duration=1,current=1)])
        machine.load_machine()
        machine.start_signal.succeed()
        self.env.run(until=self.env.now + 1.01)
        machine.unload_machine()
        machine.start_signal.succeed()

        self.env.run(until=self.env.now + 2.01)
        machine.load_machine()
        machine.start_signal.succeed()
        with self.subTest("First tool change adds to downtime counter "):
            self.assertEqual(2, machine.total_downtime, "machine.total_downtime should be 2")
            self.assertAlmostEqual(2, machine.operator_work_time, places=6, msg="Operator time tracking failed")


        self.env.run(until=self.env.now + 2.01)
        machine.unload_machine()
        machine.load_machine()
        machine.start_signal.succeed()
        self.env.run(until=self.env.now + 1.01)
        machine.unload_machine()
        machine.start_signal.succeed()
        self.env.run(until=self.env.now + 2.01)
        machine.load_machine()
        machine.start_signal.succeed()
        with self.subTest("Machine handle several tool changes and  adds to downtime counter "):
            self.assertEqual(4, machine.total_downtime, "machine.total_downtime should be 4")
            self.assertAlmostEqual(4, machine.operator_work_time, places=6, msg="Operator time tracking failed")
    def test_machine_spc_cycle(self):
        initial_tools = [Tool(life=2, replacement_duration=5),
                         Tool(life=2, replacement_duration=5)]
        operator = simpy.Resource(self.env, capacity=1)
        threshold = 10
        machine_data = {
            "name": "mc1",
            "type": "input",
            "ct": 1,
            "tools": initial_tools,
            "threshold": threshold,
            "output_size": 2,
            "operator": operator,
            "quality_duration": 2,  # shorten for faster test
        }
        machine = Machine(env=self.env, machine_data=machine_data)

        def occupy_operator(env):
            with operator.request() as req:
                yield req
                yield env.timeout(0.03)

        with self.subTest("Initial state"):

            # t = 0
            self.assertFalse(machine.spc.occupied, "spc shouldbe empty at the beginning")
            self.assertTrue(machine.is_spc_empty(), "spc shouldbe empty at the beginning")

            machine.quality_control_required = True

        self.env.process(occupy_operator(self.env))
        self.env.process(machine.load_spc())
        # t = 0.1
        self.env.run(until=self.env.now + 0.01)

        with self.subTest("Spc is loaded and waiting the operator"):
            self.assertTrue(machine.spc.occupied, "spc should occupied after loading a part")
            self.assertFalse(machine.is_spc_empty(), "spc should occupied after unloading a part")
            self.assertTrue(machine.spc.pending, "spc should pending after loading a part")

        self.env.run(until=self.env.now + 0.1)
        with self.subTest("Operator is unloaded spc"):
            self.assertFalse(machine.spc.occupied, "spc should NOT occupied after loading a part")
            self.assertTrue(machine.is_spc_empty(), "spc should NOT occupied after loading a part")
            self.assertTrue(machine.spc.pending, "spc should pending after loading a part")

        self.env.run(until=self.env.now + 2)
        with self.subTest("Operator is loaded spc after inspection"):
            self.assertTrue(machine.spc.occupied, "spc should occupied after inspection a part")
            self.assertFalse(machine.is_spc_empty(), "spc should occupied after Inspection a part")
            self.assertFalse(machine.spc.pending, "spc should not be pending after inspection")
            self.assertTrue(machine.spc.is_ready_to_unload, "spc should b ready to unload after performed inspection")

        with self.subTest("Machine source output is spc"):
            self.assertEqual(machine.get_output_source(), 'Spc', "machine should indicates that there are a spc part to unload")

        machine.unload_spc()

        with self.subTest("Unloaded Spc has the correct outcome"):
            self.assertFalse(machine.spc.occupied, "spc should NOT occupied after unloading a part")
            self.assertTrue(machine.is_spc_empty(), "spc should NOT occupied after unloading a part")
            self.assertFalse(machine.spc.pending, "spc should not pending after performed inspection a part")
            self.assertFalse(machine.spc.is_ready_to_unload, "spc should NOT be ready to unload after performed inspection")
    def test_machine_output_buffer(self):
        initial_tools = [Tool(life=2, replacement_duration=5),
                         Tool(life=2, replacement_duration=5)]
        operator = simpy.Resource(self.env, capacity=1)
        threshold = 10
        machine_data = {
            "name": "mc1",
            "type": "input",
            "ct": 1,
            "tools": initial_tools,
            "threshold": threshold,
            "output_size": 2,
            "operator": operator,
            "quality_duration": 2,  # shorten for faster test
        }
        machine = Machine(env=self.env, machine_data=machine_data)

        machine.load_buffer()


        self.assertEqual(machine.get_output_source(), 'Buffer',
                             "machine should indicates that there are a buffer part to unload")
    def test_machine_output_source(self):
        initial_tools = [Tool(life=2, replacement_duration=5),
                         Tool(life=2, replacement_duration=5)]
        operator = simpy.Resource(self.env, capacity=1)
        threshold = 10
        machine_data = {
            "name": "mc1",
            "type": "output",
            "ct": 1,
            "tools": initial_tools,
            "threshold": threshold,
            "output_size": 2,
            "operator": operator,
            "quality_duration": 2,
        }
        machine = Machine(env=self.env, machine_data=machine_data)

        machine.load_buffer()
        machine.quality_control_required = True  # <--- 🔧 This was missing

        self.env.process(machine.load_spc())
        self.env.run(until=self.env.now + 5)
        self.assertTrue(machine.spc.occupied, "SPC should be occupied after inspection")
        self.assertTrue(machine.spc.is_ready_to_unload, "SPC should be ready to unload")
        self.assertEqual(machine.output_buffer, 1, "get_output_part unload buffer failed")


        self.assertEqual(machine.get_output_source(), 'Spc', "Machine should prioritize spc")
        machine.get_output_part()
        self.assertTrue(machine.is_spc_empty(), "get output  part prioritize SPC")
        self.assertEqual(machine.get_output_source(), 'Buffer', "Machine should prioritize spc")
        machine.get_output_part()

        self.assertEqual(0, machine.output_buffer, "get_output_part unload buffer failed")
    def get_machine(self, **overrides):
        machine_data = {
            "name": "MC1",
            "tools": [Tool(life=10, replacement_duration=1), Tool(life=10, replacement_duration=1)],
            "ct": 1,
            "quality_duration": 1,
            "quality_interval": 20,
            "output_size": 2,
            "operator": simpy.Resource(self.env, capacity=1),
        }
        machine_data.update(overrides)
        return Machine(env=self.env, machine_data= machine_data)



if __name__ == '__main__':
    unittest.main()
