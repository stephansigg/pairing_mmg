import pandas as pd
import matplotlib.pyplot as plt
from scipy.integrate import cumtrapz
import scipy.signal as sig
import glob


def grey_code_extraction_3bit(a, b):
    if (a is None or len(a) == 0 or b is None or len(b) == 0):
        ValueError(" grey_code_extraction:  invalid parameters ")
    i = 0
    bits_str = ''
    while(i + jump < len(a) or i + jump < len(b)):        
        if (a[i + jump] - a[i] >= 0) and (b[i + jump] - b[i] >= 0):
            if abs(b[i + jump] - b[i]) <= abs(a[i + jump] - a[i]):
                bits_str += '000'
            else:
                bits_str += '001'
        elif (a[i + jump] - a[i] < 0) and (b[i + jump] - b[i] >= 0):
            if abs(b[i + jump] - b[i]) > abs(a[i + jump] - a[i]):
                bits_str += '011'
            else:
                bits_str += '010'
        elif (a[i + jump] - a[i] < 0) and (b[i + jump] - b[i] < 0):
            if abs(b[i + jump] - b[i]) <= abs(a[i + jump] - a[i]):
                bits_str += '110'
            else:
                bits_str += '111'
        else:
            if abs(b[i + jump] - b[i]) > abs(a[i + jump] - a[i]):
                bits_str += '101'
            else:
                bits_str += '100'
        i += 1
    return bits_str

# jump in terms of datapoint used for extracting the grey code
jump = 2
threshold = 0.7
zeroes = [0.0, 0.0]
calib_acc = 0.2
calib_vel = 0.02
results = {'matching_success': [], 
            'non_matching_success': [], 
            'false_positives': [], 
            'false_negatives': []}


files_phone = glob.glob('Tests/unlock_pattern/final_tests/Drawing_Data/*_smartphone_sample.csv')
files_watch = glob.glob('Tests/unlock_pattern/final_tests/Accelerometer_Data/*_watch_sample.csv')

files_phone.sort()
files_watch.sort()


