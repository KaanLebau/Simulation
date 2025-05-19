import os
import time
import simpy
import datetime

# --- MODULE IMPORTS ---
from components.Automation import Automation
from components.Tool import Tool
from components.Machine import Machine
from components.config import SIMULATION_START, LOG_PATH, RESULTS_PATH,EVENTS_PATH

# --- CONFIGURATION ---
minute = 60
hour = minute * 60
day = hour * 24
SIM_TIME = day *30*6
SIMULATION_START = datetime.datetime(2025, 4, 11, 4, 0)

# --- MONITORING ---
def monitor(env, machines, interval=50):
    with open(LOG_PATH, "w") as f:
        headers = ["simTime", "Timestamp", "machine", "state", "processed_parts", "scrapped_parts", "quality_counter", "tool_warning", "tool_replaced"]
        f.write(",".join(headers) + "\n")
        while True:
            yield env.timeout(interval)
            timestamp = SIMULATION_START + datetime.timedelta(seconds=env.now)
            for m in machines:
                row = [
                    str(env.now),
                    str(timestamp),
                    m.name,
                    str(m.state),
                    str(m.number_of_parts),
                    str(m.scrapped_part),
                    str(m.quality_counter),
                    str(m.tool_warning),
                    str(m.tool_replaced)
                ]
                f.write(",".join(row) + "\n")

