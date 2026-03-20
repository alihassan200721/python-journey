gretting = input("Grettings: ").lower()

if gretting == "hello":
    print("$0")

elif gretting.startswith("h"):
    print("$20")

else:
    print("$100")
