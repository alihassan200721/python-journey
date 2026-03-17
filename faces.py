def main():
    user_input = input("Enter text: ")
    print(convert(user_input))



def convert(s):
    s = s.replace(":)", "🙂")
    s = s.replace(":(", "🙁")
    
    return s

main()