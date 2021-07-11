# Python script to parse a flight data file (csv) and extract useful info from it

import os
import sys
import csv
import matplotlib.pyplot as plt
import math
from shutil import copyfile
from termcolor import colored
import time
import subprocess

FLIGHT_DATA_FILEPATH = os.environ["HOMEPATH"]

def main():
    os.system('color')
    print(colored("\n~~~~~ Flight Data Processor - Josh Bird ~~~~~\n", 'red'))
    
    sea_level_pressure_manual = getSeaLevelPressure()
    if (sea_level_pressure_manual != None):
        outside_temp_manual = getOutsideTemp()
    else:
        outside_temp_manual = None
    
    # Create a direcory for this script to use
    dir = os.path.join(os.environ["HOMEPATH"], "Desktop")
    dir = os.path.join(dir, "Flight_Data")
    if (not os.path.exists(dir)):
        os.makedirs(dir)
    
    poss_flightset_name = str(input("\nName of flight set? "))
    if (poss_flightset_name == None):
        poss_flightset_name = "no_name"
    else:
        poss_flightset_name = "".join(x for x in poss_flightset_name if x.isalnum())
    
    #Create a directory for this flightset
    i = 0
    while (True):
        if (i == 0):
            dir_name = poss_flightset_name
        else:
            dir_name = poss_flightset_name + "_" + str(i)
            
        poss_flightset_dir = os.path.join(dir, dir_name)
        if os.path.exists(poss_flightset_dir):
            i += 1
        else:
            os.makedirs(poss_flightset_dir)
            flightset_dir = poss_flightset_dir
            break
    
    print(colored("Saving files to {}".format(flightset_dir), 'green'))
    
    print("\nSearching for flight data file...")
    removable_disks = getRemovableDisks()
    filepath = None
    for disk in removable_disks:
        filepath = find('fd.csv', (disk + ':'))
        if (filepath != None):
            break
    
    if (filepath == None):
        filepath = find('fd.csv', FLIGHT_DATA_FILEPATH)
    
    if (filepath == None):
        print(colored("No flight data file found on your PC HOMEPATH.", 'red'))
        print(colored("File should be named 'fd.csv', and can be placed in Desktop, or Documents etc...", 'red'))
        sys.exit()
    else:
        print(colored("Flight data found at {}\n".format(filepath), 'green'))
        copyfile(filepath, os.path.join(flightset_dir, "original_data.csv"))
        
        with open(filepath) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            
            flight_data = []
            num_flights = 0
            
            for row in csv_reader:
                row_array = []
                for column in row:
                    row_array.append(column)
                if (len(row_array) == 2):
                    num_flights += 1
                    new_flight = [row_array]
                    flight_data.append(new_flight)
                else:
                    try:
                        flight_data[num_flights - 1].append(row_array)
                    except:
                        print("Unexpected values in file...")
                        time.sleep(1)
                        print("Exiting...")
                        time.sleep(3)
                        sys.exit()
                 
            
            if (num_flights == 0):
                print("No flight data found on SD card...")
                time.sleep(1)
                print("Exiting...")
                time.sleep(3)
                sys.exit()
            
            elif (num_flights == 1):
                print("Data for 1 flight found\n")
            else:
                print("Data for {} flights found\n".format(num_flights))
                
            i = 1
            for flight in flight_data:
                print(colored("~~~~~~~~~~~ Flight {} ~~~~~~~~~~~".format(i), 'blue'))
                sea_level_pressure = flight[0][0]
                outside_temp = flight[0][1]
                print("Sea Level Pressure: {} [hPa]".format(sea_level_pressure))
                print("Outside temperature: {} [C]".format(outside_temp))
                flight.pop(0)
                flight_data = processData(flight, sea_level_pressure_manual, outside_temp_manual)
                
                entries = len(flight)
                flight_time = (flight_data[0][-1] - flight_data[0][0])
                if (flight_time < 1000):
                    print("{} data entries, over {:.2f} milliseconds".format(entries, flight_time))
                elif (flight_time < 60000):
                    print("{} data entries, over {:.2f} seconds".format(entries, flight_time/1000.0))
                elif (flight_time < 360000):
                    print("{} data entries, over {:.2f} minutes".format(entries, flight_time/60000.0))
                else:
                    print("{} data entries, over {:.2f} hours".format(entries, flight_time/360000.0))
                
                apogee_auto = max(flight_data[4])
                print("Auto apogee of ",end ='')
                print(colored("{:.1f} metres ".format(apogee_auto), 'green'), end='')
                print("above sea level recorded")
                print("Auto max height above ground of ",end='')
                print(colored("{:.1f} metres ".format(apogee_auto - min(flight_data[4])), 'green'), end='')
                print("recorded")
                if ((sea_level_pressure_manual != None) and (outside_temp_manual != None)):
                    apogee_manual = max(flight_data[14])
                    print("Manual apogee of ", end='')
                    print(colored("{:.1f} metres ".format(apogee_manual), 'green'), end = '')
                    print("above sea level calculated")
                    print("Manual max height above ground of ",end='')
                    print(colored("{:.1f} metres ".format(apogee_manual - min(flight_data[14])), 'green'), end = '')
                    print("calculated")
                    if ((apogee_manual - min(flight_data[14])) > 1000):
                        print(colored("Woo! One kilometre!!! Musk and Bezos can eat a dick!", 'red'))
                    
                # Ask the user to give a time range to create graphs for
                flight_data = limitTime(flight_data);
                
                # Create a directory of all the graphs for each flight
                # then make python script into executable
                createFiles(flight_data, str(i), flightset_dir, sea_level_pressure, outside_temp, sea_level_pressure_manual, outside_temp_manual)
                
                print("")
                i += 1
    
    command = 'explorer "' + flightset_dir + '"'  
    subprocess.Popen(command)
    
    print("Type 'exit' to close the program... ",end='')
    while (input() != "exit"):
        sys.stdout.write("\033[F")
        sys.stdout.write("\033[K")
        print("\rType 'exit' to close the program... ",end='')
    print("Goodbye!")
    time.sleep(1)
    
