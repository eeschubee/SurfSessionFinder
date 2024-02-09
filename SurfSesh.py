
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

#Surf Imports
import pysurfline
import pandas as pd

#freetime checker
from datetime import datetime, timedelta, timezone, time, date

#import pytz



# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def Surf_Functionality():
    
    
    #These should eventually be generated from suntimes, latitude and longitude for humboldt
    sunrise_time = time(7, 0, 0)
    sunset_time = time(18, 0, 0)
   
   
   
    #The surf spots Im looking at and the conditions I will use to determine if the spot is surfable at a given time, for noe only wave height matters. Eventuallt I want to start ranking surfable times to return the most ideal time to surf.
    #The spot ID is from surfline and is required to make an make a spot forecast request.
    surf_spots = [
        {
            'spot_id': '640a3fab606c458564b0a46f',
            'name': 'Trinidad State Beach',
            'min_wave_height': 3.0,
            'max_wave_height': 12.0,
            'ideal_wave_height': 5.0,
            'min_wind_speed': 0.0,
            'max_wind_speed': 0.0,
            'min_temperature': 20.0,
            'max_temperature': 120.0,
        },
        {
            'spot_id': '640a3faab6d7692d595138e8',
            'name': 'Moonstone beach',
            'min_wave_height': 3.0,
            'max_wave_height': 12.0,
            'ideal_wave_height': 5.0,
            'min_wind_speed': 0.0,
            'max_wind_speed': 0.0,
            'min_temperature': 20.0,
            'max_temperature': 120.0,
        },
        {
            'spot_id': '640a3fad99dd448108033544',
            'name': 'College Cove',
            'min_wave_height': 3.0,
            'max_wave_height': 8.0,
            'ideal_wave_height': 5.0,
            'min_wind_speed': 0.0,
            'max_wind_speed': 0.0,
            'min_temperature': 20.0,
            'max_temperature': 120.0,
        }
    ]
    #number of days of forcast and at what interval it should return the data.
    # this needs to be edditted that the forecast is for the same time frame as the calender request but for now this will do.
    days = 3
    intervalHours = 1
    
    All_Spots_Surfable_Hours = []
    for spots in surf_spots:
    
        spot_forecasts = pysurfline.get_spot_forecasts(
            spots['spot_id'],
            intervalHours,
            days,
        )
        
       
        df = spot_forecasts.get_dataframe()

        surfable_hours = []
        
        for index, row in df.iterrows():
            if row['timestamp_dt'].time() >= sunrise_time and row['timestamp_dt'].time() <= sunset_time and spots['max_wave_height'] >= row['surf_max'] and spots['min_wave_height'] <= row['surf_max']:
                surfable_hours.append(row)

        surfable_hours_df = pd.DataFrame(surfable_hours)
        
        All_Spots_Surfable_Hours.append({'name':spot_forecasts.name,'data':surfable_hours})


        print(spot_forecasts.name)
        
        if len(surfable_hours) != 0:
            print(surfable_hours_df[['timestamp_dt', 'surf_min', 'surf_max', 'speed', 'temperature']])
        else:
            print("There are no surfable hours")
        
    return All_Spots_Surfable_Hours


#Google quick start
def authenticate_google_calendar():
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())
  return creds


# Get events from calendar APi
def get_calendar_events(service, start_time, end_time):
    events_result = service.events().list(
        calendarId="primary",
        timeMin=start_time + "Z",
        timeMax=end_time + "Z",
        singleEvents=True,
        orderBy="startTime",
    ).execute()
    return events_result.get("items", [])
    
    