for file_phone in files_phone:
    # DataFrame collection from files
    data_phone = pd.read_csv(file_phone, engine='python')
    for file_watch in files_watch:
        data_watch = pd.read_csv(file_watch, engine='python')

        file_phone_identifier = file_phone.split('/')[-1].split('_')[1]
        file_watch_identifier = file_watch.split('/')[-1].split('_')[1]

        x_acc_filtered = data_watch['x_lin_acc'].to_list()
        y_acc_filtered = data_watch['y_lin_acc'].to_list()

        x_vel_filtered = data_phone['x_velocity_filtered'].to_list()
        y_vel_filtered = (data_phone['y_velocity_filtered'] * -1).to_list()

        #Acceleration Noise filtering
        for i in range(0, len(x_acc_filtered)):
            if x_acc_filtered[i] <= calib_acc and x_acc_filtered[i] >= -calib_acc:
                x_acc_filtered[i] = 0
            if y_acc_filtered[i] <= calib_acc and y_acc_filtered[i] >= -calib_acc:
                y_acc_filtered[i] = 0

        #Velocity Noise filtering
        for i in range(0, len(x_vel_filtered)):
            if x_vel_filtered[i] <= calib_vel and x_vel_filtered[i] >= -calib_vel:
                x_vel_filtered[i] = 0
            if y_vel_filtered[i] <= calib_vel and y_vel_filtered[i] >= -calib_vel:
                y_vel_filtered[i] = 0

        x_acc_non_zero = [idx for idx, val in enumerate(x_acc_filtered) if val != 0]
        y_acc_non_zero = [idx for idx, val in enumerate(y_acc_filtered) if val != 0]

        if not x_acc_non_zero and not y_acc_non_zero:
            print(file_phone_identifier, file_watch_identifier, 'No motion detected from accelerometer!')
            continue
        elif not x_acc_non_zero:
            acc_start = y_acc_non_zero[0]
            acc_end = y_acc_non_zero[-1]
        elif not y_acc_non_zero:
            acc_start = x_acc_non_zero[0]
            acc_end = x_acc_non_zero[-1]
        else:
            acc_start = x_acc_non_zero[0] if x_acc_non_zero[0] < y_acc_non_zero[0] else y_acc_non_zero[0]
            acc_end = x_acc_non_zero[-1] if x_acc_non_zero[-1] > y_acc_non_zero[-1] else y_acc_non_zero[-1]


        x_vel_non_zero = [idx for idx, val in enumerate(x_vel_filtered) if val != 0]
        y_vel_non_zero = [idx for idx, val in enumerate(y_vel_filtered) if val != 0]

        if not x_vel_non_zero and not y_vel_non_zero:
            print(file_phone_identifier, file_watch_identifier, 'No motion detected from smartphone!')
            continue
        elif not x_vel_non_zero:
            vel_start = y_vel_non_zero[0]
        elif not y_vel_non_zero:
            vel_start = x_vel_non_zero[0]
        else:
            vel_start = x_vel_non_zero[0] if x_vel_non_zero[0] < y_vel_non_zero[0] else y_vel_non_zero[0]

        x_acc_filtered = zeroes + x_acc_filtered[acc_start:acc_end] + zeroes
        y_acc_filtered = zeroes + y_acc_filtered[acc_start:acc_end] + zeroes

        x_vel_filtered = zeroes + x_vel_filtered[vel_start:] + zeroes
        y_vel_filtered = zeroes + y_vel_filtered[vel_start:] + zeroes


        x_vel = cumtrapz(x_acc_filtered)
        x_vel = [0.0] + x_vel

        y_vel = cumtrapz(y_acc_filtered)
        y_vel = [0.0] + y_vel

        x_vel_final = sig.resample(x_vel_filtered, len(x_vel))
        y_vel_final = sig.resample(y_vel_filtered, len(y_vel))
        
        for i in range(0, len(x_vel_final)):
            if x_vel_final[i] <= calib_vel and x_vel_final[i] >= -calib_vel:
                x_vel_final[i] = 0
            if y_vel_final[i] <= calib_vel and y_vel_final[i] >= -calib_vel:
                y_vel_final[i] = 0

        watch_vel_greycode = grey_code_extraction_3bit(x_vel, y_vel)
        phone_vel_greycode = grey_code_extraction_3bit(x_vel_final, y_vel_final)

        matching_codes_count = 0
        for i in range(0, len(phone_vel_greycode)):
            if watch_vel_greycode[i] == phone_vel_greycode[i]:
                matching_codes_count += 1
        match_result = matching_codes_count / len(phone_vel_greycode)

        
        if file_phone_identifier == file_watch_identifier:
            if match_result >= threshold:
                results['matching_success'].append(match_result)
            else:
                #print(file_phone_identifier, file_watch_identifier, match_result)
                results['false_negatives'].append(match_result)
        else:
            if match_result < threshold:
                results['non_matching_success'].append(match_result)
            else:
                #print(file_phone_identifier, file_watch_identifier, match_result)
                results['false_positives'].append(match_result)

        

print('Result using 3-bit encoding:')
print('Total tests:', len(files_phone) * len(files_watch))
print('-------------------------------')
print('Key\t\t   Count  Min  Max')
for key in results.keys():
    if results[key]:
        print(key, ':', len(results[key]), min(results[key]), max(results[key]))

print('-------------------------------')

plt.hist(results['non_matching_success'] + results['false_positives'],
                 label = 'Non-matching samples', histtype='step', linewidth=2)

plt.hist(results['matching_success'] + results['false_negatives'],
                 label = 'Matching samples', histtype='step', linewidth=2)


plt.xlabel('Correlation ratio')
plt.ylabel('Number of pairing attempts')

plt.legend(loc="upper left")

plt.savefig('3bit_resampled.pdf') 