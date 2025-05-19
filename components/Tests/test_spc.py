import unittest
import simpy
from Spc import Spc

class TestSpc(unittest.TestCase):
    def setUp(self):
        self.env = simpy.Environment()
        self.spc = Spc(env=self.env, duration=5)

    def test_initial_state(self):
       self.assertFalse(self.spc.occupied, "Initially Spc is empty failed")
       self.assertFalse(self.spc.pending, "Initially Spc is pending failed")
       self.assertFalse(self.spc.is_ready_to_unload, "Initially Spc is ready to unload failed")

    def test_load_starts_hold_correctly(self):
        operator = simpy.Resource(self.env, capacity=1)

        def load_process():
            yield from self.spc.load(machine="MC1", operator=operator)

        self.env.process(load_process())
        self.env.run(until=0.1)

        self.assertFalse(self.spc.occupied, "SPC should not be occupied right after operator is acquired")
        self.assertTrue(self.spc.pending, "SPC should be pending after inspection starts")
        self.assertFalse(self.spc.is_ready_to_unload, "SPC should not be ready to unload yet")

    def test_hold_process_completion(self):
        operator = simpy.Resource(self.env, capacity=1)

        def load_process():
            yield from self.spc.load(machine="MC1", operator=operator)

        self.env.process(load_process())
        self.env.run(until=self.spc.duration + 0.1)

        self.assertTrue(self.spc.occupied, "SPC should be occupied after hold ends")
        self.assertFalse(self.spc.pending, "SPC should not be pending after duration")
        self.assertTrue(self.spc.is_ready_to_unload, "SPC should be ready to unload after hold")

    def test_unload_resets_state(self):
        operator = simpy.Resource(self.env, capacity=1)

        def load_process():
            yield from self.spc.load(machine="MC1", operator=operator)

        self.env.process(load_process())
        self.env.run(until=self.spc.duration + 0.1)

        self.spc.unload()

        self.assertFalse(self.spc.occupied, "SPC should not be occupied after unloading")
        self.assertFalse(self.spc.is_ready_to_unload, "SPC should not be ready after unloading")



    def test_spc_operator_not_available(self):
        def dummy_task(env, operator):
            with operator.request() as req:
                yield req
                yield env.timeout(1000)
        operator = simpy.Resource(self.env, capacity=1)

        # Dummy task occupies the operator
        self.env.process(dummy_task(self.env, operator))
        self.env.step()

        # Now SPC tries to load part
        def load_process():
            yield from self.spc.load(machine="MC1", operator=operator)

        self.env.process(load_process())

        # Step a little bit in simulation time
        self.env.step()

        # SPC should be occupied but still pending because operator is busy
        self.assertTrue(self.spc.occupied, "SPC should be occupied while waiting for operator")
        self.assertTrue(self.spc.pending, "SPC should still be pending while waiting for operator")
        self.assertFalse(self.spc.is_ready_to_unload, "SPC should not be ready to unload immediately")
        self.assertFalse(self.spc.is_empty(), "SPC should not be empty immediately")
        # Free the operator by running long enough for dummy_task to timeout
        self.env.run(until=1001)

        # Run enough time for spc measurement
        self.env.run(until=self.env.now + self.spc.duration + 1)

        self.assertFalse(self.spc.pending, "SPC should not be pending after inspection")
        self.assertTrue(self.spc.is_ready_to_unload, "SPC should be ready to unload after inspection")

        def test_spc_equality_true(self):
            env1 = simpy.Environment()
            env2 = simpy.Environment()
            spc1 = Spc(env=env1, duration=5)
            spc2 = Spc(env=env2, duration=5)

            self.assertEqual(spc1, spc2, "Two identical SPC instances should be equal")

        def test_spc_equality_false(self):
            env1 = simpy.Environment()
            env2 = simpy.Environment()
            spc1 = Spc(env=env1, duration=5)
            spc2 = Spc(env=env2, duration=10)  # Different duration

            self.assertNotEqual(spc1, spc2, "SPC instances with different durations should not be equal")

            spc3 = Spc(env=env2, duration=5)
            spc3.occupied = True
            self.assertNotEqual(spc1, spc3, "SPC instances with different states should not be equal")


if __name__ == '__main__':
    unittest.main()
