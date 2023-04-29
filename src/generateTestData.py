from random import randint
import pandas as pd
from datetime import datetime, timedelta


PRODUCTLIST = ["apples", "bananas"]
USER = "testUserLocal"
STARTLIMIT = 1000
BACKDATE = "3M"
ENDDATE = datetime.today()

#as a percentage
TRANSACTIONCHANCE = 60
PRICECHANGECHANCE = 10

PRICEVARIANCE = 15
WHOLESALEVARIANCE = 10


def main():
    LOOKBACKDELTA = delta_lookup(BACKDATE)
    startDate = ENDDATE - LOOKBACKDELTA

    wholesaleFrame = createWholesale(startDate)
    wholesaleFrame.to_csv(f'db/{USER}/wholesale.csv', index=False)

    retailFrame = createRetail(startDate)
    retailFrame.to_csv(f'db/{USER}/retail.csv', index=False)





def createWholesale(start: datetime):
    wholeSale = pd.DataFrame(columns=['id','product','price','units','timestamp'])
    
    for product in PRODUCTLIST:
        id = len(wholeSale) + 1
        price = getPrice()
        units = getUnits()
        timestamp = start.strftime('%Y-%m-%dT12:34:56.789Z')

        row = {'id':id,'product':product,'price':price,'units':units,'timestamp':timestamp}
        wholeSale = wholeSale.append(row, ignore_index=True)

    return wholeSale

def getPrice():
    return randint(5, 20) + (randint(0, 100) / 100)

def getUnits():
    return STARTLIMIT + randint(STARTLIMIT * WHOLESALEVARIANCE / -100, STARTLIMIT * WHOLESALEVARIANCE / 100)

def createRetail(start: datetime):
    DAYDELTA = timedelta(days=1)
    iterator = start

    retail = pd.DataFrame(columns=['id','product','price','units','timestamp'])


    while iterator < ENDDATE:
        for product in PRODUCTLIST:
            if rollDice(TRANSACTIONCHANCE):
                id = len(retail) + 1
                price = getRetailPrice(product, retail)
                units = getRetailUnits(start, product)
                timestamp = iterator.strftime('%Y-%m-%dT12:34:56.789Z')

                row = {'id':id,'product':product,'price':price,'units':units,'timestamp':timestamp}
                print(row)
                retail = retail.append(row, ignore_index=True)

        
        iterator += DAYDELTA

    return retail

def rollDice(chance: int):
    return randint(0, 100) <= chance


def getRetailPrice(product: str, retail: pd.DataFrame):
    existingSales = retail.loc[retail['product'] == product]
    #print('existing')
    #print(existingSales)

    if len(existingSales) == 0:
        return randint(15, 25) + (randint(0, 100) / 100)
    
    #print('retail')
    recentSale = existingSales[existingSales.id == existingSales.id.max()]
    #print(recentSale)
    
    lastSoldPrice = recentSale['price'].iloc[0]


    if rollDice(PRICECHANGECHANCE):
        price = lastSoldPrice * (1 + (randint(-15, 15) / 100))
        return round(price, 2)
    else:
        return lastSoldPrice




def getRetailUnits(start: datetime, product: str):
    maxPerDay = maxSell(start)
    units = randint(1, maxPerDay * 2) #maxPerDay was too conservative
    return units

def maxSell(start):
    minInventory = STARTLIMIT * (1 - (WHOLESALEVARIANCE / 100))
    
    businessDelta = ENDDATE - start
    businessDays = businessDelta.days

    return minInventory / businessDays



def delta_lookup(period):
    amount = int(period[0])
    unit = period[1]
    if unit == 'D':
        return timedelta(days=amount)
    elif unit == 'W':
        return timedelta(weeks=amount)
    elif unit == 'M':
        return timedelta(days=amount * 30)


main()








