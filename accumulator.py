from func import requests_init,saving_files,drop_duplicate,save_daily_csv,match_day_date,save_daily_csv2,main_date
from bs4 import BeautifulSoup
from lxml import html
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import os
import warnings
warnings.filterwarnings('ignore')

def create_safe_session():
    """Create a requests session with retries and SSL handling"""
    session = requests.Session()
    
    # Disable SSL warnings
    requests.packages.urllib3.disable_warnings()
    
    # Configure retries
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))
    
    # Browser headers
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    })
    
    return session

def accumulator_func():
    save_dir = save_daily_csv2(main_dir=os.path.join(os.path.dirname(os.path.dirname(__file__)),'CSV FILES'),second_dir_path_name=str(main_date())+' Main_Files')
    save_path = f'{save_dir}/ACCU_Data.csv'

    local_time = time.localtime()
    full_path = save_daily_csv()
    path = f'{full_path}/accumulator.csv'

    td_url = 'https://www.accagenerator.com/football-predictions/'

    # Create session for all requests
    session = create_safe_session()
    
    try:
        res = session.get(td_url, timeout=30, verify=False)
        soup = BeautifulSoup(res.content, "html.parser")
    except Exception as e:
        print(f"Failed to fetch main page: {e}")
        return

    links = [name.get('href') for name in soup.findAll('a')]
    all_links = []
    for link in links:
        if link and link.startswith('https://www.accagenerator.com/football-tips-and-predictions-for') and link not in all_links:
            all_links.append(link)
    
    print('LENGTH OF ALL LINKS = ', len(all_links))

    ex_link = ['1x2-predictions/', 'over-under-predictions', 'both-teams-score-predictions/']

    for i, x in enumerate(all_links[:]):
        pp_data = {'INFO': []}
        pp_target = f'{x}'
        pp_data['INFO'].append(pp_target)
        
        try:
            pp_data_df = pd.read_csv(save_path)['INFO'].to_list()
        except:
            pp_data_df = pd.DataFrame({'INFO': ['accumulator']})['INFO'].to_list()

        if pp_target not in pp_data_df:
            saving_files(data=pp_data, path=save_path)
            print(x)
            
            data = {
                'DATE': [], 'TIME': [], 'HOME TEAM': [], 'AWAY TEAM': [],
                'HOME PER': [], 'DRAW PER': [], 'AWAY PER': [],
                'UNDER 2.5': [], 'OVER 2.5': [], 'BTS': [], 'OTS': [],
                'NAME': []
            }
            
            for xlink in ex_link:
                try:
                    res = session.get(x + xlink, timeout=30, verify=False)
                    soup = BeautifulSoup(res.content, "html.parser")
                    
                    print(f'>>>>>>>>>>>>>>>>>>>>  NUMBER = {i+1} HAS STARTED TO RUN, WITH TOTAL RUNS OF {len(all_links)} & REMAINING OF {len(all_links) - (i+1)} <<<<<<<<<<<<<<<<<<<< \n')
                    
                    tip_info_elem = soup.select('#accagen-banner > div > div > div.accagen-banner-text.accagen-headline > h1')
                    if not tip_info_elem:
                        print(f"No tip info found for {xlink}, skipping...")
                        continue
                    
                    tip_info = tip_info_elem[0].text
                    print(tip_info)
                    
                    # Try multiple selectors for matches
                    matches = soup.select('#accagen-banner > div > div > div:nth-child(3) > ul > li')
                    if not matches:
                        matches = soup.select('.tips-card')
                    
                    for match in matches:
                        try:
                            # Extract date and time
                            date_elem = match.find('div', class_="datecombos")
                            if not date_elem:
                                continue
                                
                            pred_date_parts = date_elem.text.split()
                            if len(pred_date_parts) < 4:
                                continue
                                
                            pred_time = pred_date_parts[3]
                            pred_date = f'{local_time[0]}.' + pred_date_parts[1]
                            
                            # Check if match is for today
                            time_match = time.strptime(pred_date, '%Y.%d.%m')[:3] == local_time[:3]
                            if not time_match:
                                continue
                            
                            # Extract teams
                            teams_elem = match.find('h3', class_="tips-card__name-first")
                            if not teams_elem:
                                continue
                                
                            teams = teams_elem.text.split('vs')
                            if len(teams) < 2:
                                continue
                            
                            # Extract tip
                            tip_elem = match.find('div', class_="tipdetail")
                            tip = tip_elem.text.strip() if tip_elem else ""
                            
                            # Extract percentage
                            per_elem = match.find('span', class_="count-text")
                            tip_per = int(per_elem.get('data-stop')) if per_elem and per_elem.get('data-stop') else 0
                            
                            print(pred_date, pred_time, teams[0].strip(), teams[1].strip(), tip, tip_per)
                            
                            # Process based on tip type
                            if '1x2' in tip_info.lower():
                                data['DATE'].append(pred_date)
                                data['TIME'].append(pred_time)
                                data['HOME TEAM'].append(teams[0].strip())
                                data['AWAY TEAM'].append(teams[1].strip())
                                
                                if tip == '1':
                                    hw = tip_per
                                    draw = int((100 - tip_per)/2)
                                    aw = int((100 - tip_per)/2)
                                elif tip == '2':
                                    aw = tip_per
                                    draw = int((100 - tip_per)/2)
                                    hw = int((100 - tip_per)/2)
                                elif tip == 'X':
                                    draw = tip_per
                                    hw = int((100 - tip_per)/2)
                                    aw = int((100 - tip_per)/2)
                                else:
                                    continue
                                    
                                data['HOME PER'].append(hw)
                                data['DRAW PER'].append(draw)
                                data['AWAY PER'].append(aw)
                                data['NAME'].append('ACC')
                                
                            elif 'btts' in tip_info.lower():
                                if tip.lower() == 'yes':
                                    data['BTS'].append(tip_per)
                                    data['OTS'].append(100 - tip_per)
                                elif tip.lower() == 'no':
                                    data['OTS'].append(tip_per)
                                    data['BTS'].append(100 - tip_per)
                                    
                            elif 'over under' in tip_info.lower():
                                if 'over' in tip.lower():
                                    data['OVER 2.5'].append(tip_per)
                                    data['UNDER 2.5'].append(100 - tip_per)
                                elif 'under' in tip.lower():
                                    data['UNDER 2.5'].append(tip_per)
                                    data['OVER 2.5'].append(100 - tip_per)
                                    
                        except Exception as e:
                            print(f"Error processing match: {e}")
                            continue
                            
                except Exception as e:
                    print(f"Error processing {xlink}: {e}")
                    continue
                    
            if any(data.values()):  # Only save if we have data
                saving_files(data=data, path=path)
            
    drop_duplicate(path=path)

if __name__ == "__main__":
    accumulator_func()
