#-----------------------------------------------------------------------------------#
#-------------------------------Import and stuff------------------------------------#
#-----------------------------------------------------------------------------------#

import pandas as pd
pd.set_option('display.precision',1)
pd.set_option('display.max_rows',50)
pd.set_option('display.max_columns',10)
#pd.set_option('display.width',1000)
from pandas.plotting import scatter_matrix

import numpy as np
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import folium
from folium.features import DivIcon
import webbrowser
from folium import IFrame
import base64

import branca
import branca.colormap as cm

from html2image import Html2Image
from PIL import Image

import pickle

import seaborn as sns
from scipy.stats import linregress
import scipy


#-----------------------------------End Imports-------------------------------------#



#-----------------------------------------------------------------------------------#
#-------------------------------Define Functions------------------------------------#
#-----------------------------------------------------------------------------------#
  
#----------------------END MY FUNCTIONS---------------------------------------------#



#-----------------------------------------------------------------------------------#
#-------------------------Get data--------------------------------------------------#
#-----------------------------------------------------------------------------------#


####hazardous waste
hazardous_waste=pd.read_csv('hazardous_waste_clean.csv')
#clean nans
hazardous_waste=hazardous_waste.dropna()

####hazardous waste
#superfunds=pd.read_csv('superfunds.csv')
#clean nans
#superfunds=superfunds.dropna()




####To load in python
f=open('PurpleAir_KC_v6.pkl','rb')
var_list=pickle.load(f)
f.close()
all_df=var_list[0]
meta=var_list[1]


stn_id_pa=meta[:,0]
lons_pa=meta[:,1]
lats_pa=meta[:,2]




#---------------------EPA
f=open('KC_pm25_EPA.pkl','rb')
var_list=pickle.load(f)
f.close()
df_pm25_epa=var_list[0]
metadata=var_list[1]



#Parse all metadata
N_stns=metadata['Header'][0]['rows']
AQS_ID=np.empty(N_stns,dtype=int)
lats=np.empty(N_stns)
lons=np.empty(N_stns)
starttime=np.empty(N_stns,dtype='datetime64[D]')
endtime=np.empty(N_stns,dtype='datetime64[D]')

for i in range(0,N_stns):
  #station id info
  state=metadata['Data'][i]['state_code']
  county=metadata['Data'][i]['county_code']
  site=metadata['Data'][i]['site_number']
  
  #create one ID from those three
  AQS_ID[i]=int(state+county+site)
  
  #associated meta data
  lats[i]=metadata['Data'][i]['latitude']
  lons[i]=metadata['Data'][i]['longitude']
  
  start_date=np.array(metadata['Data'][i]['open_date'],dtype='datetime64')
  end_date=np.array(metadata['Data'][i]['close_date'],dtype='datetime64')
  
  starttime[i]=start_date
  #check to see if still open, which gives no close date (NaT)
  if ~np.isnat(end_date):
    endtime[i]=end_date
  else:
    endtime[i]=np.array('2022-01-01',dtype='datetime64') #set as one day after call?
    #print('there is no end')
    
  
#some stations repeat, so drop duplicates
AQS_ID_unique,b,c,d=np.unique(AQS_ID,return_index=True,return_inverse=True,return_counts=True)

#use only uniques
stn_id=AQS_ID[b]
lats=lats[b]
lons=lons[b]
starttime=starttime[b]
endtime=endtime[b]



#REWORK START AND END TIME!!!
for stns in all_df.columns:
  #all_df['pm25_480850005'].first_valid_index()
  #all_df['pm25_480850005'].last_valid_index()
  
  index=np.where(stn_id==float(stns[5:14]))
  starttime[index]=all_df[stns].first_valid_index()
  endtime[index]=all_df[stns].last_valid_index()


#---------------END EPA---------------#









#-----------------------------End Get Data------------------------------------------#


#Loop through all for animation
#map=folium.Map(location=[39.1, -94.6], zoom_start=10)

'''
for i in range(0,len(lons)):
  folium.Marker([lats[i],lons[i]]).add_to(map)
  
  folium.map.Marker([lats[i],lons[i]],
                    icon=DivIcon(icon_size=(150,36),icon_anchor=(0,0),
                    html='<div style="font-size: 12pt">%s</div>' % int(stn_id[i]),)).add_to(map)

map.save("map_1.html")
webbrowser.open("map_1.html")

hti=Html2Image(output_path='C:\\a_Projects\\air_pollution\\purple_air_get_auto\\',
                custom_flags=['--virtual-time-budget=10000', '--hide-scrollbars'],
                size=(1200,900))
hti.screenshot(html_file='map_1.html', save_as='map_purpleair.png')
'''

