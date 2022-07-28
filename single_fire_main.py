from importlib.resources import open_binary
import os
import pickle
from urllib import response
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import sqlite3
import time
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image

fw_title = "Flavor Wave"
nsfwf_title = "Me"

def generate_chart(data,variable):
    layout = go.Layout(
        title = variable,
        title_x = 0.5,
        yaxis = {
            'showgrid':False,
            'ticksuffix':"  ",
            'title':"",
            'rangemode':"nonnegative",
            'linecolor':"white",
            'linewidth':2,
        },
        xaxis = {
            'showgrid':False,
            'title':"",
            'showticklabels':False,
            'linecolor':"white",
            'linewidth':2
        },
        showlegend = True,
        legend_title = "",
        font = {
            'family': "'Helvetica'"
        },
        width = 350,
        height = 280,
        plot_bgcolor = "rgba(0,0,0,0)",
        margin = go.layout.Margin(r=30, b=20, l=0,t=50)
    )

    color_discrete_map = {
        fw_title:'#fe6a76',
        nsfwf_title:'#a7a8e0'
    }

    fig = px.line(data, template="plotly_dark", color_discrete_map=color_discrete_map)
    fig.update_layout(
        layout
    )
    return fig

def writeEntry(response_body):
    stat_dict = {}
    for item in response_body['items']:
        if item['id'] == "UCJRchI8cOT8hGQBDhBohGRw":
            stat_dict["fw"] = {"view_count": item["statistics"]['viewCount'], "sub_count": item["statistics"]['subscriberCount']}
        if item['id'] == "UCMqylReKbMU8dnscaLmgj1w":
            stat_dict["n7fwf"] = {"view_count": item["statistics"]['viewCount'], "sub_count": item["statistics"]['subscriberCount']}

    
    conn = sqlite3.connect("fw.db")
    c = conn.cursor()
    data = (time.time(),getViews('UUJRchI8cOT8hGQBDhBohGRw'), getViews('UUMqylReKbMU8dnscaLmgj1w'), stat_dict['fw']['sub_count'], stat_dict['n7fwf']['sub_count'])
    c.execute("""INSERT INTO entries VALUES (?,?,?,?,?)""", data)
    conn.commit()
    conn.close()

    return stat_dict

def getData():
    conn = sqlite3.connect("fw.db")
    c = conn.cursor()
    c.execute("SELECT * FROM entries order by time ASC")
    ret = c.fetchall()
    conn.close()
    return ret

def dataIsDifferent():
    conn = sqlite3.connect("fw.db")
    c = conn.cursor()
    c.execute("SELECT fwViews, n7fwfViews, fwSubs, n7fwfSubs FROM entries order by time DESC")
    entries = c.fetchmany(2)
    conn.close()
    return entries[0] != entries[1]

def dbWipe():
    conn = sqlite3.connect("fw.db")
    c = conn.cursor()
    c.execute("delete FROM entries")
    conn.commit()
    conn.close()

def getSubsDict():
    ret = {
        fw_title:[],
        nsfwf_title:[]
    }
    for x in getData():
        ret[fw_title].append(x[3])
        ret[nsfwf_title].append(x[4])
    return ret

def getViewsDict():
    ret = {
        fw_title:[],
        nsfwf_title:[]
    }
    for x in getData():
        ret[fw_title].append(x[1])
        ret[nsfwf_title].append(x[2])
    return ret

def getUploads(channelId):
    uploadsRequest = youtube.playlistItems().list(
        part='snippet',
        playlistId=channelId,
        maxResults=100
    )
    return uploadsRequest.execute()

def getViews(channelId):
    uploadsStatistics = youtube.videos().list(
        part='statistics',
        id=[x['snippet']['resourceId']['videoId'] for x in getUploads(channelId)['items']]
    )
    return sum([int(x['statistics']['viewCount']) for x in uploadsStatistics.execute()['items']])

credentials = None

# token.pickle stores the user's credentials from previously successful logins
if os.path.exists('token.pickle'):
    print('Loading Credentials From File...')
    with open('token.pickle', 'rb') as token:
        credentials = pickle.load(token)
        # print(credentials)


# If there are no valid credentials available, then either refresh the token or log in.
if not credentials or not credentials.valid:
    if credentials and credentials.expired and credentials.refresh_token:
        print('Refreshing Access Token...')
        credentials.refresh(Request())
    else:
        print('Fetching New Tokens...')
        flow = InstalledAppFlow.from_client_secrets_file(
            'client_secret.json',
            scopes=[
                'https://www.googleapis.com/auth/youtube.readonly',
                'https://www.googleapis.com/auth/youtube.upload',
                'https://www.googleapis.com/auth/youtube',
                'https://www.googleapis.com/auth/youtube.force-ssl'
            ]
        )

        flow.run_local_server(port=8080, prompt='consent',
                              authorization_prompt_message='')
        credentials = flow.credentials

        # Save the credentials for the next run
        with open('token.pickle', 'wb') as f:
            print('Saving Credentials for Future Use...')
            pickle.dump(credentials, f)

youtube = build('youtube','v3',credentials=credentials)

request = youtube.channels().list(
    part=['statistics'],
    id=['UCJRchI8cOT8hGQBDhBohGRw','UCMqylReKbMU8dnscaLmgj1w']
)
writeEntry(request.execute())

if(dataIsDifferent()):
    print("updating table")
    generate_chart(getViewsDict(), "Channel Views").write_image('fig1.png')
    generate_chart(getSubsDict(), "Subscribers").write_image('fig2.png')

    background = Image.open("Adjusted.png")
    fig1 = Image.open("fig2.png")
    fig2 = Image.open("fig1.png")

    background.paste(fig2, (55,435), fig2)
    background.paste(fig1, (1643,435), fig1)

    background.save("combined.png")

    request = youtube.channelBanners().insert(media_body='combined.png')
    request.execute()