#Returns all free time slots
#This needs to be cleaned up could be a alot more concise
def get_free_time_slots(calendar_events, start_time, end_time, minimum_duration):
    
    #this conversion is necessary to so that the elements im comparing are in the saame datetime format. This comes from the imported date time.
    converted_start_time = datetime.fromisoformat(start_time)
    converted_end_time = datetime.fromisoformat(end_time)
    
    FreeTimes=[]
    
    if len(calendar_events) != 0:
        for i in range(len(calendar_events)):
        
            event = calendar_events[i]
            
            #this condition checks the time from the start time to the first calender event.
            if i == 0:
            
                free_time_end = event["start"].get("dateTime", event["start"].get("date"))
                converted_free_time_end = datetime.fromisoformat(free_time_end)
                
                FreeTimeStart = converted_start_time
                FreeTimeEnd = converted_free_time_end.replace(tzinfo=None)
                
                #Checks if the break is long enough to be considered enough free time for surfing
                Start_End_Delta = FreeTimeEnd - FreeTimeStart
                Duration_Minutes = Start_End_Delta.total_seconds()/60
                
                if Duration_Minutes >= minimum_duration:
                    freetime = {'start':FreeTimeStart,'end':FreeTimeEnd,'delta':FreeTimeEnd - FreeTimeStart}
                    FreeTimes.append(freetime)
                
            #this condition is for last calender and the the free time between end of the last calender event and the end time of the time fram im looking at.
            elif i == len(calendar_events)-1:
            
                free_time_start = event["end"].get("dateTime", event["end"].get("date"))
                converted_free_time_start = datetime.fromisoformat(free_time_start)
                
                FreeTimeStart = converted_free_time_start.replace(tzinfo=None)
                FreeTimeEnd = converted_end_time
                
                #Checks if the break is long enough to be considered enough free time for surfing
                Start_End_Delta = FreeTimeEnd - FreeTimeStart
                Duration_Minutes = Start_End_Delta.total_seconds()/60
                
                if Duration_Minutes >= minimum_duration:
                    freetime = {'start':FreeTimeStart,'end':FreeTimeEnd,'delta':FreeTimeEnd - FreeTimeStart}
                    FreeTimes.append(freetime)
                    
            #This checks free time in between events by comparing event(i) endtime and event(i+1) start time.
            else:
                event_2 = calendar_events[i+1]
                
                free_time_start = event["end"].get("dateTime", event["end"].get("date"))
                converted_free_time_start = datetime.fromisoformat(free_time_start)
            
                free_time_end = event_2["start"].get("dateTime", event_2["start"].get("date"))
                converted_free_time_end = datetime.fromisoformat(free_time_end)
                
                FreeTimeStart = converted_free_time_start.replace(tzinfo=None)
                FreeTimeEnd = converted_free_time_end.replace(tzinfo=None)
                
                #Checks if the break is long enough to be considered enough free time for surfing
                
                Start_End_Delta = FreeTimeEnd - FreeTimeStart
                Duration_Minutes = Start_End_Delta.total_seconds()/60
                
                if Duration_Minutes >= minimum_duration:
                    freetime = {'start':FreeTimeStart,'end':FreeTimeEnd,'delta':FreeTimeEnd - FreeTimeStart}
                    FreeTimes.append(freetime)

    return FreeTimes
    
def Spot_Surfab_And_Free_Time(All_Surfable_Spots,Free_Times):
    Free_And_Surfable = []
    

    for spot in All_Surfable_Spots:
        spot_data = spot['data']
        
        more_data = []
        
        for time in Free_Times:
        
            start_time =  time["start"]
            end_time = time["end"]
            
            spot_times_data = []
            
            for log in spot_data:
                if start_time <= log['timestamp_dt'] <= end_time:
                    spot_times_data.append(log)
            if len(spot_times_data) !=0:
                more_data.append(spot_times_data)
        Free_And_Surfable.append({'name':spot['name'],'data': more_data})
            
    


    return Free_And_Surfable

def main():

  creds = authenticate_google_calendar()

  try:
    service = build("calendar", "v3", credentials=creds)
    
    

    now = datetime.utcnow().isoformat()
    two_days_later = (datetime.utcnow() + timedelta(days=2)).isoformat()


    events = get_calendar_events(service, now, two_days_later)

    if not events:
      print("No upcoming events found.")
      
      # this condition is fine I need to add a case where there's no need to check for free times.
      return
      
    # Specify the minimum duration in min for surf session
    min_duration = 120
    
    #Finds All FreeTimes in calender longer than the minimum duration necessary.
    #This should only be done if there are any events in the calender.
    Free_Times = get_free_time_slots(events,now,two_days_later,min_duration)
    
    #prints freetime slots in free times with start time end time and the delta between the two
    print("These are all the free time slots:")
    for freetime in Free_Times:
        print("start:",freetime['start'],"end:",freetime['end'],"delta:",freetime['delta'])


    All_Surfable_Spots = Surf_Functionality()
    
    
    # compares surfable times with when I have free time and returns when there's overlap
    Filtered_Surf_Times = Spot_Surfab_And_Free_Time(All_Surfable_Spots,Free_Times)
    
    
    #this prints the times each surfspot has surfable conditions durring my freetime slots.
    
    print("****These are all the surfable hours for each surfspot****")
    
    for Spots in Filtered_Surf_Times:
        name = Spots['name']
        data = Spots['data']
        
        surfable_hours_df = pd.DataFrame(data)
        print("\n\n***",name,"***\n")
        if len(Spots["data"]) != 0:
            num=0
            for d in data:
                num +=1
                print("\nPossible Surf Sesh #",num)
                
                surfable_hours_df = pd.DataFrame(d)
                print(surfable_hours_df[['timestamp_dt', 'surf_min', 'surf_max']])
            
           
        else:
            print("There are no surfable hours")
        
        

  except HttpError as error:
    print(f"An error occurred: {error}")





if __name__ == "__main__":
  main()

