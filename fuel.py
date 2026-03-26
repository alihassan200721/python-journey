def main():
    while True:
        try:
            #user input 
            x, y = input("Fraction: ").split("/")
            x = int(x)
            y = int(y)

            #percentage calulate
            percentage = (x/y) * 100
            if x > y:
                continue

            #round of to the nearest integer
            round_percentage = round(percentage)

            #output
            if round_percentage <= 1:
                print("E")

            elif round_percentage >= 99:
                print("F")

            else:
                print(f"{round_percentage}%")
                break

        except (ValueError, ZeroDivisionError):
            continue


main()