#---------Create map
#where to save
map_dir='C:\\a_Projects\\CleanAirNow_website\\AQ_map_python_v0\\'
#Starting map view/zoom
m=folium.Map(location=[39.1, -94.6], zoom_start=10)
#Different backgrounds
folium.TileLayer("Esri_WorldImagery").add_to(m)
#folium.TileLayer("Esri_WorldGrayCanvas").add_to(m)
folium.TileLayer("Esri_WorldStreetMap").add_to(m)
folium.TileLayer(show=False).add_to(m)



#---------Add layers
pa_rt=folium.FeatureGroup(name="Realtime-ish Purple Air PM2.5",show=False).add_to(m)
pa=folium.FeatureGroup(name="Historical Purple Air PM2.5",show=False).add_to(m)
epa=folium.FeatureGroup(name="Historical EPA PM2.5",show=False).add_to(m)
hw=folium.FeatureGroup(name="Hazardous Waste Sites",show=False).add_to(m)
info=folium.FeatureGroup(name="Current and Past EJ Projects",show=False).add_to(m)
bad=folium.FeatureGroup(name="Bad stuff",show=False).add_to(m)
wxr=folium.FeatureGroup(name="Weather stuff",show=False).add_to(m)

#put them on map
folium.LayerControl('topleft', collapsed=False).add_to(m)


#--ADD Hazardous Waste Sites
for index, location_info in hazardous_waste.iterrows():
    folium.Marker([location_info["LATITUDE"],location_info["LONGITUDE"]],
                  popup=location_info["NAME"],
                  icon=folium.Icon(prefix='fa',icon='thumbs-down',color='red',fill_opacity=0.5)).add_to(hw)



#--ADD PurpleAir Historical
for i in range(0,len(lons_pa)):
  #deselect for clean map
  if stn_id_pa[i]!=127623:
    #---Local image imbed
    encoded = base64.b64encode(open('testwindrose.png', 'rb').read())
    html = '<img src="data:image/png;base64,{}">'.format
    iframe = IFrame(html(encoded.decode('UTF-8')), width=440, height=390)
    popup = folium.Popup(iframe, max_width=400)

    folium.Marker([lats_pa[i],lons_pa[i]],popup=popup,
                   icon=folium.Icon(icon='marker',color='purple')).add_to(pa)    

#---Below works
#    folium.Marker([lats_pa[i],lons_pa[i]],
#                   icon=folium.Icon(icon='marker',color='purple')).add_to(pa)
    
    folium.map.Marker([lats_pa[i],lons_pa[i]],
                       icon=DivIcon(icon_size=(150,36),icon_anchor=(0,0),
                       html='<div style="font-size:14pt;font-weight:bold;color:purple">%s</div>' % int(stn_id_pa[i]),)).add_to(pa)


#--ADD EPA Historical
for i in range(0,len(lons)):
  #deselect for clean map
  if stn_id[i]!=127623:
    folium.Marker([lats[i],lons[i]],
                   icon=folium.Icon(icon='marker',color='green')).add_to(epa)
    
    folium.map.Marker([lats[i],lons[i]],
                       icon=DivIcon(icon_size=(150,36),icon_anchor=(0,0),
                       html='<div style="font-size:14pt;font-weight:bold;color:purple">%s</div>' % int(stn_id[i]) )).add_to(epa)


#---ADD Realtime Purple Air
html = """
	<div id='PurpleAirWidget_181075_module_PM25_conversion_C0_average_0_layer_satellite'>Loading PurpleAir Widget...</div>
	<script src='https://www.purpleair.com/pa.widget.js?key=1CY99LJ18QGJRCLS&module=PM25&conversion=C0&average=0&layer=satellite&container=PurpleAirWidget_181075_module_PM25_conversion_C0_average_0_layer_satellite'></script>
    """

iframe=branca.element.IFrame(html=html,width=300,height=460)
popup=folium.Popup(iframe)

