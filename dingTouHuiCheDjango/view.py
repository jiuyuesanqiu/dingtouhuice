import xalpha as xa
import pandas as pd
# Create your views here.
from django.http import HttpResponse
from django.http import JsonResponse
from datetime import datetime
import json
import requests


def hello(request):
    code = request.GET.get('code')
    start = request.GET.get('start')
    end = request.GET.get('end')
    amount = request.GET.get('amount')
    period = request.GET.get('period')
    if period == 'M':
        freq = 'W-MON'
    else:
        freq = 'MS'
    zzcm = xa.fundinfo(code)
    # 分红再投入
    zzcm.dividend_label = 1
    auto = xa.policy.scheduled(
        zzcm, int(amount), pd.date_range(start, end, freq=freq))
    cm_t3 = xa.trade(zzcm, auto.status)
    a = cm_t3.dailyreport(end)
    return HttpResponse(a.to_json())


def index(request):
    code = request.GET.get('code')
    try:
        zzcm = xa.fundinfo(code)
    except Exception:
        return JsonResponse({'code': 500, 'msg': '基金代码错误'})
    # 分红再投入
    zzcm.dividend_label = 1
    start = request.GET.get('start')
    end = request.GET.get('end')
    amount = request.GET.get('amount')
    freq = request.GET.get('freq')
    offset = request.GET.get('offset')
    rng = pd.date_range(start, end, freq=freq)+pd.DateOffset(days=int(offset))
    price = zzcm.price[(zzcm.price["date"] >= start)
                       & (zzcm.price["date"] <= end)]
    # 有价格的起始日期
    priceStart = price.iloc[0].date
    priceEnd = price.iloc[-1].date
    # 需要判断rng的时间是否合法，是否都在有价格的区间
    datel = []
    isSmall = False
    for date in rng:
        if date >= priceStart and date <= priceEnd:
            datel.append(date)
        elif date < priceStart:
            isSmall = True
    if isSmall:
        try:
            thing_index = datel.index(priceStart)
        except ValueError:
            thing_index = -1
        if thing_index == -1:
            datel.insert(0, priceStart)
    status = pd.DataFrame(
        data={"date": datel, zzcm.code: [float(amount)]*len(datel)})
    cm_t3 = xa.trade(zzcm, status)
    dailyreport = cm_t3.dailyreport(end)
    xirr = cm_t3.xirrrate(end)
    return JsonResponse({
        'code': 0,
        'xirr': xirr,
        'dailyreport': dailyreport.to_dict()
    })


def xirr(transactions):
    years = [(ta[0] - transactions[0][0]).days / 365.0 for ta in transactions]
    residual = 1
    step = 0.05
    guess = 0.05
    epsilon = 0.0001
    limit = 10000
    while abs(residual) > epsilon and limit > 0:
        limit -= 1
        residual = 0.0
        for i, ta in enumerate(transactions):
            residual += ta[1] / pow(guess, years[i])
        if abs(residual) > epsilon:
            if residual > 0:
                guess += step
            else:
                guess -= step
                step /= 2.0
    return guess-1


def bitcoinBackTest(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    amount = float(request.GET.get('amount'))
    freq = request.GET.get('freq')
    offset = request.GET.get('offset')

    payload = {'start': start, 'end': end}
    r = requests.get(
        'https://api.coindesk.com/v1/bpi/historical/close.json', params=payload)
    json_data = r.json()
    bpi = json_data['bpi']
    df = pd.DataFrame(bpi.items(), columns=['date', 'price'])
    df['amount'] = [amount]*len(bpi.keys())
    rng = pd.date_range(start, end, freq=freq)+pd.DateOffset(days=int(offset))
    rng = rng[rng <= end]  # 过滤超出结束时间的日期
    ds = rng.strftime("%Y-%m-%d").tolist()  # 下单日期列表

    order_df = df[df['date'].isin(ds)]
    # 总投入
    total_principal = order_df['amount'].sum()
    coinNum = order_df['amount']/order_df['price']
    # 现值
    fv = df.iloc[[-1]]['price'].array[0]*coinNum.sum()
    # 总收益
    total_interest = fv - total_principal
    # 收益率
    total_rate = total_interest / total_principal
    # xirr
    del order_df['price']
    order_df['date'] = order_df['date'].astype('datetime64[ns]')
    order_df['amount'] = order_df['amount'] * (-1)
    cash_flow = order_df.values.tolist()
    end_date = df.iloc[[-1]]['date'].astype('datetime64[ns]').array[0]
    cash_flow.append([end_date, fv])
    rate = xirr(cash_flow)
    return JsonResponse({'code': 0, 'data': {'fv': fv, 'total_principal': total_principal, 'total_interest': total_interest, 'total_rate': total_rate, 'xirr': rate}})
