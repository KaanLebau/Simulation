import datetime
from config import SIMULATION_START, EVENTS_PATH

class Spc:
    def __init__(self, env, duration):
        """
                Description:
                    Initializes the SPC station, which handles statistical inspection of parts.

                Input:
                    env (simpy.Environment): The simulation environment.
                    duration (int): Time required to inspect one part.

                Output:
                    Initializes the SPC state including flags and event placeholders.

                Example of use:
                    spc = Spc(env, duration=300)
        """
        self.env = env
        self.duration = duration
        self.occupied = False
        self.pending = False
        self.is_ready_to_unload = False
        self.done_event = None
        self.released = env.event()
        self.operator_waiting_time =0
        self.operator_work_time = 0
        self.machine = None

    def is_empty(self):
        """
                Description:
                    Checks whether the SPC station is currently unoccupied.

                Input:
                    None

                Output:
                    bool: True if unoccupied, False otherwise.

                Example of use:
                    if spc.is_empty():
                        ...
        """
        return not self.occupied

    def load(self, machine, operator):
        """
                Description:
                    Loads a part into the SPC for inspection. If the operator is available,
                    logs the event and starts the inspection process.

                Input:
                    machine (str): Machine name sending the part.
                    operator (simpy.Resource): Operator controlling the SPC.

                Output:
                    Yields operator request and starts a timed inspection.
                    Logs start and end time of inspection to the event file.

                Example of use:
                    yield env.process(spc.load("MC1", operator))
        """
        #print(f"65 - Spc \t\t\t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {machine}\033[0m  \t \033[93m Spc is LOADED \033[0m ")
        real_time = SIMULATION_START + datetime.timedelta(seconds=self.env.now)
        self.machine = machine
        self.occupied = True
        self.pending = True
        self.is_ready_to_unload = False
        wait = self.env.now
        with operator.request() as req:
            yield req
            #print(f"74 - SPC \t\t\t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {self.machine}\033[0m  \t\t Operator \033[92m available \033[0m ")
            self.operator_waiting_time = self.env.now - wait
            end = real_time + datetime.timedelta(seconds=self.duration)
            with open(EVENTS_PATH, 'a') as log:
                log.write(
                    f"{real_time.strftime('%Y-%m-%d %H:%M:%S')},{machine},{end.strftime('%Y-%m-%d %H:%M:%S')}, qualityCheck \n")
            self.occupied = False
            #self.done_event = self.env.process(self._hold_part(machine))
            self.env.process(self._hold_part())

    def _hold_part(self):
        """
            Description:
                Internal method to simulate the inspection duration.

            Input:
                None

            Output:
                Yields a timeout equal to the inspection duration.
                Updates internal flags after timeout.

            Example of use:
                Internal only. Automatically invoked by `load()`.
        """
        #print(f"99 - SPC \t\t\t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {self.machine}\033[0m  \t\t Hold part \033[92m START \033[0m ")
        start = self.env.now
        yield self.env.timeout(self.duration)
        self.operator_work_time = self.env.now - start
        self.pending = False
        self.is_ready_to_unload = True
        self.occupied = True
        #print(f"106 - SPC \t\t\t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {self.machine}\033[0m  \t\t Hold part \033[91m END \033[0m ")


    def unload(self):
        """
                Description:
                    Unloads the inspected part from the SPC.

                Input:
                    None

                Output:
                    Updates internal flags to reflect SPC being empty and ready for next load.

                Example of use:
                    spc.unload()
        """
        self.is_ready_to_unload = False
        self.occupied = False
        #print(f"125 - SPC \t\t\t time: \033[93m {self.env.now:.2f} \033[0m \t \033[96m {self.machine}\033[0m  \t\t \033[93m UNLOADED \033[0m ")

    def __eq__(self, other):
        if not isinstance(other, Spc):
            return False
        return (
                self.duration == other.duration and
                self.occupied == other.occupied and
                self.pending == other.pending and
                self.is_ready_to_unload == other.is_ready_to_unload
        )

    def __str__(self):
        return (f"SPC Status @ {self.env.now:.2f}:\n"
                f"  Duration: {self.duration}\n"
                f"  Occupied: {self.occupied}\n"
                f"  Pending: {self.pending}\n"
                f"  Ready to Unload: {self.is_ready_to_unload}\n"
                f"  Operator Waiting Time: {self.operator_waiting_time}\n"
                f"  Operator Work Time: {self.operator_work_time}")

