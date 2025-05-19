
import unittest
import simpy
from numpy.ma.testutils import assert_equal

from Machine import Machine
from MachineStates import MachineState
from Automation import Automation
from Tool import Tool


class TestAutomation(unittest.TestCase):

    def setUp(self):
        self.env = simpy.Environment()
        self.operator = simpy.Resource(self.env, capacity=1)


    def create_operator(self):
      simpy.Resource(self.env, capacity=1)
    def create_input_machine(self, **kwargs):
        data = {
            "name": "MC_in",
            "type": "input",
            "ct": 1,
            "output_size": 10,
            "quality_interval": 6,
            "tools": [Tool(life=20, replacement_duration=1)],
            "threshold": 10,
            "quality_duration": 2,
            'operator': self.operator,
        }
        data.update(kwargs)
        return Machine(env=self.env, machine_data=data)
    def create_output_machine(self, **kwargs):
        data ={"name": "MC_out",
            "type": "output",
            "ct": 1,
            "output_size": 10,
            "quality_interval": 6,
            "tools": [Tool(life=20, replacement_duration=1)],
            "threshold": 10,
            "quality_duration": 2,
            'operator': self.operator}
        data.update(kwargs)
        return Machine(env=self.env, machine_data=data)
    def create_inline_machine(self, **kwargs):
        data = {
            "name": "MC_line",
            "ct": 2,
            "output_size": 5,
            "tools": [Tool(life=10, replacement_duration=1)],
            "threshold": 10,
            "quality_interval": 10,
            "quality_duration": 2,
            'operator': self.operator,
        }
        data.update(kwargs)
        return Machine(env=self.env, machine_data=data)

    def test_automation_triggers_a_machine_processing(self):
        machine = self.create_input_machine()
        automation = Automation(env=self.env, machines=[machine])
        time = self.env.now +10.1
        self.env.run(until=time)
        # Check if machine processed the part (output_buffer increases)

        self.assertEqual(1, machine.output_buffer, "Automation has triggered start_signal buffer has 1 part")
        self.assertEqual(1, machine.number_of_parts, "Automation has triggered start_signal Machine has  process 1 part")
        time += 6
        self.env.run(until=time)
        self.assertEqual(2, machine.output_buffer, "Machine has 3 part in buffer")
        self.assertEqual(2, machine.number_of_parts,"Machine has processed 2 part" )
        time += 5.5
        self.env.run(until=time)
        self.assertEqual(3, machine.output_buffer, "Machine has 3 part in buffer")
        self.assertEqual(3, machine.number_of_parts, "Machine has processed 3 part")
        time += 5.5
        self.env.run(until=time)
        self.assertEqual(4, machine.output_buffer, "Machine has 4 part in buffer")
        self.assertEqual(4, machine.number_of_parts, "Machine has processed 4 part")
        time += 5.5
        self.env.run(until=time)
        self.assertEqual(5, machine.output_buffer, "Machine has 5 part in buffer")
        self.assertEqual(5, machine.number_of_parts, "Machine has processed 5 part")

    def test_automation_handle_spc_part_route(self):
        machine = self.create_input_machine()
        automation = Automation(env=self.env, machines=[machine])

        time = self.env.now
        time +=32.22
        self.env.run(until=time)
        # Check if machine processed the part (output_buffer increases)
        self.assertEqual(5, machine.output_buffer, "Automation should have triggered machine to process part")

        def busy():
            with self.operator.request() as req:
                yield req
                yield self.env.timeout(0.03)

        with self.subTest("before spc part triggered and machine is correct state before quality check"):
            self.assertEqual(5, machine.output_buffer, "Machine do NOT has all 5 part stored in Buffer")
            self.assertEqual(5, machine.quality_counter, "Machine quality counter failed")
            self.assertFalse(machine.quality_check_part(),
                             "Machine has wrong state before spc part Quality check part ")
            self.assertFalse(machine.spc.pending, "Machine spc has WRONG state before spc part")

        time += 0.01
        self.env.process(busy())
        self.env.run(until=time)
        self.assertTrue(self.operator.count > 0, "Operator is busy failed")
        self.assertEqual([], self.operator.queue, "Operator waiting tasks failed")

        time += 5.5

        self.env.run(until=time)
        with self.subTest("Machine produces the quality part"):
            self.assertEqual(6, machine.number_of_parts, "Machine produces wrong number of part before spc routing")
            self.assertEqual(6, machine.quality_counter, "Machine quality counter resets failed")
        time += 0.8
        self.env.run(until=time)
        with self.subTest("part route checks "):
            self.assertEqual(6, machine.number_of_parts, "Machine produces wrong number of part before spc routing")
            self.assertEqual(5, machine.output_buffer, "Machine has more part in buffer then possible")
        time += 0.01
        self.env.process(busy())
        self.env.run(until=time)
        with self.subTest("operator is busy and spc is pending state"):
            self.assertEqual(1, self.operator.count, "Operator is not busy when expected")
            self.assertTrue(machine.spc.pending, "Spc state turn to pending after loaded part")
        time += 2.1
        self.env.run(until=time)
        with self.subTest("operator is done with control spc is ready to unload state"):
            self.assertTrue(machine.spc.is_ready_to_unload, "inspection is Done failed")
            self.assertTrue(machine.spc.occupied, "Spc is occupied after inspection")
            self.assertFalse(machine.spc.pending, "Spc is NOT in pending state after control failed")

    def test_machine_downstream_blockage(self):
        m1 = self.create_input_machine(output_size=2)
        m2 = self.create_inline_machine(ct=25)
        m2.set_input_source(m1)
        automation = Automation(env=self.env, machines=[m1, m2])


        time = self.env.now + 2
        self.env.run(until=time)
        with self.subTest("Machine state during loading"):
            self.assertEqual(MachineState.IDLE, m1.state, "Machine 1 state during loading is Idle")
            self.assertEqual(MachineState.IDLE, m2.state, "Machine 2 state is Idle before m1 produces part")
        time = self.env.now + 2.6
        self.env.run(until=time)
        with self.subTest("Machine state before machine is ready"):
            self.assertAlmostEqual(4.5, m1.total_idle_time,2,"Machine 1 downtime should be equal to 4.5")
            self.assertEqual(MachineState.WORKING, m1.state, "Machine state before machine is ready is working")
            self.assertFalse(m1.is_ready(), "Machine is not ready during working state")
            self.assertEqual(MachineState.IDLE, m2.state, "Machine 2 state is Idle during m1 produces first part")
            self.assertEqual(0, m1.number_of_parts, "Machine 1 part counter is 0 " )
        time = self.env.now + 1
        self.env.run(until=time)
        with self.subTest("Machine state after produced part machine is ready"):
            self.assertEqual(MachineState.IDLE, m1.state, "Machine state after produced part machine is ready")
            self.assertEqual(MachineState.IDLE, m2.state, "Machine 2 state is Idle during m1 is unloading")
            self.assertEqual(1, m1.number_of_parts, "Machine 1 part counter is 1 " )
            self.assertTrue(m1.is_ready(), "Machine 1 should be ready after producing one part")
            self.assertTrue(m2.is_ready(), "Machine 2 should be ready for load a part")
        time = self.env.now + 9.5
        self.env.run(until=time)
        with self.subTest("Machine state after unload part machine is ready"):
            self.assertAlmostEqual(14.6, m2.total_idle_time, 2, "Machine 2 total idle time after load  equal to 14.6")
            self.assertTrue(m2.occupied,"Machine 2 is loaded first part")
            self.assertEqual(0, m2.number_of_parts, "Machine 2 have not produced a part yet")
            self.assertEqual(MachineState.WORKING, m2.state, "Machine 2 has working state after loaded")
            self.assertEqual(MachineState.IDLE, m1.state, "Machine 1 has Idle state during automation is busy with loading m2")
        time = self.env.now + 5
        self.env.run(until=time)
        with self.subTest("Machine state after unload part machine is ready"):
            self.assertEqual(1, m1.output_buffer, "Machine 1 output buffer should have 1 part")
            self.assertTrue(m1.occupied, "Machine 1 producing 3 th  part")
            self.assertEqual(MachineState.WORKING, m1.state, "Machine 1 has working state")
            self.assertEqual(MachineState.WORKING, m2.state, "Machine 2 has working state")
        time = self.env.now + 6
        self.env.run(until=time)
        with self.subTest("Machine state after unload part machine is ready"):
            self.assertEqual(2, m1.output_buffer, "Machine 1 output buffer should have 1 part")
            self.assertTrue(m1.occupied, "Machine 1 producing 3 th  part")
            self.assertEqual(MachineState.IDLE, m1.state, "Machine 1 has working state")
            self.assertEqual(MachineState.WORKING, m2.state, "Machine 2 has working state")
            self.assertFalse(m1.is_ready(), "Machine 1 should be ready after unload part")
        time = self.env.now + 13.5
        print(time)
        self.env.run(until=time)
        with self.subTest("M2 is ready for unload "):
            self.assertEqual(2, m1.output_buffer, "Machine 1 output buffer is full ")
            self.assertEqual(MachineState.IDLE, m2.state, "Machine 2 has idle state during unload")
            self.assertEqual(4, m1.number_of_parts, "Machine 1 can only produce 4 part during this time period")
            self.assertAlmostEqual(21.7, m1.total_idle_time,2, "Machine 1 total idle time should be 21.7")
            self.assertAlmostEqual(4, m1.total_uptime,2, "Machine 1 total uptime should be 4")

    def test_machine_spc_routing_with_two_machines(self):
        m1 = self.create_input_machine(output_size=1, ct=1.5,quality_interval=2,quality_counter=1,quality_duration=1)
        m2 = self.create_inline_machine(output_size=1, ct=12.5)
        m2.set_input_source(m1)
        automation = Automation(env=self.env, machines=[m1, m2])

        time = self.env.now + 1.5
        self.env.run(until=time)
        self.assertEqual(1, automation.arm.count, "Automation is busy")

        time = self.env.now +3.1
        self.env.run(until=time)
        with self.subTest("After m1 is loaded"):
            self.assertTrue(m1.occupied, "Machine 1 should be occupied")
            self.assertEqual(MachineState.WORKING, m1.state, "Machine 1 should be in working state")
        time = self.env.now + 1
        self.env.run(until=time)
        self.assertEqual(0, automation.arm.count, "Automation is NOT busy")
        time = self.env.now +0.5
        self.env.run(until=time)
        with self.subTest("Machine 1 is produce one part"):
            self.assertEqual(MachineState.IDLE, m1.state, "Machine 1 should be in Idle state")
            self,assert_equal(2, m1.quality_counter, "Machine 1 quality counter should be 2")
            self.assertEqual(1, m1.number_of_parts, "M1 should have produced 1 parts")
            self.assertTrue(m1.quality_check_part(),"Part should be mark as quality")
            self.assertTrue(m1.occupied, "Machine 1 should be still occupied with part 1")
        time  = self.env.now + 3.5
        self.env.run(until=time)
        self.assertEqual(1, automation.arm.count, "Automation is busy")
        time = self.env.now +1.1
        self.env.run(until=time)
        with self.subTest("Part should loaded to SPC"):
            self.assertTrue(m1.spc.pending, "Spc should have pending state ")
            self.assertEqual(0, m1.output_buffer, "M1 buffer should be empty")
            self.assertTrue(m1.occupied, "Machine 1 should be occupied")
            self.assertEqual(MachineState.WORKING, m1.state, "Machine 1 should be in Working state")
        time += 0.5
        self.env.run(until=time)
        with self.subTest("Part should be in SPC and handling "):
            self.assertTrue(m1.spc.pending, "Spc should have pending state ")
            self.assertFalse(m1.spc.occupied, "Machine 1 spc should be  not occupied")
            #self.assertEqual(1, self.operator.count,"Operator should be busy")
        time += 0.4
        self.env.run(until=time)
        with self.subTest("Part should be in SPC and handling "):
            self.assertFalse(m1.spc.pending, "Spc should have NOT pending state ")
            self.assertTrue(m1.spc.occupied, "Machine 1 spc should be occupied")

        time += 0.2
        self.env.run(until=time)
        with self.subTest("SPC part shold unloaded and loaded to M2 "):
            self.assertFalse(m1.spc.pending, "Spc should NOT have pending state ")
            self.assertTrue(m1.is_spc_empty(), "Spc should be empty")
            self.assertEqual(1, automation.arm.count, "Automation is busy")
        time += 0.4
        self.env.run(until=time)
        with self.subTest("M1 shld produced one part during quality check and m2 is loading state"):
            self.assertTrue(m1.is_ready(), "M1 should be ready to unload ")
            self.assertEqual(MachineState.IDLE, m1.state, "Machine 1 has idle state during automations is busy")
            self.assertEqual(1, automation.arm.count, "Automation is busy")
        time += 4
        self.env.run(until=time)
        with self.subTest("M2 shold be loaded and working state"):
            self.assertTrue(m2.occupied, "M2 should be occupied")
            self.assertEqual(MachineState.WORKING, m2.state, "Machine 2 has working state")
            self.assertTrue(m1.is_ready(), "M1 still ready and waiting")
        time += 1
        self.env.run(until=time)
        with self.subTest("SPC part shold unloaded and loaded to M2"):
            self.assertEqual(1, automation.arm.count, "Automation is busy")
        time += 3.6
        self.env.run(until=time)
        with self.subTest("M1 is loaded and start working"):
            self.assertTrue(m1.occupied,"M1 should be occupied")
            self.assertFalse(m1.is_ready(),"M1 should not be ready")
            self.assertEqual(MachineState.WORKING, m1.state, "Machine 1 has working state")
            self.assertEqual(0, automation.arm.count, "Automation is NOT busy")
        time += 1.5
        self.env.run(until=time)
        with self.subTest("M1 shuld be done with part and waiting the m2 and m2 still running first part"):
            self.assertTrue(m1.occupied, "M1 should be occupied")
            self.assertTrue(m2.occupied, "M2 should be occupied")
            self.assertEqual(MachineState.WORKING, m2.state, "Machine 2 has working state")
            self.assertEqual(MachineState.IDLE, m1.state, "Machine 1 has idle state")

    def test_machine_tool_replacement_flow_route_in_automation(self):
        tools = [Tool(life=20, replacement_duration=2, current=2),Tool(life=20, replacement_duration=2, current=2), Tool(life=20, replacement_duration=2,current=2)]
        m1 = self.create_input_machine()
        m2 = self.create_inline_machine(tools=tools)
        m2.set_input_source(m1)
        automation = Automation(env=self.env, machines=[m1, m2])

        with self.subTest("Test starting state"):
            self.assertTrue(m1.is_ready(),"M1 should be ready")
            self.assertFalse(m1.occupied,"M1 should be empty")
            self.assertTrue(m2.is_ready(),"M2 should be ready")
            self.assertFalse(m2.occupied,"M2 should be empty")
            self.assertEqual(0,m1.output_buffer,"M1 buffer is empty")
            self.assertEqual(0,m2.output_buffer,"M2 buffer is empty")
            self.assertEqual(2, m2.tools.get_shortest_life(),"Testing shorted tool life is 2")
        time = self.env.now + 14.5
        self.env.run(until=time)
        with self.subTest("M1 is done with part 2 and automation is laoding m2"):
            self.assertEqual(MachineState.IDLE, m1.state, "Machine 1 has working state")
            self.assertEqual(1, automation.arm.count, "Automation is busy")
            self.assertTrue(m1.occupied,"M1 should be occupied")
            self.assertFalse(m2.occupied,"M2 should be NOT occupied")
        time += 0.3
        self.env.run(until=time)
        with self.subTest("M2 is loaded now automation is busy with unloading m1 "):
            self.assertEqual(MachineState.WORKING, m2.state, "Machine 1 has working state")
            self.assertEqual(1, automation.arm.count, "Automation is busy")
            self.assertTrue(m1.occupied, "M1 should be occupied")
            self.assertTrue(m2.occupied, "M2 should be occupied")
        time += 1.9
        self.env.run(until=time)
        with self.subTest("M2 is idle state automation still busy with m1"):
            self.assertEqual(MachineState.IDLE, m2.state, "Machine 1 has working state")
            self.assertEqual(1, m2.tools.get_shortest_life(),"Testing shorted tool life is 2")
            self.assertEqual(1, automation.arm.count, "Automation is busy")
            self.assertEqual(1, m2.tools.get_shortest_life(),"M1 should be occupied")
        time+= 2.4
        self.env.run(until=time)
        with self.subTest("M1 is loading m2 waiting"):
            self.assertTrue(m1.occupied,"M1 should be occupied")
            self.assertEqual(MachineState.IDLE, m2.state, "Machine 2 has Idle state")
            self.assertEqual(MachineState.IDLE, m1.state, "Machine 1 has Idle state")
            self.assertEqual(1, automation.arm.count, "Automation is busy")
        time += 0.3
        self.env.run(until=time)
        with self.subTest("M2 is loading m1 is processing"):
            self.assertEqual(MachineState.WORKING, m1.state, "Machine 1 has working state")
            self.assertEqual(MachineState.IDLE, m2.state, "Machine 2 has working state")
            self.assertEqual(1, automation.arm.count, "Automation is busy")
            self.assertEqual(1,m2.tools.get_shortest_life(),"M1 ready to unload")
        time += 1
        self.env.run(until=time)
        with self.subTest("M1 Waiting state"):
            self.assertEqual(MachineState.IDLE, m1.state, "Machine 1 has Idle state")
            self.assertEqual(MachineState.IDLE, m2.state, "Machine 2 has Idle state")
            self.assertEqual(3, m1.number_of_parts, "M1 has produced 3 part")
            self.assertEqual(1, m2.number_of_parts, "M1 has produced 3 part")
            self.assertEqual(1, automation.arm.count, "Automation is busy")
        time += 3.45
        self.env.run(until=time)
        with self.subTest("M2 part number 2 in process"):
            self.assertEqual(MachineState.IDLE, m1.state, "Machine 1 has Idle state")
            self.assertEqual(1,m2.tools.get_shortest_life(),"M1 ready to unload")
            self.assertEqual(MachineState.WARNING, m2.state, "Machine 2 has Warning state due to tool life 1")
            self.assertEqual(3, m1.number_of_parts, "M1 has produced 3 part")
            self.assertEqual(1, m2.number_of_parts, "M2 has produced 1 part")
            self.assertEqual(1, automation.arm.count, "Automation is busy")
        time += 4.5
        self.env.run(until=time)
        with self.subTest("m1 is working m2 is  loading"):
            self.assertEqual(MachineState.WORKING, m1.state, "Machine 1 has Working state")
            self.assertEqual(MachineState.IDLE, m2.state, "Machine 2 has Idle state")

        time +=1.1
        self.env.run(until=time)
        with self.subTest("m1 is idle m2 is  loading"):
            self.assertEqual(MachineState.IDLE, m2.state, "Machine 2 has Idle state")
            self.assertEqual(MachineState.IDLE, m1.state, "Machine 1 has Idle state")

        time += 3.55
        self.env.run(until=time)
        with self.subTest("m1 is idle m2 is  loading"):
            self.assertTrue(m1.occupied,"M1 should be occupied")
            self.assertFalse(m2.occupied,"M2 should NOT be occupied")
            self.assertEqual(MachineState.STOPPED, m2.state, "Machine 2 has Idle state")
            self.assertTrue(m2.quality_control_required, "M2 next part should be measured")

        print(f"{time:.2f} m1 loading m2 loading")
        time += 7
        self.env.run(until=time)

        with self.subTest("M2 is done with tool change m1 hsa produced 5 part"):
            self.assertEqual(MachineState.IDLE, m2.state, "Machine 2 has Idle state")
            self.assertEqual(5, m1.number_of_parts, "M1 has produced 5 part")
        time += 8
        self.env.run(until=time)
        with self.subTest("M2 is in processing first part"):
            self.assertEqual(MachineState.WORKING, m2.state, "Machine 2 has working state")
            self.assertEqual(MachineState.IDLE, m1.state, "Machine 1 has idle state")
            self.assertEqual(1, automation.arm.count, "Automation is busy")

        time += 1
        self.env.run(until=time)
        with self.subTest("M2 and m1 is in processing"):
            self.assertEqual(MachineState.WORKING, m2.state, "Machine 2 has working state")
            self.assertEqual(1, automation.arm.count, "Automation is busy")
        time += 1
        self.env.run(until=time)
        with self.subTest("M2 is stopped during quality check after tool change"):
            self.assertEqual(MachineState.STOPPED, m2.state, "Machine 2 has Stopped state")
            self.assertEqual(6, m1.number_of_parts, "M1 has produced 6 part")
        time += 2
        self.env.run(until=time)

        with self.subTest("M2 is stopped during quality check after tool change"):
            self.assertEqual(MachineState.IDLE, m2.state, "Machine 2 has Idle state after tool change quality control")
            self.assertEqual(6, m1.number_of_parts, "M1 has produced 6 part")
            self.assertEqual(1, m2.scrapped_part, "M2 should have 1 scrapped part")
            self.assertFalse(m2.occupied, "M2 should NOT be occupied")

        time += 5
        self.env.run(until=time)

        self.assertEqual(19, m2.tools.get_shortest_life(), "Machine 2 tools life updated")
        self.assertEqual(MachineState.WORKING, m2.state, "Machine 2 has loaded and keep producing after tool change")
        self.assertEqual(8, m2.total_downtime,"M2 total down time during tool change is 8")
        self.assertEqual(0, m2.operator_waiting_time,"M2 total down time during tool change is 8")
        self.assertEqual(8, m2.operator_work_time,"M2 total down time during tool change is 8")


    ##########################################not yet


    def test_automation_handles_part_flow_in_machines(self):
        m1 = self.create_input_machine()
        m2 = self.create_inline_machine()
        m3 = self.create_inline_machine(name='MC_line2')
        m4 = self.create_output_machine()
        m2.set_input_source(m1)
        m3.set_input_source(m2)
        m4.set_input_source(m3)
        #m4.set_input_source(m2)
        automation = Automation(env=self.env, machines=[m1, m2, m3, m4])

        time = self.env.now + 1.5
        self.env.run(until=time)
        self.assertEqual(1, automation.arm.count, "Automation is busy")

        time += 1000
        self.env.run(until=time)
        #with self.subTest("After m1 is loaded"):
        #    self.assertTrue(m1.occupied, "Machine 1 should be occupied")
        #    self.assertEqual(MachineState.WORKING, m1.state, "Machine 1 should be in working state")
        #time += 70
        #self.env.run(until=time)


        print(time)











if __name__ == '__main__':
    unittest.main()
