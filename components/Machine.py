from ToolManagement import ToolManagement
from MachineStates import MachineState
from Spc import Spc
import datetime
from config import SIMULATION_START, EVENTS_PATH

class Machine:
    # --- Machine Lifecycle Control
    def __init__(self,env, machine_data):
        # --- Core Configuration __
        self.final_throughput_timestamps = None
        self.env = env
        self.name = self.safe_get(machine_data, 'name', '')
        self.type = self.safe_get(machine_data, 'type', 'inline')
        self.ct = self.safe_get(machine_data, 'ct', 0)
        self.input_source = self.safe_get(machine_data, 'input_source', None)
        self.operator = self.safe_get(machine_data, 'operator', None)

        # --- Production State ---
        self.state = MachineState.IDLE
        self.occupied = False
        self.part = ""
        self.ready_to_unload = False
        self.start_signal = env.event()  # triggered by automation
        self.action = env.process(self.run())

        # --- Performance Tracking ---
        self.number_of_parts = 0
        self.scrapped_part = 0
        self.total_uptime = 0
        self.total_downtime = 0
        self.operator_waiting_time = 0
        self.operator_work_time= 0
        self.operator_spc_waiting_time = 0
        self.operator_spc_work_time = 0
        self.idle_start_time = self.env.now
        self.downstream_start_time = None
        self.downstream_time = 0


        self.total_idle_time = 0



        # --- Tooling Management ---
        self.tools = ToolManagement(self.safe_get(machine_data, 'tools', []))
        self.threshold = self.safe_get(machine_data, 'threshold', 10)
        self.tool_warning = False
        self.tool_replaced = False

        # --- Buffer Management ---
        self.output_buffer = 0
        self.buffer_utilization = 0
        self.output_size = self.safe_get(machine_data, 'output_size', 1)

        # --- Quality Configuration __
        self.quality_interval = self.safe_get(machine_data, 'quality_interval', 20)
        self.quality_counter = self.safe_get(machine_data, 'quality_counter', 0)
        self.quality_control_required = False
        self.quality_duration = self.safe_get(machine_data, 'quality_duration', 100)
        self.spc = Spc(self.env, self.quality_duration)

        # --- Output part ---
        self.output_source = None

    def set_input_source(self, source):
            self.input_source = source
    def run(self):
            while True:

                yield self.start_signal
                self.start_signal = self.env.event()

                if self.state == MachineState.STOPPED:
                    wait_start = self.env.now
                    with self.operator.request() as req:
                        yield req
                        self.operator_waiting_time += self.env.now - wait_start
                        real_time = SIMULATION_START + datetime.timedelta(seconds=self.env.now)
                        replacement_duration = self.replace_tooling()
                        self.logging(real_time, replacement_duration)
                        work_start = self.env.now
                        #print(f"82 - Machine \t\t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {self.name}\033[0m \t\t state \033[91m {self.state} \033[0m \t\t before Tool change ")
                        yield self.env.timeout(replacement_duration)
                        #print(f"84 - Machine \t\t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {self.name}\033[0m \t\t state \033[91m {self.state} \033[0m \t\t after Tool change ")
                        self.operator_work_time += self.env.now - work_start
                        self.state = MachineState.IDLE
                        #print(f"85 - Machine \t\t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {self.name}\033[0m \t\t state \033[91m {self.state} \033[0m ")
                        self.idle_start_time = self.env.now
                        self.ready_to_unload = True
                        self.tool_replaced = True
                        continue

                if self.idle_start_time is not None:
                    self.total_idle_time += self.env.now - self.idle_start_time
                    self.idle_start_time = None
                if self.state != MachineState.WARNING:
                    self.state = MachineState.WORKING
                #print(f"93 - Machine \t\t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {self.name}\033[0m \t\t state \033[91m {self.state} \033[0m ")
                yield self.env.timeout(self.ct)
                self.process_part()
                #print(f"96 - Machine \t\t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {self.name}\033[0m \t\t part: \033[94m {self.number_of_parts} \033[0m")

                if self.quality_control_required:
                    self.state = MachineState.STOPPED
                    #print(f"104 - Machine \t\t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {self.name}\033[0m \t\t state \033[91m {self.state} \033[0m before quality control after tool change")
                    self.quality_control_required = False
                    wait_start = self.env.now
                    with self.operator.request() as req:
                        yield req
                        self.operator_waiting_time += self.env.now - wait_start
                        yield self.env.timeout(self.quality_duration)
                        self.scrapped_part += 1
                        self.total_downtime += self.quality_duration
                        self.operator_work_time += self.quality_duration
                        self.occupied = False
                        self.quality_counter_reset()
                        print(f"118 - Machine \t\t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {self.name}\033[0m  \t\t  quality_counter: \033[94m {self.quality_counter} \033[0m \t Quality conunter resets  \033[92m SUCCESSFULLY \033[0m outside of reset function")

                        #print(f"110 - Machine \t\t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {self.name}\033[0m \t\t state \033[91m {self.state} \033[0m after quality control after tool change")
                self.state = MachineState.IDLE
                #print(f"111 - Machine \t\t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {self.name}\033[0m \t\t state \033[91m {self.state} \033[0m ")
                self.idle_start_time = self.env.now

                self.ready_to_unload = True

    # --- Readiness controls ---
    def buffer_ready_to_load(self):
        result = self.output_buffer < self.output_size
        return result
    def is_spc_empty(self):
        return self.spc.is_empty()
    def spc_ready_to_unload(self):
        return self.spc.is_ready_to_unload
    def is_ready(self):
        if not self.occupied:
            return True
        else:
            part_processed = self.ready_to_unload
            spc_empty = self.spc.is_empty()
            buffer_ready = self.output_buffer < self.output_size
            if self.quality_control_required:
                return part_processed and spc_empty
            else:
                return part_processed and buffer_ready


    # --- unloading functionality--
    def unload_machine(self):
        #print(f"135 - Machine \t\t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {self.name}\033[0m  \t\t \033[96m Machine is UNLOADED \033[0m \t  part: \033[94m {self.number_of_parts + 1} \033[0m \t ")
        self.occupied = False
        self.ready_to_unload = False
        self.part = "raw"
        self.tool_check()
    def unload_buffer(self):
        if self.output_buffer == 0:
            raise ValueError('Buffer is empty')
        #print(f"143 - Machine \t\t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {self.name}\033[0m  \t\t \033[41;96m Buffer is UNLOADED \033[0m \t  part: \033[93m {self.number_of_parts + 1} \033[0m \t current:\033[94m {self.output_buffer}/{self.output_size} \033[0m")
        self.output_buffer -= 1
    def unload_spc(self):
        #print(f"146 - Machine \t\t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {self.name}\033[0m  \t\t \033[47;96m Spc is UNLOADED \033[0m \t  part: \033[94m {self.number_of_parts + 1} \033[0m \t ")
        self.spc.unload()

    # --- loading functionality
    def load_machine(self):
        if self.occupied:
            raise Exception('Machine is occupied')
        self.occupied = True
        self.part = "processing"
        self.ready_to_unload = False
        #print(f"156 - Machine \t\t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {self.name}\033[0m  \t\t \033[93m Machine is LOADED \033[0m \t  part: \033[94m {self.number_of_parts + 1} \033[0m \t ")

        #if not self.start_signal.trigger:
        #    self.start_signal.succeed()
    def load_buffer(self):
        if self.output_buffer == self.output_size:
            raise ValueError('Buffer is full')
        if not self.type == 'output':
            self.output_buffer += 1
            #print(f"178 - Machine \t\t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {self.name}\033[0m  \t\t \033[93m Buffer is LOADED \033[0m \t  part: \033[94m {self.number_of_parts + 1} \033[0m \t current:\033[94m {self.output_buffer}/{self.output_size} \033[0m")
        #print(f"179 - Machine \t\t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {self.name}\033[0m  \t\t \033[93m Buffer is LOADED \033[0m \t  part: \033[94m {self.number_of_parts + 1} \033[0m \t current:\033[94m {self.output_buffer}/{self.output_size} \033[0m output buffer is full")
    def load_spc(self):
        spc_process = self.spc.load(machine=self.name, operator=self.operator)
        self.operator_spc_work_time += self.spc.operator_work_time
        self.operator_spc_waiting_time += self.spc.operator_waiting_time
        #print(f"167 - Machine \t\t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {self.name}\033[0m  \t\t \033[93m Spc is LOADED \033[0m \t\t  part: \033[94m {self.number_of_parts + 1} \033[0m \t ")
        return spc_process

    # --- Tooling functionality ---
    def tool_check(self):
        if self.tools.get_shortest_life() == 0:
            self.state = MachineState.STOPPED
            #print(f"182 - Machine \t\t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {self.name}\033[0m \t\t state \033[91m {self.state} \033[0m ")
        elif self.tools.get_shortest_life() <= self.threshold:
            self.state = MachineState.WARNING
            self.tool_warning = True
            #print(f"186 - Machine \t\t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {self.name}\033[0m \t\t state \033[91m {self.state} \033[0m ")
    def replace_tooling(self):
        duration = self.tools.tool_replacement()
        self.quality_control_required = True
        self.total_downtime += duration
        return duration
    def update_tooling(self):
        self.tools.tool_update()

    # --\t \t - Machine logging ---
    def last_machine_operations(self):
        ##TODO not tested
        if self.type == 'output':
            if not hasattr(self, "final_throughput_timestamps"):
                self.final_throughput_timestamps = []
            self.final_throughput_timestamps.append(self.env.now)
    def logging(self, real_time, replacement_duration):
        end = real_time + datetime.timedelta(seconds=replacement_duration)
        with open(EVENTS_PATH, 'a') as log:
            log.write(
                f"{real_time.strftime('%Y-%m-%d %H:%M:%S')},{self.name},{end.strftime('%Y-%m-%d %H:%M:%S')}, tool change \n")

    # --- Processed part to next machine
    def get_output_part(self):
        if self.output_source == 'Spc':
            self.unload_spc()
        else:
           self.unload_buffer()
    def get_output_source(self):
        if  self.spc_ready_to_unload():
            self.output_source =  'Spc'
        elif self.output_buffer > 0:
            self.output_source =  "Buffer"
        else:
            self.output_source = None
        return self.output_source


    # --- Quality related functionality ---
    def quality_check_part(self):
        return self.quality_counter == self.quality_interval
    def quality_counter_reset(self):
        print(f"237 - Machine \t\t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {self.name}\033[0m  \t\t  quality_counter: \033[94m {self.quality_counter} \033[0m \t Quality conunter before resets")
        self.quality_counter = 0
        print(f"239 - Machine \t\t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {self.name}\033[0m  \t\t  quality_counter: \033[94m {self.quality_counter} \033[0m \t Quality conunter resets  \033[92m SUCCESSFULLY \033[0m")



    # --- Class Utilities ---
    @staticmethod
    def safe_get(machine_data, key, default):
        value = machine_data.get(key, default)
        return default if value is None else value
    def process_part(self):
        self.part = "processed"
        self.quality_counter += 1
        self.number_of_parts += 1
        self.total_uptime += self.ct
        self.update_tooling()
        #print(f"256 - Machine \t\t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {self.name}\033[0m  \t\t part \033[94m {self.number_of_parts}\033[0m  \t quality counter \033[94m {self.quality_counter}\033[0m \t buffer: \033[94m {self.output_buffer}/{self.output_size} \033[0m")
    def trigger_if_ready(self):
        if self.occupied and not self.part == "processing":
            pass
    def update_buffer_utilization(self):
        if self.buffer_utilization < self.output_buffer:
            self.buffer_utilization = self.output_buffer
    def __repr__(self):
        return (
            f"Machine(name='{self.name}', type='{self.type}', ct={self.ct}, "
            f"output_size={self.output_size}, state='\033[91m {self.state} \033[0m')"
        )
    def __str__(self):
        return (
            f"Machine(name='{self.name}', type='{self.type}', state='\033[91m {self.state} \033[0m')\n"
            f"  CT: {self.ct}, Output Size: {self.output_size}, Output Buffer: {self.output_buffer}, "
            f"Buffer Utilization: {self.buffer_utilization}\n"
            f"  Tools Warning: {self.tool_warning}, Tools Replaced: {self.quality_control_required}\n"
            f"  Quality Interval: {self.quality_interval}, Quality Counter: {self.quality_counter}, "
            f"Quality Duration: {self.quality_duration}\n"
            f"  SPC: occupied={self.spc.occupied}, pending={self.spc.pending}, "
            f"ready_to_unload={self.spc.is_ready_to_unload}"
        )
    def __eq__(self, other):
        if not isinstance(other, Machine):
            return False
        return self.name == other.name

    def print_processing_data(self):
        print(f"--- Processing Data for {self.name} ---")
        print(f"Type: {self.type}")
        print(f"State: {self.state.value}")
        print(f"CT: {self.ct}")
        print(f"Tools Warning: {self.tool_warning}")
        print(f"Tool Life (Shortest): {self.tools.get_shortest_life()}")
        print(f"Output Buffer: {self.output_buffer}/{self.output_size}")
        print(f"Parts Processed: {self.number_of_parts}")
        print(f"Scrapped Parts: {self.scrapped_part}")
        print(f"Total Uptime: {self.total_uptime}")
        print(f"Total Downtime (Tool Changes): {self.total_downtime}")
        print(f"Quality Interval: {self.quality_interval}")
        print(f"Quality Counter: {self.quality_counter}")
        print(f"SPC - Occupied: {self.spc.occupied}, Ready to Unload: {self.spc.is_ready_to_unload}")
        print(f"Operator Work Time: {self.operator_work_time}")
        print(f"Operator Waiting Time: {self.operator_waiting_time}")
        print(f"Operator SPC Work Time: {self.operator_spc_work_time}")
        print(f"Operator SPC Waiting Time: {self.operator_spc_waiting_time}")
        print(f"Total Idle Time: {self.total_idle_time}")
        print("--------------------------------------")


    # --- Questionable functionality need to check

    """"
    def upstream_check(self):
        return self.input_source is not None and self.input_source.output_buffer <= 0

   

    def blockage(self):
        if self.type == 'input':
            return not self.downstream_check()
        elif self.type == 'inline':
            return not self.downstream_check() or self.upstream_check()
        else:
            return self.upstream_check()
    """






