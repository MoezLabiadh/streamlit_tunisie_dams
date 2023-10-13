
import pandas as pd
import plotly.express as px
import streamlit as st
import folium
from folium.plugins import MarkerCluster, MiniMap
from streamlit_folium import folium_static


@st.cache_data
def input_data(url):
    df= pd.read_csv(url)
    
    df['Region']= 'Nord'
    df.loc[df['id_barrage'].between(17, 24), 'Region'] = 'Centre'
    df.loc[df['id_barrage'].between(25, 30), 'Region'] = 'CapBon'

    fix_coords = {
        'sarrat': {'Latitude': 35.832308, 'Longitude': 8.443517},
        'harka': {'Latitude': 37.221177, 'Longitude': 9.402368},
        'melah': {'Latitude': 37.076438, 'Longitude': 9.446414}
    }

    for location, values in fix_coords.items():
        df.loc[df['Nom_Fr'] == location, ['Latitude', 'Longitude']] = values['Latitude'], values['Longitude']
    
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    
    return df


@st.cache_data
def create_map_df (df):
    df_mp = df.groupby(['Nom_Fr', 'Region']).first().reset_index()
    df_mp = df_mp[['Nom_Fr', 'Nom_Ar', 'Region', 'Cap_tot_act', 'stock', 'Date',
                   'Annee_prod','Latitude', 'Longitude']]
    
    return df_mp


def create_map(df):
    m= folium.Map(location=[35.5,9.5])
    bounds = [[df['Latitude'].min(), df['Longitude'].min()], 
              [df['Latitude'].max(), df['Longitude'].max()]]
    
    m.fit_bounds(bounds)
    
    satellite_url = 'https://server.arcgisonline.com/ArcGIS/rest/services/'\
                    'World_Imagery/MapServer/tile/{z}/{y}/{x}'
    satellite_attribution = 'Tiles &copy; Esri'
    folium.TileLayer(
        tiles=satellite_url,
        name='Imagery',
        attr=satellite_attribution,
        overlay=False,
        control=True).add_to(m)
    
    marker_cluster = MarkerCluster(name='Dams of Tunisia').add_to(m)


    for idx, row in df.iterrows():
        lat, lon = row['Latitude'], row['Longitude']
        dam_name_fr = row['Nom_Fr']
        dam_name_ar = row['Nom_Ar']
        cap = round(row['Cap_tot_act'],1)
        yr_prod= row['Annee_prod']
        stock = round(row['stock'],1)
        date= row['Date']
        fill = round((stock/cap)*100,1)
        popup_html = f"<b>Dam Name (FR)</b>: {dam_name_fr}<br>\
                       <b>Dam Name (AR)</b>: {dam_name_ar}<br>\
                       <b>Construction Year</b>: {yr_prod}<br>\
                       <b>Total Capacity</b>: {cap} Mm3<br>\
                       <b>Current Stock</b>: {stock} Mm3 ({date}) <br>\
                       <b>Current Filling Rate</b>: {fill} % ({date})"
        popup = folium.Popup(popup_html, max_width=300)
        folium.Marker([lat, lon], popup=popup).add_to(marker_cluster)
        
    #minimap = MiniMap(position="bottomleft")
    #m.add_child(minimap)
    
    folium.LayerControl().add_to(m)
    
    return m


