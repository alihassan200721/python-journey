months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December"
]


# main loop
while True:
    date = input("Date: ").strip()

    try:
        #format one => MM/DD/YYYY
        if "/" in date:
            month, day, year = date.split("/")
            month = int(month)
            day = int(day)
            year = int(year)

        #format two => month DD, YYYY
        elif "," in date:
            month_day, year = date.split(", ")
            month_name, day = month_day.split(" ")

            month = months.index(month_name) + 1
            day = int(day)
            year = int(year)

        else:
            continue

        if 1 <= month <= 12 and 1 <= day <= 31:
            print(f"{year}-{month:02}-{day:02}")

    except (ValueError, IndexError):
        continue
