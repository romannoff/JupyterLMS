import re

text = """
'All tests passed!
peak memory: 68.95 MiB, increment: 0.19 MiB
CPU times: user 51.9 ms, sys: 2.94 ms, total: 54.8 ms
Wall time: 171 ms
"""

pattern = r'peak memory: ([0-9\.]+) .*? increment: ([0-9\.]+)'
pattern2 = r'CPU times: .*? total: ([0-9\.]+)'

print(re.findall(pattern, text)[0])
print(re.findall(pattern2, text)[0])