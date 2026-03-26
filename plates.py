def main():
    plate = input("Plate: ")
    if is_valid(plate):
        print("Valid")
    else:
        print("Invalid")


def is_valid(s):
    if len(s) < 2 or len(s) > 6:
        return False
    
    if not s.isalnum():
        return False
    
    if not s[0:2].isalpha():
        return False
    
    return check_number_placement(s)


def check_number_placement(s):
    number_start = None
    for i, char in enumerate(s):
        if char.isdigit():
            number_start = i
            break
    
    if number_start is None:
        return True
    
    for i in range(number_start, len(s)):
        if not s[i].isdigit():
            return False
    
    if s[number_start] == '0':
        return False
    
    return True


if __name__ == "__main__":
    main()
