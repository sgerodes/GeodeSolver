import time

from src.pumpkin_solver import parse_input

# Contains 93 pumpkins
# This is the main direction in Ilmango's tutorial video
input_grid = '''00000000000000000
00000000p00000000
0000000pop0000000
000000pooop0p0000
00000ppoop0pop000
000ppoppopppop000
00popppoopoppp000
00poooppp0p0pop00
0poopppoppop0pop0
0poopppp00p0pop00
00ppooop0pp00p000
00popppppooppp000
000p00poppppoop00
0000000ppoppop000
000000ppppopop000
00000poooopop0000
000000ppoopp00000
00000000pp0000000
00000000000000000'''

start = time.time()
parse_input(input_grid)
print(f'Took {time.time() - start} seconds')
