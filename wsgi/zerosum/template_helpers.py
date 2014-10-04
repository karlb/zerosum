import pytz
from datetime import datetime

from zerosum import app


@app.template_filter('dt')
def format_dt(dt):
    if isinstance(dt, str):
        dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S.%f")
    tz = pytz.timezone('Europe/Berlin')
    dt_with_tz = dt.replace(tzinfo=pytz.timezone('UTC')).astimezone(tz)
    return dt_with_tz.strftime('%Y-%m-%d %H:%M')


@app.template_filter('plusminus')
def format_plusminus(value):
    if value < 0:
        return 'minus'
    if value > 0:
        return 'plus'
    else:
        return ''


@app.template_filter('money')
def format_money(value):
    return '{:.2f}'.format(value)


@app.context_processor
def inject_app_name():
    return dict(app_name='TrackMyOwe')

