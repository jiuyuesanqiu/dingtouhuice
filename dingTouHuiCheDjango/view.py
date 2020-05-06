import xalpha as xa
import pandas as pd
from django.http import HttpResponse


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
    auto = xa.policy.scheduled(zzcm, int(amount), pd.date_range(start, end, freq=freq))
    cm_t3 = xa.trade(zzcm, auto.status)
    a = cm_t3.dailyreport(end)
    return HttpResponse(a.to_json())