def processData(flight, sea_level_pressure_manual, outside_temp_manual):
    timestamps = []
    temps = []
    humidities = []
    pressures = []
    altitudes = []
    xaccels = []
    yaccels = []
    zaccels = []
    xgyros = []
    ygyros = []
    zgyros = []
    xmags = []
    ymags = []
    zmags = []
    manual_altitudes = []
    
    first_time = float(flight[0][0])
    
    for row in flight:
        timestamps.append(float(row[0]) -  first_time)
        temps.append(float(row[1]))
        humidities.append(float(row[2]))
        pressures.append(float(row[3]))
        altitudes.append(float(row[4]))
        xaccels.append(float(row[5]))
        yaccels.append(float(row[6]))
        zaccels.append(float(row[7]))
        xgyros.append(float(row[8]))
        ygyros.append(float(row[9]))
        zgyros.append(float(row[10]))
        xmags.append(float(row[11]))
        ymags.append(float(row[12]))
        zmags.append(float(row[13]))
    
    if ((sea_level_pressure_manual != None) and (outside_temp_manual != None)):
        for pressure in pressures:
            manual_altitudes.append(pressure_to_altitude(pressure, sea_level_pressure_manual, outside_temp_manual))
    else:
        for pressure in pressures:
            manual_altitudes.append(0);   # not provided with manual values, so just write to zero
    
    temps_corrected = []
    for temp in temps:
        if (temp > 50):
            temp = temps[0]
        temps_corrected.append(temp)
    temps = temps_corrected
    
    hums_corrected = []
    for hum in humidities:
        if (hum == 100):
            hum = humidities[0]
        hums_corrected.append(hum)
    humidities = hums_corrected
        
        
    auto_altitude_gnd = []
    # Get the lowest altitude recorded before apogee was reached, use this as ground reference
    ground_height = min(altitudes[:max(range(len(altitudes)), key=altitudes.__getitem__)])
    for altitude in altitudes:
        auto_altitude_gnd.append(altitude - ground_height)
    
    manual_altitude_gnd = []
    # Get the lowest altitude calculated before apogee was reached, use this as ground reference
    ground_height = min(manual_altitudes[:max(range(len(manual_altitudes)), key=manual_altitudes.__getitem__)])
    for altitude in manual_altitudes:
        manual_altitude_gnd.append(altitude - ground_height)
    
    
    flight_data = [timestamps, temps, humidities, pressures, altitudes, xaccels, yaccels, zaccels, xgyros, ygyros, zgyros, xmags, ymags, zmags, manual_altitudes, auto_altitude_gnd, manual_altitude_gnd]
    return flight_data

