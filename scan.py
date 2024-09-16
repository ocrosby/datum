import re

def print_previous_line_for_no_roster(file_path: str):
    with open(file_path, 'r') as file:
        previous_line = None
        for line in file:
            if re.match(r'No roster found for .*', line):
                if previous_line:
                    if previous_line.startswith('Sending request to '):
                        previous_line = previous_line[len('Sending request to '):]
                    previous_line = previous_line.strip()
                    if previous_line.endswith('...'):
                        previous_line = previous_line[:-3]

                    previous_line = previous_line.replace('/roster', '')
                    print(previous_line.strip())

            previous_line = line

# Usage
print_previous_line_for_no_roster('a.out')