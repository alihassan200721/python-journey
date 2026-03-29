import sys
import random
from pyfiglet import Figlet

figlet = Figlet()
fonts = figlet.getFonts()

# Check cmd arg
if len(sys.argv) == 1:
    font = random.choice(fonts)

elif len(sys.argv) == 3:
    if sys.argv[1] == "-f" or sys.argv[1] == "--font":
        if sys.argv[2] in fonts:
            font = sys.argv[2]
        else:
            sys.exit("Invalid usage")
    else:
        sys.exit("Invalid usage")

else:
    sys.exit("Invalid usage")

#Seting font
figlet.setFont(font=font)

#user input
text = input("Input: ")

#ASCII art
print(figlet.renderText(text))