# --- SUMMARY REPORT ---
def production_state():
    final_machine = machines[-1]
    throughput_by_hour = [0] * (SIM_TIME // 3600 + 1)

    for t in getattr(final_machine, "final_throughput_timestamps", []):
        hour_index = int(t // 3600)
        throughput_by_hour[hour_index] += 1

    with open(RESULTS_PATH, 'w') as f:
        for m in machines:
            total_time = SIM_TIME
            process = m.processing_time
            upstream = m.upstream_blockage_time
            downstream = m.downstream_blockage_time
            automation = m.automation_blockage_time
            stop = m.total_downtime

            accounted = process + upstream + automation + stop + downstream
            gap = total_time - accounted
            utilization = round((process / total_time) * 100, 2)

            f.write(f"\nMachine name           : {m.name} \n")
            f.write(f"Produced               : {m.number_of_parts}\n")
            f.write(f"Scrapped               : {m.scrapped_part}\n")
            f.write(f"Process time           : {round(process / 60, 2)} min\n")
            f.write(f"Upstream blockage      : {round(upstream / 60, 2)} min\n")
            f.write(f"Downstream blockage    : {round(downstream / 60, 2)} min\n")
            f.write(f"Automation blockage    : {round(automation / 60, 2)} min\n")
            f.write(f"Tool stoppage          : {round(stop / 60, 2)} min\n")
            f.write(f"Untracked (gap) time   : {round(gap / 60, 2)} min\n")
            f.write(f"Utilization            : {utilization} %\n")
            f.write("\n" + "%" * 24)

        f.write("\n" + "%" * 24)
        f.write("Production Line Summary")
        f.write("%" * 24)
        f.write(f"\nFinal Machine         : {final_machine.name}")
        f.write(f"\nHourly Line Throughput: {throughput_by_hour}")
        f.write(f"\nTotal Simulation Time : {SIM_TIME / 60:.2f} min")
        f.write("\n" + "%" * 24)

# --- ENVIRONMENT SETUP ---
env = simpy.Environment()
operator = simpy.Resource(env, capacity=1)

mc1_tools = [Tool(life=100, replacement_duration=120),
             Tool(life=800, replacement_duration=60),
             Tool(life=800, replacement_duration=60),
             Tool(life=1000, replacement_duration=60),
             Tool(life=500, replacement_duration=60),
             Tool(life=1400, replacement_duration=60),
             ]
mc2_tools = [Tool(life=50, replacement_duration=20),
             Tool(life=50, replacement_duration=20),
             Tool(life=50, replacement_duration=20),
             Tool(life=50, replacement_duration=20),
             Tool(life=50, replacement_duration=20),
             Tool(life=50, replacement_duration=20),
             Tool(life=50, replacement_duration=20),
             Tool(life=50, replacement_duration=20),
             Tool(life=50, replacement_duration=20),
             Tool(life=50, replacement_duration=20),
             Tool(life=50, replacement_duration=20),
             Tool(life=50, replacement_duration=20),
             Tool(life=150, replacement_duration=25)

             ]
mc3_tools = [Tool(life=600, replacement_duration=35),
             Tool(life=600, replacement_duration=35),
             Tool(life=600, replacement_duration=35),
             Tool(life=200, replacement_duration=35),
             Tool(life=200, replacement_duration=35),
             Tool(life=800, replacement_duration=35),
             Tool(life=1000, replacement_duration=35),
             Tool(life=3000, replacement_duration=35),
             Tool(life=3000, replacement_duration=35),
             Tool(life=3500, replacement_duration=35),
             Tool(life=7000, replacement_duration=35),
             Tool(life=9000, replacement_duration=35),
             ]
mc4_tools = [Tool(life=300, replacement_duration=35),
             Tool(life=300, replacement_duration=35),
             Tool(life=200, replacement_duration=755),
             Tool(life=100, replacement_duration=55),
             ]
mc5_tools = [Tool(life=400, replacement_duration=95)]
mc6_tools = [Tool(life=300, replacement_duration=45),
             Tool(life=250, replacement_duration=45),
             Tool(life=1000, replacement_duration=55),
             Tool(life=1000, replacement_duration=55),
             Tool(life=1000, replacement_duration=55)
             ]

# machine data

mc1_data = {"name": "MC1", "type": 'input', "operator": operator, "ct": 124, "tools": mc1_tools, "tool_threshold": 20, "quality_interval": 1, "quality_duration": 400, "output_size": 9}
mc2_data = {"name": "MC2", "type": 'inline', "operator": operator, "ct": 170, "tools": mc2_tools, "tool_threshold": 20,"quality_interval": 20, "quality_duration": 500, "output_size": 9 }
mc3_data = {"name": "MC3", "type": 'inline', "operator": operator, "ct": 164, "tools": mc3_tools, "tool_threshold": 20,"quality_interval": 30, "quality_duration": 500, "output_size": 6 }
mc4_data = {"name": "MC4", "type": 'inline', "operator": operator, "ct": 161, "tools": mc4_tools, "tool_threshold": 20,"quality_interval": 30, "quality_duration": 500, "output_size": 6 }
mc5_data = {"name": "MC5", "type": 'inline', "operator": operator, "ct": 154, "tools": mc5_tools, "tool_threshold": 20,"quality_interval": 30, "quality_duration": 500, "output_size": 6 }
mc6_data = {"name": "MC6", "type": 'output', "operator": operator, "ct": 166, "tools": mc6_tools, "tool_threshold": 10,"quality_interval": 30, "quality_duration": 500, "output_size": 10}
# mc2_data = {"name":"MC2", "type":'inline', "ct":10, "tool_life":20,"output_size":10, "tool_replacement":600, "loading_time":LOODING, "prio":0.7}

# Set up environment and machine(s)

machine1 = Machine(env, mc1_data)
machine2 = Machine(env, mc2_data)
machine3 = Machine(env, mc3_data)
machine4 = Machine(env, mc4_data)
machine5 = Machine(env, mc5_data)
machine6 = Machine(env, mc6_data)

machine2.set_input_source(machine1)
machine3.set_input_source(machine2)
machine4.set_input_source(machine3)
machine5.set_input_source(machine4)
machine6.set_input_source(machine5)

machines = [machine1, machine2, machine3, machine4, machine5, machine6]

automation = Automation(env, machines)

# --- INIT CSV LOG ---
with open(EVENTS_PATH, "w") as f:
    f.write("Timestamp,Machine,End,Type\n")

# --- MONITOR PROCESS ---
env.process(monitor(env, machines, interval=50))

# --- SIMULATION ---
start = time.time()
env.run(until=SIM_TIME)
duration = time.time() - start

print("\n" + "%" * 24)
print("Machine Production Summary")
print(f"Sim run time {duration:.2f} sec")
print("%" * 24)

# --- RESULT OUTPUT ---
production_state()
