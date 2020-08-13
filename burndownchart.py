#!/usr/bin/env python3

import matplotlib.pyplot as plt
import numpy as np
import sys
import argparse

"""
sys.argv[0] : scriptname
sys.argv[1] : filename
sys.argv[2] : number of graphs to plot (2 or 3)
sys.argv[3] : first day of sprint (mo, di, mi, do, fr, sa, so)
sys.argv[4] : length of sprint in days
"""

parser = argparse.ArgumentParser(description= "Burndownchart that optionally shows how much time actually went into the tasks of the sprint")

parser.add_argument("data", help="Data file with issue number, planned time, day of completion, and - optionally - actually used time")
parser.add_argument("graphs", type=int, help="Number of graphs to plot: either two (ideal and actual) or three (actual time)")
parser.add_argument("firstdayofsprint", help="either mo, di, mi, do, fr, sa, or so")
parser.add_argument("duration", help="Duration of sprint in days", type=int)
args = parser.parse_args()


if len(sys.argv) < 2:
    print("Usage:\n\tpython3 <scriptname> <datafile> <graphs> <start> <duration>\n")
    print("\te.g.\t python3 burndownchart3.py Sprint4 3 fr 14\n")
if len(sys.argv) < 4:
    sys.argv.extend(["2", "mo", "7"])

def sprintweek(day):
    week = ["mo", "di", "mi", "do", "fr", "sa", "so"] 
    start = week.index(day)
    tail = week[:start]
    sprintweek = week[start:]
    sprintweek.extend(tail)
    return sprintweek

def adjust_sprintlength(duration, sprint, sprintweek):
    if duration <= 7:
        sprint= sprintweek[:duration]
    elif duration > 7:
        length = len(sprint)
        diff = duration - length
        for i in range(diff):
            if len(sprint) < 7:
                sprint.append(sprintweek[(length%7 + i%7)%7])
            else:
                sprint.append(sprintweek[(length%7 + i%7)%7] + str((length + i)//7 + 1))
    return sprint

def map_days(sprint, duration):
    daynum= [i+1 for i in range(duration)]
    sprintdays = dict(zip(sprint, daynum))
    return sprintdays
    
#sprintweek = sprintweek(sys.argv[3])
sprintweek = sprintweek(args.firstdayofsprint)
#duration = int(sys.argv[4])
duration = int(args.duration)
sprint = adjust_sprintlength(duration, [], sprintweek)
sprintdays = map_days(sprint, duration)

burnt_minutes = [0]*(duration+1)
burnt_actualminutes = [0]*(duration+1)
sum_minutes = 0
issues = []
day_in_minutes = 480
actualminutes = 0
buffer_minutes = 0

#with open (sys.argv[1]) as f:
with open (args.data) as f:
    firstline = f.readline().split()
    columns = len(firstline)
    f.seek(0)
    for line in f:
        if columns == 4:
            issue, minutes_str, day, actualminutes_str = line.strip().split()  
        else:
            issue, minutes_str, day = line.strip().split()  
        minutes = int(minutes_str)
        sum_minutes += minutes
        issues.append(issue)
        if issue.startswith("p"):
            buffer_minutes += minutes
        if day in sprintdays:
            burnt_minutes[sprintdays[day]] += minutes
        elif day.startswith(("mo","di","mi","do","fr","sa","so")) and (duration<7 or day[2:].isdigit()):
            alpha = day[:2]
            stop = sprintweek.index(alpha)
            if duration < 7 and len(day) == 2:
                extend_by = stop+1 - len(sprint)
            else:
                num = int(day[2:])
                extend_by = stop+1 - len(sprint) + 7*(num-1)
            duration += extend_by
            sprint = adjust_sprintlength(duration, sprint, sprintweek)
            burnt_minutes.extend([0]*extend_by)
            burnt_actualminutes.extend([0]*extend_by)
            sprintdays = map_days(sprint, duration)
            burnt_minutes[sprintdays[day]] += minutes

        if columns == 3:
            continue
        if actualminutes_str.isdigit():
            actualminutes = int(actualminutes_str)
            burnt_actualminutes[sprintdays[day]] += actualminutes

print("sprint = ", sprint)
unique_issues = list(set(issues))
print("number of issues = ", len(issues), "number of unique issues = ", len(unique_issues))
if len(issues) != len(unique_issues):
    print("Duplicate issues in issue file!")
print("average minutes/task = ", sum_minutes/len(issues))
print("workload in days = ", sum_minutes/day_in_minutes)
print("workload in hours = ", sum_minutes/60)
print("buffer in minutes = ", buffer_minutes)
buffer_days = buffer_minutes/day_in_minutes
print("buffer in days = ", buffer_days)

def burn_minutes(workload_week, burndown_week):
    burnt = 0
    for i in range(len(workload_week)):
        burnt += burndown_week[i]
        workload_week[i] -= burnt
    return workload_week

def minutes2days(burnt_week):
    return [item/day_in_minutes for item in burnt_week]

workload_week = [sum_minutes]* (duration+1)
burntdown = burn_minutes(workload_week, burnt_minutes)
burnt_days = minutes2days(burntdown)
burnt_days_arr = np.array(burnt_days)

tasks_in_days = sum_minutes/day_in_minutes

x = np.arange(0,duration+1,1)
y = np.arange(tasks_in_days)
plt.plot([0,duration], [tasks_in_days, buffer_days], label = 'Ideal Tasks Remaining')
plt.axis('equal')
plt.xticks(x)
if burnt_minutes != [0]*(duration+1):
    plt.plot(x, burnt_days_arr, label = "Actual Tasks Remaining", marker='o')

if sys.argv[2] == "3":
    workload_week = [sum_minutes]*(duration+1)
    burntdown_actual = burn_minutes(workload_week, burnt_actualminutes)
    if burnt_actualminutes != [0]*(duration+1):
        burnt_days_actual = minutes2days(burntdown_actual)
        burnt_days_actual_arr = np.array(burnt_days_actual)
        plt.plot(x, burnt_days_actual_arr, label = "Actual Time Burnt")
        if burntdown_actual[-1] >= 0:
            ax = plt.subplot(1,1,1)
            ax.set_ylim(ymin=0)

if buffer_minutes != 0:
    plt.axhline(y=buffer_days, color='gray', label = "Buffer Time Issues")
    plt.axhline(y=0, color='black', linewidth=0.5)

ax = plt.subplot(1,1,1)
if sys.argv[2] == "2":
    ax.set_ylim(ymin=0)
ax.set_xlim(xmin=0)
sprint.insert(0,"0")
for i in range(duration+1):
    sprint[i] = str(i)+ "\n" + sprint[i].capitalize().rstrip('01234')
ax.set_xticklabels(sprint)
ax.spines['left'].set_position('zero')
ax.spines['bottom'].set_position('zero')
ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)

ax.spines['left'].set_visible(True)

plt.ylabel('Tasks (in days)\n' + str(np.round(sum_minutes/60,2)) + 'h = '+ str(np.round(sum_minutes/day_in_minutes, 2)) + ' days')
filename = sys.argv[1].partition(".")
plt.title('Burndown Chart ' + filename[0])
plt.legend()
plt.tight_layout()
plt.show()
