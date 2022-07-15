from pprint import pp
import random
import os
import pandas as pd # pip install pandas -> https://pypi.org/project/pandas/
import numpy as np 

from rcplant import *  # using the pip package

def is_PVC(spectrum):
    decision = False
    if 1250 < spectrum.idxmax() < 1275:
        decision = True
    return decision

def is_PS(spectrum):
    decision = False
    if 1400 < spectrum.idxmax() < 1500:
        decision = True
    return decision

def is_PP_HPDE_LDPE(spectrum):
    decision = False
    if 2850 < spectrum.idxmax() < 2950:
        decision = True
    return decision

def is_PC_PU_PET_Polyester(spectrum): #one PC max occurs at 1250, others are around 1700 - 1800
    decision = False    
    if 1700 < spectrum.idxmax() < 1800 or spectrum.idxmax() == 1250:
        decision = True
    return decision

def is_PU(spectrum):
    decision = False
    spectrum_zoomin = spectrum.loc[3500:3050]
    if 3300 < spectrum_zoomin.idxmax() < 3400:  # wavenumber of second max transmittance
        decision = True
    return decision

def is_PET_Polyester(spectrum):
    decision = False
    spectrum_zoomin = spectrum.loc[1700:1250]
    if spectrum_zoomin.idxmax() < 1300:  # wavenumber of second max transmittance
        decision = True
    return decision

#import the data from the excel database
def import_excel(x):
    data_file = os.path.join(os.path.dirname(__file__), 'averagespectra.xlsx') 
    data_table = pd.read_excel(data_file, sheet_name=0, index_col=0)
    raw_spectrum = data_table.loc[x]
    return raw_spectrum;

#global variables of all the average spectras
hdpespectra = import_excel('HDPE')
ldpespectra = import_excel('LDPE')
ppspectra = import_excel('PP')
psspectra = import_excel('PS')
pcspectra = import_excel('PC')
pvcspectra = import_excel('PVC')
polysterspectra = import_excel('Polyester')
petspectra = import_excel('PET')
puspectra = import_excel('PU')

