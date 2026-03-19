def main():
    user_input = input("Enter string: ")
    rev_string = reverse_string(user_input)
    print(rev_string)

def reverse_string(string):
    reverse_str = ""

    for char in string:
        reverse_str = char + reverse_str

    return reverse_str


main()

