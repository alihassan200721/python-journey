#simple program

grocery = {}

try:
    while True:
        item = input().strip().lower()
        grocery[item] = grocery.get(item, 0) + 1
except EOFError:
    pass

for item in sorted(grocery):
    print(grocery[item], item.upper())