def user_sorting_function(sensors_output):
    # This sorting function provides a simple example to help you understand how to use
    # the variable sensors_output. You need to figure out more advanced function to achieve 
    # a higher sorting accuracy in both 'training' and 'testing' mode
    sensor_id = 1
    spectrum = sensors_output[sensor_id]['spectrum']
    
    decision = {sensor_id:random.choice(list(Plastic)[0:-1])} 
    if spectrum.iloc[0] == 0:  # For FTIR, if the first transmittance is 0, it is blank spectra
        decision = {sensor_id:Plastic.Blank}
    else:

        #calculate the difference between the sensor spectra and the average spectras for all the plastics
        s1 = abs(spectrum - hdpespectra)
        s2 = abs(spectrum - ldpespectra)
        s3 = abs(spectrum - ppspectra)
        s4 = abs(spectrum - psspectra)
        s5 = abs(spectrum - pcspectra)
        s6 = abs(spectrum - pvcspectra)
        s7 = abs(spectrum - polysterspectra)
        s8 = abs(spectrum - petspectra)
        s9 = abs(spectrum - puspectra)

        #add up all the differences 
        sum1 = s1.sum()
        sum2 = s2.sum()
        sum3 = s3.sum()
        sum4 = s4.sum()
        sum5 = s5.sum()
        sum6 = s6.sum()
        sum7 = s7.sum()
        sum8 = s8.sum()
        sum9 = s9.sum()

        #redundant code, just helps show the code is running
        print(sum1,sum2,sum3,sum4,sum5,sum6,sum7,sum8,sum9)

        #choose the spectra that has the lowest difference
        answer = min(sum1, sum2, sum3, sum4, sum5, sum6, sum7, sum8, sum9)

        #set the type of plastic depending on the choice
        if answer == sum1:
            decision = {sensor_id : Plastic.HDPE}
        elif answer == sum2:
            decision = {sensor_id : Plastic.LDPE}
        elif answer == sum3:
            decision = {sensor_id : Plastic.PP}
        elif answer == sum4:
            decision = {sensor_id : Plastic.PS}
        elif answer == sum5:
            decision = {sensor_id : Plastic.PC}
        elif answer == sum6:
            decision = {sensor_id : Plastic.PVC}
        elif answer == sum7:
            decision = {sensor_id : Plastic.Polyester}
        elif answer == sum8:
            decision = {sensor_id : Plastic.PET}
        else:
            decision = {sensor_id : Plastic.PU}
        
        
        #EDGE CASES TO MAKE THE ALGORITHM MORE ACCURATE
        if is_PVC(spectrum):                                         #check if pvc
            decision = {sensor_id : Plastic.PVC}
        elif is_PS(spectrum):                                        #check if ps
            decision = {sensor_id : Plastic.PS}
        elif is_PP_HPDE_LDPE(spectrum):                              #check if pp
            
            spectrum_zoomin = spectrum.loc[1550:1250]   # zoom in to check the second max
            if 1350 < spectrum_zoomin.idxmax() < 1450:  # Difference occurs at the second max transmittance
                decision = {sensor_id : Plastic.PP}

        #MORE EDGE CASES TO NARROW DOWN ONCE A PLASTIC IS CHOSEN
        if decision == {sensor_id : Plastic.PVC}:                       #note one case still exists where identified PVC but acc PET
            spectrum_zoomin = spectrum.loc[1800:1250]                   #this edge case can be further narrowed
            if spectrum_zoomin.idxmax() > 1500:
                decision = {sensor_id : Plastic.PET}
        

        #^^^^^^^^^^ whats going on here is:
        # if the choice made was PVC
        # zoom into this spectra range and if the maxium value is after 1500, set the plastic to PET

        if decision == {sensor_id : Plastic.PET}:                #note red and orange cases need to be checked
            spectrum_zoomin = spectrum.loc[3000:2750]              #this edge case could be further narrowed
            if spectrum_zoomin.max() > 0.1:
                decision = {sensor_id : Plastic.Polyester}

        if decision == {sensor_id : Plastic.PS}:
            if 2750 < spectrum.idxmax() < 3000:
                decision = {sensor_id : Plastic.LDPE}

        #more edge cases can make this more accurate, HDPE VS LDPE is very hard

    return decision



def main():

    # simulation parameters
    conveyor_length = 1000  # cm
    conveyor_width = 100  # cm
    conveyor_speed = 35  # cm per second
    num_containers = 2000
    sensing_zone_location_1 = 500  # cm
    sensors_sampling_frequency = 5 # Hz
    simulation_mode = 'testing'

    #Add two lists
    identification_lst = []
    actual_lst = []
    
    sensors = [
        Sensor.create(SpectrumType.FTIR, sensing_zone_location_1),
    ]

    conveyor = Conveyor.create(conveyor_speed, conveyor_length, conveyor_width)

    simulator = RPSimulation(
        sorting_function=user_sorting_function,
        num_containers=num_containers,
        sensors=sensors,
        sampling_frequency=sensors_sampling_frequency,
        conveyor=conveyor,
        mode=simulation_mode
    )

    elapsed_time = simulator.run()  #added last two arguments
    for item_id, result in simulator.identification_result.items():
        if result['actual_type'] != result['identified_type']:
            print(f"incorrectly identified : {result}")


    print(f'\nResults for running the simulation in "{simulation_mode}" mode:')
    print(f'Total missed containers = {simulator.total_missed}')
    print(f'Total sorted containers = {simulator.total_classified}')
    print(f'Total mistyped containers = {simulator.total_mistyped}')

    print(f'\n{num_containers} containers are processed in {elapsed_time:.2f} seconds')


if __name__ == '__main__':
    main()
