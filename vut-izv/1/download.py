import urllib.parse as up
import urllib.request as ur
import requests as req
import os
import numpy as np
import zipfile
from bs4 import BeautifulSoup
import re
import csv
import io
import pickle
import gzip

class DataDownloader():
    def __init__(self, url="https://ehw.fit.vutbr.cz/izv/", folder="data", cacheFileName="data_{}.pk1.gz"):
        self.url = url
        if not os.path.exists(f'./{folder}'):
            os.makedirs(f'./{folder}')
        self.folder = folder
        self.cacheFileName = cacheFileName
        self.cache = {}


    def download_data(self):
        """Downloads all files from url into data directory folder"""
        html = req.get(self.get_url(), headers={'User-Agent': 'down/0.0.1'})
        soup = BeautifulSoup(html.content, 'html.parser')
        for path in soup.find_all('a', href=re.compile("~*.zip")):
            r = req.get(f'{self.get_url()}{path.get("href")}')
            fileName = path.get("href")[5:]
            open(f'./{self.get_folder()}/{fileName}', 'wb').write(r.content)


    def parse_region_data(self, region):
        """Parse data of one region and return a tuple (list[str], list[np.ndarray])
        
        Keyword arguments:
        region -- specifies which region to parse
        """
        if len(os.listdir(f'./{self.get_folder()}')) == 0:
            print("Downloading data.")
            self.download_data()

        # header list of column names for return tuple
        header = ["p1",	"p36", "p37", "p2a", "weekday(p2a)", "p2b", "p6", "p7", "p8", "p9", "p10", "p11", "p12", "p13a", "p13b", "p13c", "p14", "p15", "p16", "p17", "p18", "p19", "p20", "p21", "p22", "p23", "p24", "p27", "p28", "p34", "p35", "p39", "p44", "p45a", "p47", "p48a", "p49", "p50a", "p50b", "p51", "p52", "p53", "p55a", "p57", "p58", "a", "b", "d", "e", "f", "g", "h", "i", "j", "k", "l", "n", "o", "p", "q", "r", "s", "t", "p5a", "region"]

        # all the datatypes for return tuple
        data_types = [np.longlong, np.short, np.int_, 'datetime64[D]', np.short, np.int_, *[np.short for i in range(10)], np.int_, *[np.short for i in range(24)], np.int, *[np.short for i in range(3)], *[np.double for i in range(6)], *[np.unicode_ for i in range(2)], np.short, *[np.unicode_ for i in range(2)], np.int_, np.short, *[np.unicode_ for i in range(2)], *[np.int_ for i in range(2)], np.unicode_, np.short, np.unicode_]

        # determine which file to open according to region
        regionFileNumber = self.get_region_number(region)
        regionFileName = f'{regionFileNumber}.csv' if regionFileNumber > 10 else f'0{regionFileNumber}.csv'
        
        # sort zip files by year
        newest = 0
        newestFileName = ''
        sortedZipFiles = []
        for filename in os.listdir(self.get_folder()):
            # check and choose the right files from which data will be parsed
            if filename == 'datagis2016.zip' or re.match(r'.*-rok-.*', filename):
                sortedZipFiles.append(filename)
            if re.match(r'.*2020.*', filename):
                num = int(filename.split("-")[1].split(".")[0])
                if num > newest:
                    newest = num
                    newestFileName = filename
        sortedZipFiles.append(newestFileName)
        sortedZipFiles.sort(key=lambda y: int(re.match(r'.*([0-9]{4}).*', y).group(1)))

        # fill parsed data into temporary list
        temp = [[] for i in range(65)]
        for dataZipFile in sortedZipFiles:
            with zipfile.ZipFile(f'./{self.get_folder()}/{dataZipFile}', 'r') as zf:
                if regionFileName in zf.namelist():
                    with zf.open(regionFileName, 'r') as csvfile:
                        reader = csv.reader(io.TextIOWrapper(csvfile, 'windows-1250'), delimiter=';')
                        for row in reader:
                            for i, column in enumerate(row):
                                if data_types[i] != np.unicode_ and (column == '' or re.match(r'.*\D.*', column)):
                                    temp[i].append(-1)
                                elif re.match(r'.*,.*', column):
                                    column.replace(',','.')
                                else:
                                    temp[i].append(column)
                        temp[64].append(region)

        # convert temporary parsed data list to list of numpy array
        data = []
        for i in range(65):
            data.append(np.array(temp[i], dtype=data_types[i]))
            
        return (header, data)


    def get_list(self, regions=None):
        """Returns parsed data for chosen regions as tuple (list[str], list[np.ndarray])."""
        header = ["p1",	"p36", "p37", "p2a", "weekday(p2a)", "p2b", "p6", "p7", "p8", "p9", "p10", "p11", "p12", "p13a", "p13b", "p13c", "p14", "p15", "p16", "p17", "p18", "p19", "p20", "p21", "p22", "p23", "p24", "p27", "p28", "p34", "p35", "p39", "p44", "p45a", "p47", "p48a", "p49", "p50a", "p50b", "p51", "p52", "p53", "p55a", "p57", "p58", "a", "b", "d", "e", "f", "g", "h", "i", "j", "k", "l", "n", "o", "p", "q", "r", "s", "t", "p5a", "region"]

        result = []

        # if none of the regions were selected, take all
        if regions == None:
            regions = ['PHA', 'STC', 'JHC', 'PLK', 'ULK', 'HKK', 'JHM', 'MSK', 'OLK', 'ZLK', 'VYS', 'PAK', 'LBK', 'KVK']
        
        # iterate through regions, while concatenating results
        for region in regions:
            if region not in self.cache:
                # data of the region is not in memory
                path = f'./{self.get_folder()}/{self.cacheFileName.format(region)}'
                if not os.path.exists(path):
                    # data of the region is not in cache so parse it
                    parsedRegionData = self.parse_region_data(region)
                    # save parsed data to cache
                    with gzip.open(path, 'wb') as f:
                        pickle.dump(parsedRegionData[1], f)
                    # save parsed data to memory
                    self.cache[region] = parsedRegionData[1]
                    # concatenate parsed data
                    if result:
                        for i, column in enumerate(parsedRegionData[1]):
                            result[i] = np.concatenate((result[i], column))
                    else:
                        result = parsedRegionData[1]
                else:
                    # data of the region is in cache but not in memory so load data from cache
                    with gzip.open(path, 'rb') as f:
                        loadedData = pickle.load(f)
                    # save data from cache into memory
                    self.cache[region] = loadedData
                    # concatenate data
                    if result:
                        for i, column in enumerate(loadedData):
                            result[i] = np.concatenate((result[i], column))
                    else:
                        result = loadedData
            else:
                # region data is in memory so only concatenate with result
                if result:
                    for i, column in enumerate(self.cache[region]):
                        result[i] = np.concatenate((result[i], column))
                else:
                    result = self.cache[region]
        return (header, result)


    def get_folder(self):
        return self.folder


    def get_url(self):
        return self.url


    def get_region_number(self, region):
        return {
            'PHA': 0,
            'STC': 1,
            'JHC': 2,
            'PLK': 3,
            'ULK': 4,
            'HKK': 5,
            'JHM': 6,
            'MSK': 7,
            'OLK': 14,
            'ZLK': 15,
            'VYS': 16,
            'PAK': 17,
            'LBK': 18,
            'KVK': 19
        }[region]

if __name__ == "__main__":
    dd = DataDownloader()
    data = dd.get_list(["STC", "JHC", "OLK"])
    print("Basic info about downloaded entries:")
    print(f'Columns: {[data[0][i] for i in range(65)]}')
    print(f'Number of entries: {len(data[1][0])}')
    print(f'Selected regions: {np.unique(data[1][-1])}')