import simpy
from MachineStates import MachineState


class Automation:
    def __init__(self, env, machines):

        self.machines = machines
        self.env = env
        self.arm = simpy.Resource(env, capacity=1)
        self.action = env.process(self.run())
        self.part_changeover = 4.5


    def _has_input_source(self, machine):
        if machine.get_output_source() is None:
            return False
        else:
            return True

    def _get_input_part(self, machine):
        machine.get_output_part()
    def downstream_down_time_tracking(self, machine, now):
        if machine.downstream_start_time is not None:
            machine.downstream_time += now - machine.downstream_start_time
            machine.downstream_start_time = now
        machine.downstream_start_time = now

    def run(self):
        while True:
            any_ready = False
            for m in self.machines:
                has_part = m.occupied
                source = m.input_source
                ##print(f"35 - Automation \t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {m.name} \033[0m ")
                with self.arm.request() as req:
                    yield req
                    if (m.input_source and self._has_input_source(source) and not m.state == MachineState.STOPPED) or (m.type =="input" and  m.state == MachineState.IDLE):
                        #print(f"38 - Automation \t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {m.name} \033[0m \t\t is \033[92m READY \033[0m ")
                        if not has_part:
                            if not m.type == "input":
                                self._get_input_part(source)
                            #print(f"43 - Automation \t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {m.name} \033[0m \t\t Loading \033[92m START \033[0m ")
                            yield self.env.timeout(self.part_changeover)
                            #print(f"43 - Automation \t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {m.name} \033[0m \t\t Loading \033[92m END \033[0m ")
                            m.load_machine()
                            m.start_signal.succeed()
                        else:
                            if m.ready_to_unload:
                                if m.quality_check_part():
                                    if not m.spc.occupied:
                                        if not m.type =="input":
                                            self._get_input_part(source) #has load part
                                        #print(f"56 - Automation \t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {m.name} \033[0m \t\t Loading \033[92m START \033[0m ")
                                        yield self.env.timeout(self.part_changeover)
                                        #print(f"58 - Automation \t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {m.name} \033[0m \t\t Loading \033[92m END \033[0m ")
                                        m.unload_machine() # removed spc part
                                        if not m.state == MachineState.STOPPED:
                                            m.load_machine()
                                        m.start_signal.succeed()
                                        self.env.process(m.load_spc())
                                        continue
                                    else: # spc is occupied machine stops
                                        self.downstream_down_time_tracking(m, self.env.now)
                                else: # part route to buffer
                                    if m.buffer_ready_to_load():
                                        if not m.type == "input":
                                            self._get_input_part(source)
                                        #print(f"72 - Automation \t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {m.name} \033[0m \t\t Loading \033[92m START \033[0m ")
                                        yield self.env.timeout(self.part_changeover)
                                        #print(f"74 - Automation \t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {m.name} \033[0m \t\t Loading \033[92m END \033[0m ")
                                        m.unload_machine()
                                        if not m.state == MachineState.STOPPED:
                                            m.load_machine()
                                        m.start_signal.succeed()
                                        m.load_buffer()
                                    else:
                                        self.downstream_down_time_tracking(m, self.env.now)

                            else:
                                continue

            yield self.env.timeout(0.01 if any_ready else 0.1)