folium.Marker([38.9,-94.7],popup=popup,lazy=True).add_to(pa_rt)



#-----TEST CIRCLE REALTIME
epa_pm25_list=list(df_pm25_epa)

col_labels=[0,5,10,15,20,25,30,35,40,50];
col_hex=["#68FF42", "#FFFF54", "#EF8432", "#EA3323",
                "#8C1A4B", "#8C1A4B", "#721324", "#721324",
                "#721324", "#721324"];
#pm25_colormap=cm.LinearColormap(colors=['red','lightblue'], index=[0,15],vmin=0,vmax=15)
pm25_colormap=cm.StepColormap(col_hex,col_labels,vmin=0,vmax=15,
                              tick_labels=col_labels,caption='PM2.5 Color Scale')


for i in range(0,len(lons)):
  try:
    if ~np.isnan(df_pm25_epa['pm25_'+str(stn_id[i])][-1]):
      display(df_pm25_epa['pm25_'+str(stn_id[i])][-1])
      
      folium.CircleMarker([lats[i],lons[i]],radius=20,color='black',
                          fill=True,fill_opacity=0.6,
                          #fill_color='red'
                          fill_color=pm25_colormap(df_pm25_epa['pm25_'+str(stn_id[i])][-1])
                         ).add_to(pa_rt)
        
      folium.map.Marker([lats[i],lons[i]],
                       icon=DivIcon(icon_size=(150,36),icon_anchor=(12,14),
                       html='<div style="font-size:16pt;font-weight:bold;color:black">%s</div>' % str(int(df_pm25_epa['pm25_'+str(stn_id[i])][-1])).zfill(2) )).add_to(pa_rt)
  except:
    display('0')




#transform:rotate(45deg)

#---ADD Weather
#folium.Marker([39.1,-94.5],
#              #icon=folium.Icon(icon='marker',color='green')).add_to(wxr)
#              icon=folium.Icon(prefix='fa',icon='thumbs-down',color='black',fill_opacity=0.5)).add_to(wxr)


#html = '''
#<div style="size: 300px; background-color: lightblue; transform:rotate(45deg)">
#<i class="fa-solid fa-arrow-left"> test </i>
#</div>
#'''
#folium.map.Marker(location=[39.1,-94.5],
#                  icon=DivIcon(icon_size=(100,100),icon_anchor=(0,0),html=html )
#                 ).add_to(wxr)

import folium.plugins as plugins
#folium.plugins.BoatMarker(
#    location=[39.1,-94.5], heading=-20, wind_heading=46, wind_speed=25, color=""
#).add_to(wxr)




icon_wxr=folium.plugins.BeautifyIcon(
#    icon="arrow-up", border_color="#b3334f", text_color="#b3334f", icon_shape="triangle"
    icon="long-arrow-up",spin=True
)

'''
thetmpc=32
folium.Marker(location=[39.1,-94.5], popup="ASOS",icon=icon_wxr).add_to(wxr)
folium.map.Marker([lats[i],lons[i]],
                 icon=DivIcon(icon_size=(150,36),icon_anchor=(0,0),
                 html='<div style="font-size:24pt;font-weight:bold;color:black">%s</div>' % f" {thetmpc}{chr(176)}" )).add_to(wxr)
'''

thetmpc=32
kw = {"prefix": "fa", "color": "black", "icon": "arrow-up"}
an_icon=folium.Icon(angle=55,**kw)
folium.Marker(location=[39.2,-94.5],icon=an_icon,tooltip=str(55)).add_to(wxr)
folium.map.Marker([39.2,-94.5],
                 icon=DivIcon(icon_size=(150,36),icon_anchor=(0,0),
                 html='<div style="font-size:24pt;font-weight:bold;color:black">%s</div>' % f" {thetmpc}{chr(176)}" )).add_to(wxr)



thetmpc=36
kw = {"prefix": "fa", "color": "black", "icon": "arrow-up"}
an_icon=folium.Icon(angle=25,**kw)
folium.Marker(location=[39.1,-94.6],icon=an_icon,tooltip=str(25)).add_to(wxr)
folium.map.Marker([39.1,-94.6],
                 icon=DivIcon(icon_size=(150,36),icon_anchor=(0,0),
                 html='<div style="font-size:24pt;font-weight:bold;color:black">%s</div>' % f" {thetmpc}{chr(176)}" )).add_to(wxr)