if __name__==__name__:
    
    #---------------Page Settings-------------#
    st.set_page_config(page_title='Tunisian Dams',
                       page_icon=':bar_chart:',
                       layout= 'wide')

    #---------------Some CSS styling-----------------#    
    st_style = """
            <style>
            .stApp {margin-top: -100px;}
            
            h1 {font-size: 35px;}
            h2 {font-size: 20px;}
            h3 {font-size: 10px;}

            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
    st.markdown(st_style, unsafe_allow_html=True)
    
    
    #---------------Prepare inputs----------------#
    url= r'https://data.gov.tn/cms/download/38a44692-16a9-4974-bf20-e849d193e929/'\
         r'34a59c57-c0b8-495e-b8a9-9bed28f19bed/aHR0cDovL2FncmlkYXRhLnRuL2RhdGFzZXQvNGJ'\
         r'iM2Q2NjgtNmM5Yi00MDcyLWFkNTYtMWViOTExOTA5MWFmL3Jlc291cmNlLzhkNzAxOTZjLWE5NWUt'\
         r'NGEwNC05YzYxLTgxNDRiNGI2MGExOC9kb3dubG9hZC9iYXJyYWdlcy5jc3Y='
         
    loc_file = 'barrages.csv'
   
    
    '''
    try:
        df= input_data(url)
        print('Pulled file from data.gov.tn')
    except:
        df= input_data(loc_file)
        print('data.gov.tn is down! Pulled file from local')
        
    '''
    df= input_data(loc_file)
    df_mp= create_map_df (df)
    
    
    

    #------------Setup Sidebar (Filters)------------#
    st.sidebar.header('Please Filter here:')
    
    min_date = df['Date'].min()
    max_date = df['Date'].max()

    date = st.sidebar.date_input(
            "Select a Date", 
             min_value=min_date, 
             max_value=max_date, 
            value=max_date)

    regions= st.sidebar.multiselect(
            "Select a Region(s)",
            options= df_mp['Region'].unique(),
            default= df_mp['Region'].unique())
    
    
    df_dms= df_mp.loc[df_mp['Region'].isin(regions)]

    dams= st.sidebar.multiselect(
            "Select a Dam(s)",
            options= df_dms['Nom_Fr'].unique(),
            default= df_dms['Nom_Fr'].unique())   
    
    #------------------Main Page--------------------#
    st.title('Daily Situation of Tunisian Dams')   
    st.write('A dashboard of the situation of Dams in Tunisia.\
             Data is updated daily.<br>\
             Data source: data.gov.tn') 
    

    df_sel = df.loc[(df['Region'].isin(regions)) &
                    (df['Date']== date)]
    
    

    #stats
    stock_pre= round(df_sel['stock_annee_prec'].sum(),1)
    stock_cur= round(df_sel['stock'].sum(),1)
    cap= round(df_sel['Cap_tot_act'].sum(),1)
    
    fill_rate = round((stock_cur/cap)*100,1)

    
    
    
    ################### line plot: stock
    df_stk = df.loc[df['Region'].isin(regions)]
    df_stk_grp = df_stk.groupby('Date')[['stock', 'stock_annee_prec']].apply(sum).reset_index()
    
    pl_stock = px.line(df_stk_grp, x='Date', y=['stock', 'stock_annee_prec'],
                       markers=True)
    
    pl_stock.update_traces(line=dict(color='#7078CA'), selector=dict(name='stock'))
    pl_stock.update_traces(line=dict(color='#DCA525'), selector=dict(name='stock_annee_prec'))
    pl_stock.for_each_trace(lambda t: t.update(name='Current Stock' if t.name == 'stock' 
                                               else 'Last Year Stock'))
    config = {'displayModeBar': False}

    ################### pie chart: fill rate
    labels = ['Current Stock', 'Remaining']
    values = [stock_cur, cap - stock_cur]
    percentages = [fill_rate, 100 - fill_rate]
    
    pie_colors = ['#DCA525','#7078CA']
    
    pie_data = pd.DataFrame({'labels': labels, 'values': values, 'percentages': percentages})
    
    pl_fill = px.pie(pie_data, names='labels', values='values',
                 labels={'labels': 'Stock', 'values': 'Amount'},
                 hover_data=['percentages'],
                 hole=0.5,
                 color_discrete_sequence=pie_colors)
    
    pl_fill.update_traces(textposition='inside', textinfo='percent+label+value',
                      texttemplate="<b>%{label}</b> <br>%{value} (M m3) <br>%{percent}",
                      insidetextorientation='horizontal',
                      insidetextfont=dict(size=17, color='white', family='Arial'))  
    
    pl_fill.update_layout(showlegend=False)
    
    ####################### bar chart: previous year difference

    date_prYr = date.replace(year=date.year - 1)
    
    bar_data = {'Dates': [str(date), str(date_prYr)], 
                'stock': [stock_cur, stock_pre]}
 
    bar_colors = ['#7078CA','#C5D33A']
    
    pl_pryr = px.bar(bar_data, x='Dates', y='stock', color='Dates',
                     color_discrete_sequence=bar_colors)
    
    pl_pryr.update_traces(texttemplate='<b>%{y} (M m3)</b>', textposition='auto')
    
    
    stock_diff = round(stock_cur - stock_pre,1)
    stock_diff_pct = round((stock_diff/stock_pre)*100,1)

    pl_pryr.add_shape(
        type='line',
        x0=str(date_prYr),
        y0=stock_pre,
        x1=str(date),
        y1=stock_cur,
        line=dict(color='black', width=2)
    )
    
    pl_pryr.add_annotation(
        x=str(date),
        y=stock_cur,
        text=f'<b>Difference: {"+" if stock_diff > 0 else ""}{stock_diff} M m3 ({stock_diff_pct}%)</b>',
        showarrow=True,
        arrowhead=1,
        arrowcolor='black',
        arrowsize=1,
        ax=20,
        ay=-40,
        font=dict(color='green' if stock_diff > 0 else 'red')
        )


    pl_pryr.update_layout(
        xaxis_title='Dates',
        yaxis_title='stock')
    
    
    
    
    ###############################################################################################
    #st.dataframe(df_sel)
    
        # First row with three columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        #st.header('Spatial distribution of Observations')
        df_dms_mp= df_mp.loc[(df_mp['Region'].isin(regions)) & 
                             (df_mp['Nom_Fr'].isin(dams))]
        
        m= create_map(df_dms_mp)
        folium_static(m, width=400,height=350)
    
    with col2:
        #st.header('Filling Rate')
        st.markdown('<h2 style="margin-top: 0; margin-bottom: 0;">Filling Rate</h2>', unsafe_allow_html=True)
        st.plotly_chart(pl_fill,use_container_width=True)
    
    with col3:
        st.header('Comparison with last year')
        st.plotly_chart(pl_pryr,use_container_width=True)
        
    
    # Second row with one column
    col4 = st.columns(1)
    
    with col4[0]:
        st.header('Evolution of Water stock')
        st.plotly_chart(pl_stock,use_container_width=True)
        
    
    
    
    
    
    
    
    
    
    
   #################################################################################################################### 
    

    #pl_stock.write_html('pl_stock.html')
    #pl_fill.write_html('pl_fill.html')
    #pl_pryr.write_html('pl_pryr.html')
    #m.save('test_map.html')

    
    
    
  
