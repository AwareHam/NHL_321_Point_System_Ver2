import json
from pymongo import MongoClient
from bs4 import BeautifulSoup
from urllib.request import urlopen
from html.parser import HTMLParser
import numpy as np
import pandas as pd


url = 'https://www.hockey-reference.com/leagues/NHL_2024_standings.html'
soup = BeautifulSoup(urlopen(url), "html.parser")


# Find the proper table using the caption tag
for caption in soup.find_all('caption'):
    if caption.get_text() == 'Expanded Standings Table':
        table = caption.find_parent('table', {"id":"standings"})

#Table data into one large array
all_teams = []
#Grab all the data
for row in table.find_all('tr'):
    for cell in row.find_all('td'):
        all_teams.append(cell.text)


#divide the all_teams data into their own arrays
def teamsplitter(l, n):
    # For item i in a range that is a length of l,
    for i in range(0, len(l), n):
        # Create an index range for l of n items:
        yield l[i:i+n]

#21 columns in chart
all_teams = list(teamsplitter(all_teams,21))
#Data->numpy
all_teams = np.array(all_teams)
#numpy-> Pandas DataFrame
teamtable = pd.DataFrame(all_teams)
# print(teamtable)
#clean data & rename headers
teamtable = teamtable.drop([4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20],axis=1)
teamtable = teamtable.rename(columns={0:"team",1:"Overall",2:"Shootout",3:"Overtime"})

# Striping out the strings of the records

teamname = teamtable.drop(["Overall","Shootout","Overtime"],axis=1)
Overall_math = teamtable.Overall.str.split("-",expand=True).rename(columns={0:"wins",1:"loss",2:"OT_L"}).astype(int)
Shootout_math = teamtable.Shootout.str.split("-",expand=True).drop([1],axis=1).rename(columns={0:"SOWins"}).astype(int)
Overtime_math = teamtable.Overtime.str.split("-",expand=True).drop([1],axis=1).rename(columns={0:"OTWins"}).astype(int)

#Join math tables
pts_math = teamname.join(Overall_math)
pts_math = pts_math.join(Shootout_math)
pts_math = pts_math.join(Overtime_math)

# print(pts_math)

# Math to get all the pts totals...(Keeping to show the work)
pts_math['OT_W'] = pts_math.SOWins + pts_math.OTWins
pts_math['true_Wins'] = pts_math.wins - pts_math.OT_W
pts_math['True_Wins_Pts'] = pts_math.true_Wins*3
pts_math['OT_W_Pts'] = pts_math.OT_W*2
pts_math['OT_L_Pts'] = pts_math.OT_L*1

# THE NEW TOTAL POINTS!!
pts_math['new_Record']= pts_math.true_Wins.astype(str).str.cat([pts_math.OT_W.astype(str),pts_math.OT_L.astype(str),Overall_math.loss.astype(str)],sep='-')
pts_math['PTS_Total']= pts_math.True_Wins_Pts+pts_math.OT_W_Pts+pts_math.OT_L_Pts

pts_math['current_Points']=(pts_math.wins*2)+(pts_math.OT_L)
# clean for export
pts_math = pts_math.drop(['OT_W', 'True_Wins_Pts', 'OT_W_Pts', 'OT_L_Pts'], axis=1)
pts_math = pts_math.rename(columns={"OT_L":"overtime_Loss","SOWins":"shoot_Out_Wins","OTWins":"overtime_Wins","PTS_Total":"points"})


pts_math['current_Rank'] = pts_math['current_Points'].rank(ascending=False)

pts_math['new_Rank'] = pts_math['points'].rank(ascending=False)
pts_math = pts_math.sort_values(by=["points"],ascending=False)

# pts_math = pts_math.set_index('Team')
# print(pts_math)

team_props = pd.read_json('teams.json',typ='frame')
# print(team_props)

finish_table = pts_math.join(team_props,on='team')
# print(finish_table)
finish_table = finish_table.set_index('abb')
# print(finish_table)




# print(pts_math)
#export .csv file
# pts_math.to_csv('321-Point-Standings.csv',header=True,index=False)

#export .html file
#pts_math.to_html("321-Point-Standings.html",header=True,index=False,table_id="2019_Standings")

# export .json file
finish_table.to_json('standings.json')


print("x")
