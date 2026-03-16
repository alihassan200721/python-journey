import random  

#user info
name = input("Enter your name: ")
print("Welcome to Rock, Paper, Scissors, ", name)

#user wins, computer wins, ties
user_wins = 0
computer_wins = 0
ties = 0


#options
options = ["rock", "paper", "scissors"]


#game loop
while True:
    user_input = input("Enter rock/paper/scissors, or press Q to quit: ").strip().lower()
    if user_input == "q":
        print("Bye:)")
        break

    if user_input not in options:
        continue

    random_number = random.randint(0,2)
    computer_pick = options[random_number]

    if user_input == "rock" and computer_pick == "scissors":
        print(computer_pick)
        print("You WON!")
        user_wins += 1

    elif user_input == "paper" and computer_pick == "rock":
        print(computer_pick)
        print("You WON!")
        user_wins += 1

    elif user_input == "scissors" and computer_pick == "paper":
        print(computer_pick)
        print("You WON!")
        user_wins += 1

    elif user_input == "rock" and computer_pick == "rock":
        print(computer_pick)
        print("DRAW!")
        ties += 1

    elif user_input == "paper" and computer_pick == "paper":
        print(computer_pick)
        print("DRAW!")
        ties += 1

    elif user_input == "scissors" and computer_pick == "scissors":
        print(computer_pick)
        print("DRAW!")
        ties += 1

    else:
        print(computer_pick)
        print("Computer WON!")
        computer_wins += 1

print(name, "won", user_wins, "times.")
print("Computer won", computer_wins, "times")
print("Tied", ties)