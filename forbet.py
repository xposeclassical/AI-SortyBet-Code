import time
import asyncio
import pandas as pd
from pyppeteer import launch
from bs4 import BeautifulSoup
from func import requests_init,saving_files,drop_duplicate,match_day_date,main_date,save_daily_csv,sorting_values
import os
import sys

async def main(): 
    full_path = save_daily_csv()
    path = f'{full_path}/forebet.csv'
    
    # Try multiple Chrome paths
    chrome_paths = [
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
        None  # Let pyppeteer find it automatically
    ]
    
    browser = None
    for chrome_path in chrome_paths:
        try:
            if chrome_path and os.path.exists(chrome_path):
                print(f"Using Chrome at: {chrome_path}")
                browser = await launch(
                    executablePath=chrome_path,
                    headless=False,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                break
            elif chrome_path is None:
                print("Trying to let pyppeteer find Chrome automatically...")
                browser = await launch(
                    headless=False,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                break
        except Exception as e:
            print(f"Failed with path {chrome_path}: {e}")
            continue
    
    if not browser:
        print("❌ Could not launch Chrome. Please install Google Chrome.")
        print("Download from: https://www.google.com/chrome/")
        return

    page = await browser.newPage()

    _1x2url = f'https://www.forebet.com/en/football-predictions/predictions-1x2/{main_date()}'
    ovrund_url = f'https://www.forebet.com/en/football-predictions/under-over-25-goals/{main_date()}'
    btsots_url = f'https://www.forebet.com/en/football-predictions/both-to-score/{main_date()}'
    all_url = [_1x2url, ovrund_url, btsots_url]

    _1x2data = {
        'DATE': [], 'TIME': [], 'HOME TEAM': [], 'AWAY TEAM': [],
        'HOME PER': [], 'DRAW PER': [], 'AWAY PER': []
    }

    ovrund_data = {
        'HOME TEAM': [], 'AWAY TEAM': [],
        'UNDER 2.5': [], 'OVER 2.5': []
    }
    
    btsund_data = {
        'HOME TEAM': [], 'AWAY TEAM': [],
        'BTS': [], 'OTS': [], 'NAME': []
    }
    
    for main_url in all_url:
        try:
            print(f"\n🌐 Navigating to: {main_url}")
            await page.goto(main_url, timeout=60000, waitUntil='networkidle2')

            # Scroll to load content
            for i in range(5):
                await page.evaluate('window.scrollBy(0, window.innerHeight)')
                await asyncio.sleep(1)

            # Click MORE button if exists
            for x in range(3):
                try:
                    await page.waitForSelector('#mrows', {'visible': True, 'timeout': 5000})
                    await page.click('#mrows')
                    print(f'Clicked MORE button {x+1} times')
                except:
                    break
                await asyncio.sleep(2)

            await asyncio.sleep(5)
            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            all_content = soup.find('div', class_='schema')
            
            if not all_content:
                print(f"⚠ No content found for {main_url}")
                continue

            if main_url == _1x2url:
                print('\n📊 CURRENTLY ON 1X2 OPTION')
                match_date = [y.text.split()[0] for y in all_content.find_all('span', class_='date_bah')]
                match_time = [y.text.split()[-1] for y in all_content.find_all('span', class_='date_bah')]
                hm_team = [y.text for y in all_content.find_all('span', class_='homeTeam')]
                aw_team = [y.text for y in all_content.find_all('span', class_='awayTeam')]
                
                hm_per = [y.find_all('span')[0].text for y in all_content.find_all('div', class_='fprc')]
                draw_per = [y.find_all('span')[1].text for y in all_content.find_all('div', class_='fprc')]
                aw_per = [y.find_all('span')[2].text for y in all_content.find_all('div', class_='fprc')]
                
                print(f"Found {len(match_date)} matches")
                _1x2data['DATE'] = match_date
                _1x2data['TIME'] = match_time
                _1x2data['HOME TEAM'] = hm_team
                _1x2data['AWAY TEAM'] = aw_team
                _1x2data['HOME PER'] = hm_per
                _1x2data['DRAW PER'] = draw_per
                _1x2data['AWAY PER'] = aw_per

            elif main_url == ovrund_url:
                print('\n📊 CURRENTLY ON OVER/UNDER OPTION')
                hm_team = [y.text for y in all_content.find_all('span', class_='homeTeam')]
                aw_team = [y.text for y in all_content.find_all('span', class_='awayTeam')]
                under_2_5 = [y.find_all('span')[0].text for y in all_content.find_all('div', class_='fprc')]
                over_2_5 = [y.find_all('span')[1].text for y in all_content.find_all('div', class_='fprc')]
                
                ovrund_data['HOME TEAM'] = hm_team
                ovrund_data['AWAY TEAM'] = aw_team
                ovrund_data['UNDER 2.5'] = under_2_5
                ovrund_data['OVER 2.5'] = over_2_5

            else:
                print('\n📊 CURRENTLY ON BTS/OTS OPTION')
                hm_team = [y.text for y in all_content.find_all('span', class_='homeTeam')]
                aw_team = [y.text for y in all_content.find_all('span', class_='awayTeam')]
                ots = [y.find_all('span')[0].text for y in all_content.find_all('div', class_='fprc')]
                bts = [y.find_all('span')[1].text for y in all_content.find_all('div', class_='fprc')]
                
                btsund_data['HOME TEAM'] = hm_team
                btsund_data['AWAY TEAM'] = aw_team
                btsund_data['BTS'] = bts
                btsund_data['OTS'] = ots
                btsund_data['NAME'] = 'Forebet'
                
        except Exception as e:
            print(f"❌ Error processing {main_url}: {e}")
            continue

    # Combine data
    df1 = pd.DataFrame(_1x2data)
    df2 = pd.DataFrame(ovrund_data)
    df3 = pd.DataFrame(btsund_data)
    
    if len(df1) > 0 and len(df2) > 0:
        all_df = pd.merge(df1, df2, on=['HOME TEAM', 'AWAY TEAM'], how='inner')
        if len(df3) > 0:
            all_df = pd.merge(all_df, df3, on=['HOME TEAM', 'AWAY TEAM'], how='inner')
        
        all_df = all_df.reset_index(drop=True)
        print(f"\n✅ Total matches collected: {len(all_df)}")
        all_df.to_csv(path, index=False)
        print('============================= FILE SAVED ==========================')
        drop_duplicate(path=path)
    else:
        print("❌ No data collected")
    
    await browser.close()

asyncio.run(main())