'''
url="https://leafletjs.com/examples/custom-icons/{}".format
icon_image = url("leaf-red.png")
shadow_image = url("leaf-shadow.png")

icon = folium.CustomIcon(
    icon_image,
    icon_size=(38, 95),
    icon_anchor=(22, 94),
    shadow_image=shadow_image,
    shadow_size=(50, 64),
    shadow_anchor=(4, 62),
    popup_anchor=(-3, -76),
)

folium.Marker(
    location=[39.2,-94.6], icon=icon, popup="Mt. Hood Meadows"
).add_to(wxr)
'''











#---Add image in top right corner
#from folium.plugins import FloatImage
#url = (
#    "https://raw.githubusercontent.com/ocefpaf/secoora_assets_map/"
#    "a250729bbcf2ddd12f46912d36c33f7539131bec/secoora_icons/rose.png"
#)
#FloatImage(url, top=5, right=5).add_to(m)




#---ADD projects, etc
#https://storymaps.arcgis.com/stories/2884a980a61d4e3ca699bb1e4d646b0e
html_EJarmourdale = """
<a href="https://storymaps.arcgis.com/stories/2884a980a61d4e3ca699bb1e4d646b0e" target="_blank" rel="noopener noreferrer">Environmental Justice Analysis in Armourdale</a>
    """
iframe_EJarmourdale=branca.element.IFrame(html=html_EJarmourdale,width=300,height=100)

folium.Circle(
    location=[39.09,-94.635],
    radius=2500,
    fill=True,
    popup=folium.Popup(iframe_EJarmourdale),
).add_to(info)





#https://osf.io/65xjt?view_only=e8239e511d0f4413ad6d2b88fc1d768c
#https://www.kansashealthmatters.org/content/sites/kansas/Reports/CHC_HeatReport_1228.pdf
html_JoWy_Heat = """
<a href="https://osf.io/65xjt?view_only=e8239e511d0f4413ad6d2b88fc1d768c" target="_blank" rel="noopener noreferrer">Results from the 2023 urban heat mapping campaign</a>
    """
iframe_JoWy_heat=branca.element.IFrame(html=html_JoWy_Heat,width=300,height=100)

folium.Circle(
    location=[39.15,-94.78],
    radius=5000,
    fill=True,
    color='red',
    popup=folium.Popup(iframe_JoWy_heat),
).add_to(info)



#---Add Other bad stuff

#Fire
# 39.076797,-94.639586
#https://www.kansascity.com/news/local/article275587436.html
#https://www.kansascity.com/latest-news/jt0ye/picture275592146/alternates/FREE_1140/KCM_KCKADVANTAGEMETALSFIRE0%20(2)
#https://www.kansascity.com/latest-news/oa1ek1/picture275589916/alternates/FREE_1140/IMG_6127.jpeg
html_recycle_fire = """
<h2>Recycling center fire (May 2023)</h2><p>
(Click image for link)<p>
<a href="https://www.kansascity.com/news/local/article275587436.html" target="_blank" rel="noopener noreferrer">
<img src="https://www.kansascity.com/latest-news/jt0ye/picture275592146/alternates/FREE_1140/KCM_KCKADVANTAGEMETALSFIRE0%20(2)" alt="Recycling center fire (May 2023)" width="400" height="200" border="2">
</a>
    """


iframe_recycle_fire=branca.element.IFrame(html=html_recycle_fire,width=420,height=320)

folium.Marker([39.076797,-94.639586],popup=folium.Popup(iframe_recycle_fire,show=True,sticky=True)).add_to(bad)

folium.map.Marker([39.076797,-94.639586],
                   icon=DivIcon(icon_size=(150,36),icon_anchor=(60,0),
                   html='<div style="font-size:18pt;font-weight:bold;color:black">%s</div>' % 'Recycle Fire' )).add_to(bad)








#-----------------------------------------------------------------------------#
#-------------------Other information
#-----------------------------------------------------------------------------#

col_labels=[0,50,100,150,200,250,300,350,400,500];
col_hex=["#68FF42", "#FFFF54", "#EF8432", "#EA3323",
                "#8C1A4B", "#8C1A4B", "#721324", "#721324",
                "#721324", "#721324"];


