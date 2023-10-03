# Script for modification data from APC SYMETRA SYBT5 battery module
# input file must by in the format INTEL-HEX. I use SW PonyProg for reading and writing data from/to EEPROM
# EEPROM type is 93C66B
#
# created by Miroslav Pivovarsky - miroslav.pivovarsky@gmail.com

import sys

def calculate_checksum_and_format_line(line_tmp):
    byte_data = [line_tmp[j:j + 2] for j in range(1, len(line_tmp), 2)]
    checksum = sum(int(x, 16) for x in byte_data) & 0xFF
    checksum = (0xFF - checksum + 1) & 0xFF
    checksum_hex = format(checksum, '02X')
    line_out = line_tmp + checksum_hex
    return line_out

print("")
if len(sys.argv) < 3:
    print("Missing neccesary input parameters. checksum_file.py filename manufacture_date")
    print("file name: <file.hex>. File with intel HEX format")
    print("New manufacture date: DD/MM/YY")
    print("For example: python3.9 checksum_file.py battery.hex 26/09/23")
    print("")
    print("Optional parameter is argument 3, new serial number: QD0937150369")
    print("Example with optional parameter: python3.9 checksum_file.py battery.hex 26/09/23 QD0937150369")
    print("")
    print("It is necessary to observe the format and length of the string for the date and serial number!")
    sys.exit(1)

enable_set_SN = False
file_in = sys.argv[1]
file_out = file_in.replace(".hex", "_edit.hex")
set_date = sys.argv[2]

print("Input parameters: ")
print("File name input: " + file_in)
print("File name output: " + file_out)
print("Manufacture date: " + set_date)

if len(sys.argv) == 4:
    set_SN = sys.argv[3]
    print("New serial number: " + set_SN)
    enable_set_SN = True

print("")
print("Start updating file...")
print("Reading original file")

with open(file_in, 'r') as file:
    data_hex = []
    data_raw = [] 
    read_data = False
    
    # read lines from file
    for line in file:
        # read data from line ":100000"
        if line.startswith(':100000'):
            read_data = True

        # read data from line ":1000A0"
        if line.startswith(':1000A0'):
            read_data = False
            continue

        # update new datum
        if line.startswith(':100090'):
            read_data = False
            hex_date = "00" + ''.join(f'00{ord(c):02X}' for c in set_date)
            data_hex.append(hex_date)
        
		# update manufacture number
        if line.startswith(':100050'):
            if enable_set_SN == True:
                read_data = False
                start_line = line[7:25]
                data = set_SN[:4]
                new_sn = ''.join(f'00{ord(c):02X}' for c in data)
                data_hex.append(start_line + new_sn)

        # update manufacture number
        if line.startswith(':100060'):
            if enable_set_SN == True:
                data = set_SN[4:13]
                new_sn = "00" + ''.join(f'00{ord(c):02X}' for c in data)
                data_hex.append(new_sn)

        # after update SN, continue
        if line.startswith(':100070'):
            read_data = True
			
		# read data from ":100000" to ":100050" and from ":100070" to ":100090"
        if read_data:
            # removed first 7 symbols and last 3 symbols (:10xxxxxx DATA CRC)
            data = line[7:-3].strip()
            data_hex.append(data)

# calculation checksum
print("Calculation checksum...")
checksum = sum(int(x, 16) for row in data_hex for x in [row[i:i+2] for i in range(0, len(row), 2)])

modified_checksum = ((checksum & 0x00FF) << 16) | (checksum & 0x00FF00)
checksum_hex = ' '.join(f'{x:02X}' for x in bytearray.fromhex(hex(modified_checksum)[2:]))
checksum_hex_out = '0000' + checksum_hex[0:2] + '00' + checksum_hex[3:5] + '000000000000000000000000'

print("Generating new data: ")
with open(file_out, 'w') as edit_file:
    for i in range(32):
        formatted_i = format(i, '04X')
        formatted_line = f":1{formatted_i}0"
        
        if i < 10:
            line_tmp = formatted_line + data_hex[i]
            line_out = calculate_checksum_and_format_line(line_tmp)
            edit_file.write(line_out + '\n')
            print(line_out)
        elif i == 10:
            line_tmp = formatted_line + checksum_hex_out
            line_out = calculate_checksum_and_format_line(line_tmp)
            edit_file.write(line_out + '\n')
            print(line_out)
        else:
            line_tmp = formatted_line + "0000000000000000000000000000000000"
            line_out = calculate_checksum_and_format_line(line_tmp)
            edit_file.write(line_out + '\n')
            print(line_out)

    edit_file.write(":00000001FF" + '\n')

print("")
print("Data is saved in the file " + file_out)

# EOF