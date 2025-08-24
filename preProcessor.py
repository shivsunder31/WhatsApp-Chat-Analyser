import re
import pandas as pd

def preProcess(data):
    # Pattern: [dd/mm/yy, hh:mm:ss AM/PM]
    pattern = r'\[(\d{1,2}/\d{1,2}/\d{2,4}),\s(\d{1,2}:\d{2}:\d{2}\s?[APMapm]{2})\]'
    matches = re.findall(pattern, data)

    # Split lines (each starts with [date])
    messages = re.split(pattern, data)[1:]

    dates = []
    msgs = []
    for i in range(0, len(messages), 3):  
        date = matches[i//3][0] + " " + matches[i//3][1]
        text = messages[i+2].strip() if i+2 < len(messages) else ""
        dates.append(date.replace('\u202f', ' '))  # fix narrow space
        msgs.append(text)

    df = pd.DataFrame({'message_date': dates, 'user_message': msgs})

    # Parse datetime (with seconds)
    df['message_date'] = pd.to_datetime(
        df['message_date'], 
        format="%d/%m/%y %I:%M:%S %p", 
        errors="coerce"
    )
    df.rename(columns={'message_date': 'date'}, inplace=True)

    # Split into user + message
    users, messages_out = [], []
    for message in df['user_message']:
        entry = re.split(r'([^:]+?):\s', message, maxsplit=1)
        if len(entry) >= 3:
            users.append(entry[1])
            messages_out.append(entry[2])
        else:
            users.append("group_notification")
            messages_out.append(message)
    df['user'] = users
    df['message'] = messages_out
    df.drop(columns=['user_message'], inplace=True)

    # Extract date parts
    df['only_date'] = df['date'].dt.date
    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute

    # Hourly period like "23-00"
    period = []
    for hour in df['hour'].fillna(0).astype(int):
        if hour == 23:
            period.append("23-00")
        elif hour == 0:
            period.append("00-1")
        else:
            period.append(f"{hour}-{hour+1}")
    df['period'] = period

    return df