step=cm.StepColormap(
 col_hex,
 col_labels,
 vmin=0, vmax=500,
 tick_labels=col_labels,
# text_color='red',
 caption='PM2.5 Color Scale'
)

step.add_to(m)


#more_info=branca.element.IFrame('Hello World')
#more_info.add_to(m)

#iframe=folium.IFrame(html, width=200, height=200)
#popup=folium.Popup(iframe)
#marker=folium.Marker([39.0,-94.8],popup,draggable=True).add_to(m)
#m._repr_html_()


map_title="Draft RISE4EJ Map v0"
title_html=f'<h1 style="position:absolute;z-index:100000;left:20vw" >{map_title}</h1>'
m.get_root().html.add_child(folium.Element(title_html))





info_html = """
<style> 
#info_style {
  position: fixed;
  bottom: 0;
  right: 0;
  z-index: 9999;
  width: 25%;
  margin-right: 10px;
  margin-bottom: 10px;
  order-radius: 5px;
  border: 1px solid black;
  box-shadow: 3px 3px 4px grey;
  background: whitesmoke;
  background-color: lightblue
}
</style>
<div class="bottomleft" id="info_style">
  <font size="2">
  <strong>Air Quality:</strong>
  <p>
      The sensor data displayed here is collected by
      <a href="https://www2.purpleair.com" target="_blank">PurpleAir</a> Air Quality
      Sensors.<br><br>
      The numerical reports are based on the <strong>US EPA PM2.5 Air Quality Index
          (AQI)</strong>. The AQI
      is a number used by goverment agencies to communicate how polluted the air currently is or
      how polluted
      it is forecast to become.<br><br>
      Particulate Matter (PM) 2.5 refers to the pollutants which are 2.5 micrometers or smaller.
  </p>
  <strong>Hazardous Waste Sites:</strong>
  <p>

      Data for Superfund sites can be found
      <a href="https://www.epa.gov/superfund/superfund-data-and-reports" target="_blank">here</a>
  </p>
  </font>
</div>
"""
m.get_root().html.add_child(folium.Element(info_html))

#Trim
        # <em>Superfund sites</em> are EPA-designated locations of pollution that require a long-term
        # response
        # to clean up hazardous material contaminations. <em>Treatment, Storage, and Disposal
        #     Facilities (TSDF)</em> are
        # locations that produce some form of waste which needs to be disposed of according to strict
        # regulations.<br><br>        and TSDF data can be found
        # <a href="https://enviro.epa.gov/facts/rcrainfo/search.html" target="_blank">here</a>.




'''
from IPython.display import display
from ipywidgets import Dropdown

def dropdown_eventhandler(change):
    print(change.new)

option_list = (1, 2, 3)
dropdown = Dropdown(description="Choose one:", options=option_list)
dropdown.observe(dropdown_eventhandler, names='value')
display(dropdown)
'''




m.save("map_1.html")
webbrowser.open("map_1.html")

hti=Html2Image(output_path=map_dir,
               custom_flags=['--virtual-time-budget=10000', '--hide-scrollbars'],
               size=(1200,900))
hti.screenshot(html_file='map_1.html', save_as='map_pa.png')

#Crop
im=Image.open(map_dir+'\\map_pa.png')
im1=im.crop((300,200,900,800))
im1.save(map_dir+'\\map_pa.png')
  
  





'''
#Gantt-like chart for data availability
#station_info_size=np.shape(response.json()['data'])
getnames=list(all_df)

plt.figure(figsize=(10,7))
plt.xlim(pd.Timestamp(2018,1,1,0,0,0),pd.Timestamp(2022,6,1,0,0,0))
plt.ylim(0,(len(getnames)/4)+2)
labels=[]
offset=0
for i in range(0,int(len(getnames)/4)):
  plt.plot(offset+all_df[getnames[i]]/all_df[getnames[i]],'k.')
  offset=offset+1
  #get labels
  labels.append(getnames[i])
  
plt.yticks(range(1,1+len(labels)),labels)

plt.gca().xaxis.set_major_locator(mdates.YearLocator())
plt.gca().xaxis.set_major_formatter(mdates.ConciseDateFormatter(plt.gca().xaxis.get_major_locator()))

plt.gca().xaxis.set_minor_locator(mdates.MonthLocator(bymonth=(1,7)))
plt.xticks(rotation=-90)
plt.show()

'''