def find(name, path):
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)
            
def createFiles(flight_data, flight_name, flightset_dir, sea_level_pressure, outside_temp, sea_level_pressure_manual, outside_temp_manual):
    
    #Create a directory for this actual flight
    dir = os.path.join(flightset_dir, ("Flight_" + flight_name))
    
    if (not os.path.exists(dir)):
        os.makedirs(dir)
    
    save_plot(flight_name, "Temperature",             flight_data[0], flight_data[1],   "[C]",       dir)
    save_plot(flight_name, "Humidity",                flight_data[0], flight_data[2],   "[%]",       dir)
    save_plot(flight_name, "Pressure",                flight_data[0], flight_data[3],   "[hPa]",     dir)
    save_plot(flight_name, "Auto_Altitude",           flight_data[0], flight_data[4],   "[m]",       dir)
    save_plot(flight_name, "x_Accel",                 flight_data[0], flight_data[5],   "[ms^-2]",   dir)
    save_plot(flight_name, "y_Accel",                 flight_data[0], flight_data[6],   "[ms^-2]",   dir)
    save_plot(flight_name, "z_Accel",                 flight_data[0], flight_data[7],   "[ms^-2]",   dir)
    save_plot(flight_name, "x_Gyro",                  flight_data[0], flight_data[8],   "[rads^-1]", dir)
    save_plot(flight_name, "y_Gyro",                  flight_data[0], flight_data[9],   "[rads^-1]", dir)
    save_plot(flight_name, "z_Gyro",                  flight_data[0], flight_data[10],  "[rads^-1]", dir)
    save_plot(flight_name, "x_Mag",                   flight_data[0], flight_data[11],  "[mG]",      dir)
    save_plot(flight_name, "y_Mag",                   flight_data[0], flight_data[12],  "[mG]",      dir)
    save_plot(flight_name, "z_Mag",                   flight_data[0], flight_data[13],  "[mG]",      dir)
    save_plot(flight_name, "Auto_Altitude_Gnd",       flight_data[0], flight_data[15],  "[m]",       dir)
    if (max(flight_data[14]) > 0):
        save_plot(flight_name, "Manual_Altitude",     flight_data[0], flight_data[14],  "[m]",       dir)
        save_plot(flight_name, "Manual_Altitude_Gnd", flight_data[0], flight_data[16],  "[m]",       dir)
    
    write_key_stats(flight_name, flight_data, dir, sea_level_pressure, outside_temp, sea_level_pressure_manual, outside_temp_manual)
    print(colored("\nFlight info and graphs saved in {}".format(dir), 'yellow'))

def save_plot(flight_name, plotname, times, data, units, dir):
    plt.plot(times, data, color='red')
    plt.title("Flight {}, {}".format(flight_name, plotname))
    plt.grid(True)
    plt.xlabel('Time [ms]')
    plt.ylabel("{} {}".format(plotname, units))
    plt.axis([min(times), max(times), min(data) - abs(0.1*(max(data)-min(data))), max(data) + abs(0.1*(max(data)-min(data)))])
    filename = str(plotname) + ".png"
    fullfilename = os.path.join(dir, filename)
    plt.savefig(fullfilename)
    plt.clf()
    

