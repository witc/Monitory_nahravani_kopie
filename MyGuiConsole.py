
from datetime import datetime


def myPrint(globalData, *message, end = "\n", sep = " ",tag="normal"):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    text = current_time
    text+=": "
    
    for item in message:
        text += "{}".format(item)
        text += sep
    text += end
    
    print(text)
    globalData.console.insert("end", text,tag)
    globalData.console.see("end")
    