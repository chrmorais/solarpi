# -*- coding: utf-8 -*-
import calendar
from datetime import datetime, timedelta
from sqlalchemy import func
from solarpi.extensions import db
from solarpi.pvdata.models import PVData


def get_todays_max_power():
    """
    :return: the maximum enegy yieled today
    """
    todays_max_power = PVData.query.with_entities(func.max(PVData.current_power).label('todays_max_power')).filter(
        PVData.created_at >= datetime.now()).first().todays_max_power

    if not todays_max_power:
        todays_max_power = 0

    return todays_max_power


def get_daily_energy_series(current_date):
    """
    :param current_date: date of the energy series
    :return: energy series
    """
    tomorrow = current_date + timedelta(days=1)
    return PVData.query.with_entities(PVData.created_at, PVData.current_power, PVData.daily_energy, PVData.dc_1_u,
                                      PVData.dc_2_u, PVData.ac_1_u, PVData.ac_2_u, PVData.ac_3_u).filter(
        PVData.created_at > current_date.strftime('%Y-%m-%d')).filter(
        PVData.created_at < tomorrow.strftime('%Y-%m-%d')).filter(PVData.current_power > 0).all()


def get_7_day_max_energy_series(current_date):
    """
    :param current_date: pivot date of the energy series
    :return: theoretical maximum energy series ± 3 days around current date
    """
    return PVData.query.with_entities(func.strftime('%H:%M:00', PVData.created_at).label('pvdata_created_at'),
                                      func.max(PVData.current_power).label('pv_max')).filter(
        PVData.created_at >= (current_date - timedelta(days=3)).strftime('%Y-%m-%d')).filter(
        PVData.created_at <= (current_date + timedelta(days=3)).strftime('%Y-%m-%d')).filter(
        PVData.current_power > 0).group_by(
        func.strftime('%H:%M:00', PVData.created_at)).all()


def get_last_n_days(n):
    query = "SELECT strftime('%Y-%m-%dT00:00:00', created_at) as created_at, max(daily_energy) as daily_energy FROM pvdata WHERE created_at > ? GROUP BY strftime('%Y-%m-%d', created_at)"
    return db.engine.execute(query, (datetime.now() - timedelta(days=n)))


def get_yearly_series():
    return db.engine.execute(
        "SELECT Strftime('%Y', created_at) as year, max(total_energy) - min(total_energy) as yearly_output FROM pvdata GROUP BY Strftime('%Y', created_at)")


def get_max_daily_energy_last_seven_days():
    """
    :return: returns the maximum energy yielded in the last 7 days
    """
    return PVData.query.with_entities(
        func.max(PVData.daily_energy).label('max_daily_energy')).filter(
        PVData.created_at >= (datetime.now() - timedelta(days=7))).first().max_daily_energy


def get_last_years_energy():
    """
    :return: total energy yielded in the previous year
    """
    current_year = datetime.now().year
    return PVData.query.with_entities(PVData.total_energy).filter(
        func.strftime('%Y', PVData.created_at) == str(current_year - 1)).order_by(PVData.id.desc()).first()


def get_yearly_data(year):
    """
    :param year: year of the data
    :return: returns an array of monthly energy for a given year
    """
    return PVData.query.with_entities((func.max(PVData.total_energy) - func.min(PVData.total_energy)).label(
        'total_energy')).filter(
        func.strftime('%Y', PVData.created_at) == str(year)).group_by(
        func.strftime('%Y-%m', PVData.created_at)).all()


def get_yearly_average_data():
    """
    :return: returns an array of monthly averages for previous years
    """
    current_year = str(datetime.now().year)
    query = "SELECT avg(monthly_yield) FROM ( SELECT strftime('%m', created_at) as month, max(total_energy) - min(total_energy) as monthly_yield FROM pvdata WHERE strftime('%Y', created_at) < ? GROUP BY strftime('%Y-%m', created_at) ) subq WHERE monthly_yield > 0 GROUP BY month;"
    return db.engine.execute(query, current_year)


def get_current_month_prediction(current_month_energy, last_years_average):
    """

    :param current_month_energy: energy yieled so far this month
    :param last_years_average: daily average energy yield for the same month in the previous year
    :return: series with predicted energy yield for the current month
    """
    now = datetime.now()
    current_month_prediction = current_month_energy + last_years_average * (
        calendar.monthrange(now.year, now.month)[1] - now.day + 1)

    current_month_prediction_series = ['null'] * 12
    current_month_prediction_series[now.month - 1] = int(current_month_prediction)
    return current_month_prediction_series


def get_current_values():
    """
    :return: the current photovoltaic values from the system
    """
    return PVData.query.order_by(PVData.id.desc()).first()


def get_first_date():
    """

    :return: the date in the databse
    """
    return PVData.query.order_by(PVData.id.asc()).first().created_at


def get_sec(s):
    l = map(int, s.split(':'))
    return sum(n * sec for n, sec in zip(l[::-1], (1, 60, 3600)))


def get_todays_date():
    return datetime.now().date()