def write_key_stats(flight_name, flight_data, dir, sea_level_pressure, outside_temp, sea_level_pressure_manual, outside_temp_manual):
    entries = len(flight_data)
    flight_time = (flight_data[0][-1] - flight_data[0][0])
    auto_apogee = max(flight_data[4])
    auto_max_height_gnd = max(flight_data[15])
    manual_apogee = max(flight_data[14])
    manual_max_height_gnd = max(flight_data[16])
    file_name = os.path.join(dir, "key_stats.txt")
    f = open(file_name, "a")
    f.write("Key statistics for flight {}\n\n".format(flight_name))
    if (flight_time < 1000):
        f.write("{} data entries, over {:.2f} milliseconds\n".format(entries, flight_time))
    elif (flight_time < 60000):
        f.write("{} data entries, over {:.2f} seconds\n".format(entries, flight_time/1000.0))
    elif (flight_time < 360000):
        f.write("{} data entries, over {:.2f} minutes\n".format(entries, flight_time/60000.0))
    else:
        f.write("{} data entries, over {:.2f} hours\n".format(entries, flight_time/360000.0))
    f.write("\nFlight computer was programmed with...\n")
    f.write("Sea level pressure = {} [hPa]\n".format(sea_level_pressure))
    f.write("Outside temperature = {} [C]\n".format(sea_level_pressure))
    f.write("Flight computer recorded an apogee of {:.2f} [m] above sea level\n".format(auto_apogee))
    f.write("Flight computer recorded a height of {:.2f} [m] above ground\n".format(auto_max_height_gnd))
    if (manual_apogee != 0):
        f.write("\nManual sea level pressure = {} [hPa]\n".format(sea_level_pressure_manual))
        f.write("Manual outside temperature = {} [C]\n".format(outside_temp_manual))
        f.write("Manual pressure conversion gives an apogee of {:.2f} [m] above sea level\n".format(manual_apogee))
        f.write("Manual pressure conversion gives a height of {:.2f} [m] above ground\n".format(manual_max_height_gnd))
    f.close()

    return None

#https://en.wikipedia.org/wiki/Barometric_formula
#https://keisan.casio.com/exec/system/1224585971
def pressure_to_altitude(pressure, sea_level_pressure, outside_temp):
    
    outside_temp = float(outside_temp) + 273.15
    try:
        pressure_ratio = float(sea_level_pressure) / float(pressure)
    except ValueError:
        return 0
    exp = 0.1902664357
    gain = 2000.0 / 13.0
    try:
        return (outside_temp * gain) * ((math.pow(pressure_ratio, exp) - 1))
    except ValueError:
        return 0

def getSeaLevelPressure():
    print("https://meteologix.com/uk/observations/cambridgeshire/pressure-qnh/20210622-1900z.html")
    try:
        sea_level_pressure_manual = float(input("Enter sea level pressure [hPa] at time of flight: "))
    except ValueError:
        print("That's not a number, will rely on automatic mid-flight conversions")
        return None
    
    return sea_level_pressure_manual
    
def getOutsideTemp():
    print("\nhttps://www.bbc.co.uk/weather/2653941")
    try:
        outside_temp_manual = float(input("Enter outside air temp [C] at time of flight: "))
    except ValueError:
        print("That's not a number... will rely on automatic mid-flight conversions")
        return None
    
    return outside_temp_manual

def getRemovableDisks():
    
    possibleSDlocations = []
    
    drivelist = subprocess.Popen('wmic logicaldisk get name, description', shell=True, stdout=subprocess.PIPE)
    drivelisto, err = drivelist.communicate()
    driveliststr = str(drivelisto)
    drivelist = driveliststr.split('\\r')
    removable_disks = []
    for disk in drivelist:
        if 'Removable Disk' in disk:
            removable_disks.append(disk)
            
    for removable_disk in removable_disks:
        possibleSDlocations.append((removable_disk.split(':'))[0][-1])
        
    return possibleSDlocations
    
def limitTime(flight_data):
    
    startTime = 0
    try:
        startTime = float(input("\nEnter start time for graphs (default = 0) [seconds] : "))
    except ValueError:
        print("That's not a number... defaulting to starting graphs at time = 0 [seconds]")
    startTime = startTime * 1000.0
    
    endTime = (flight_data[0][-1] - flight_data[0][0]) / 1000.0
    myString = "Enter end time for graphs (default = {}) [seconds] : ".format(endTime)
    try:
        endTime = float(input(myString))
    except ValueError:
        print("That's not a number... defaulting to ending graphs at time = {} [seconds]".format(endTime))
    endTime = endTime * 1000.0
    
    # find index of first value after start time, then = min(0, index - 1)
    i = 0
    time_entries = len(flight_data[0])
    try:
        while (float(flight_data[0][i]) < startTime):
            i += 1
    except IndexError:
        i = 0
    startIndex = i
    
    i = 0
    try:
        while (float(flight_data[0][i]) < endTime):
            i += 1
    except IndexError:
        i = -1
    endIndex = i
    
    if (endIndex > time_entries):
        endIndex = -1
        
    truncatedFlightData = []
    
    for variable in flight_data:
        truncatedFlightData.append(variable[startIndex:endIndex])
     
    return truncatedFlightData

main()