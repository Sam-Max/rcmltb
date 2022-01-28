def status(val):
    if val < 10:
        progress = "[▫️▫️▫️▫️▫️▫️▫️▫️▫️▫️]"

    if val >= 10 and val <= 19:
        progress = "[▪️▫️▫️▫️▫️▫️▫️▫️▫️▫️]"

    if val >= 20 and val <= 29:
        progress = "[▪️▪️▫️▫️▫️▫️▫️▫️▫️▫️]"

    if val >= 30 and val <= 39:
        progress = "[▪️▪️▪️▫️▫️▫️▫️▫️▫️▫️]"

    if val >= 40 and val <= 49:
        progress = "[▪️▪️▪️▪️▫️▫️▫️▫️▫️▫️]"

    if val >= 50 and val <= 59:
        progress = "[▪️▪️▪️▪️▪️▫️▫️▫️▫️▫️]"

    if val >= 60 and val <= 69:
        progress = "[▪️▪️▪️▪️▪️▪️▫️▫️▫️▫️]"

    if val >= 70 and val <= 79:
        progress = "[▪️▪️▪️▪️▪️▪️▪️▫️▫️▫️]"

    if val >= 80 and val <= 89:
        progress = "[▪️▪️▪️▪️▪️▪️▪️▪️▫️▫️]"

    if val >= 90 and val <= 99:
        progress = "[▪️▪️▪️▪️▪️▪️▪️▪️▪️▫️]"

    if val == 100:
        progress = "[▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️]"

    return progress
