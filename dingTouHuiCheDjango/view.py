import xalpha as xa
import pandas as pd
# Create your views here.
from django.http import HttpResponse
from django.http import JsonResponse
from datetime import datetime
import json

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
    auto = xa.policy.scheduled(zzcm, int(amount), pd.date_range(start, end, freq=freq))
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
        'xirr':xirr,
        'dailyreport': dailyreport.to_dict()
    })