def increment_string(string):
    i = len(string)
    while i > 0 and string[i-1].isdigit():
        i -= 1
    
    prefix = string[:i]
    number = string[i:]
    
    if number:
        new_number = str(int(number) + 1).zfill(len(number))
        return prefix + new_number
    else:
        return string + '1'
    

print(increment_string("alihasssan200721"))