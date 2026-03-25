# coke machine
valid_coins = [25, 10, 5]
amount = 50
print("Amount Due:", amount)

while amount > 0:
    user_input = int(input("Insert Coin: "))
    if user_input not in valid_coins:
        print("Invalid coin. Please insert 25, 10, or 5 cents.")
        continue
    amount -= user_input
    print("Amount Due:", max(amount, 0))

if amount < 0:
    print(f"Change Owed: {abs(amount)}")
else:
    print("Change Owed: 0")
