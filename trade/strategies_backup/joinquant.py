# 导入函数库
from jqdata import *
from dateutil.relativedelta import relativedelta
import pandas as pd
import jqdata
import json
from typing import Callable, Optional
import math
import talib as tl
from copy import copy
import numpy as np
from datetime import datetime
from enum import Enum
from datetime import timedelta
from pytz import timezone

# constant and data object
CHINA_TZ = timezone("Asia/Shanghai")

EVENT_TRADE = "eTrade."
EVENT_BAR = "eBar."
EVENT_ORDER = "eOrder."
EVENT_POSITION = "ePosition."
EVENT_ACCOUNT = "eAccount."
EVENT_CONTRACT = "eContract."
EVENT_LOG = "eLog"
EVENT_RENDER = 'eRender'
EVENT_LOAD = "eLoad"
EVENT_STRATEGY = "eStrategy"
EVENT_STRATEGY_LOG = "eStrategyLog"
EVENT_STRATEGY_STOPORDER = "eStopOrder"
EVENT_CHANTU = "eCHANTU"
EVENT_BACKTEST_LOG = "eBacktestLog"
EVENT_BACKTEST_FINISHED = "eBacktestFinished"
EVENT_BACKTEST_OPTIMIZATION_FINISHED = "eBacktestOptimizationFinished"


class Direction(Enum):
    LONG = "多"  # 1
    SHORT = "空"  # 2


class Offset(Enum):
    NONE = ""
    OPEN = "开"
    CLOSE = "平"
    CLOSETODAY = "平今"
    CLOSEYESTERDAY = "平昨"


class Status(Enum):
    """
    OrderStatus_Unknown = 0
    OrderStatus_New = 1                   ## 已报
    OrderStatus_PartiallyFilled = 2       ## 部成
    OrderStatus_Filled = 3                ## 已成
    OrderStatus_Canceled = 5              ## 已撤
    OrderStatus_PendingCancel = 6         ## 待撤
    OrderStatus_Rejected = 8              ## 已拒绝
    OrderStatus_Suspended = 9             ## 挂起
    OrderStatus_PendingNew = 10           ## 待报
    OrderStatus_Expired = 12              ## 已过期
    """
    UNKNOWN = "UNKNOWN"
    SUBMITTING = "已提交"
    PARTTRADED = "部分成交"
    ALLTRADED = "全部成交"
    CANCELLED = "已撤销"
    WAIT_CANCELLED = "待撤销"
    REJECTED = "拒单"
    SUSPENDED = "挂起"
    PENDINGNEW = "待提交"
    EXPIRED = "已过期"
    NOTTRADED = "未成交"


STATUS_MAP = {
    1: Status.SUBMITTING,
    2: Status.PARTTRADED,
    3: Status.ALLTRADED,
    5: Status.CANCELLED,
    6: Status.WAIT_CANCELLED,
    8: Status.REJECTED,
    9: Status.SUSPENDED,
    10: Status.PENDINGNEW,
    12: Status.EXPIRED,
}


class StopOrderStatus(Enum):
    WAITING = "等待中"
    CANCELLED = "已撤销"
    TRIGGERED = "已触发"


class EngineType(Enum):
    LIVE = "实盘"
    BACKTEST = "回测"


class OrderType(Enum):
    """
    OrderType_Unknown = 0
    OrderType_Limit = 1            ## 限价委托
    OrderType_Market = 2           ## 市价委托
    OrderType_Stop = 3             ## 止损止盈委托
    """
    UNKNOWN = "UNKNOWN"
    LIMIT = "限价委托"
    MARKET = "市价委托"
    STOP = "止损止盈委托"


ORDERTYPE_MAP = {
    1: OrderType.LIMIT,
    2: OrderType.MARKET,
    3: OrderType.STOP,
}


class Exchange(Enum):
    SZSE = "SZSE"
    SSE = "SSE"


class Interval(Enum):
    MINUTE = "1m"
    MINUTE5 = "5m"
    MINUTE30 = "30m"

    HOUR = "1h"
    DAILY = "d"
    WEEKLY = "w"


INTERVAL_VT2RQ = {
    Interval.MINUTE: "1m",
    Interval.HOUR: "60m",
    Interval.DAILY: "1d",
}

INTERVAL_ADJUSTMENT_MAP = {
    Interval.MINUTE: timedelta(minutes=1),
    Interval.HOUR: timedelta(hours=1),
    Interval.DAILY: timedelta()  # no need to adjust for daily bar
}


class METHOD(Enum):
    BZ = '标准操作方法'
    JJ = '激进操作方法'
    DX = '短线反弹操作方法'


INTERVAL_DAYS = 30

INTERVAL_DELTA_MAP = {
    Interval.MINUTE: timedelta(minutes=1),
    Interval.HOUR: timedelta(hours=1),
    Interval.DAILY: timedelta(days=1),
}

# ['月线', '周线', '日线', '60分钟', '30分钟', '15分钟', '5分钟', '1分钟']
FREQS = ['日线', '30分钟', '5分钟', '1分钟']

FREQS_INV = list(FREQS)
FREQS_INV.reverse()

FREQS_WINDOW = {
    '日线': [240, Interval.MINUTE, Interval.DAILY],
    '30分钟': [30, Interval.MINUTE, Interval.MINUTE30],
    '5分钟': [5, Interval.MINUTE, Interval.MINUTE5],
    '1分钟': [1, Interval.MINUTE, Interval.MINUTE],
}

INTERVAL_FREQ = {
    'd': '日线',
    '30m': '30分钟',
    '5m': '5分钟',
    '1m': '1分钟'
}

STOPORDER_PREFIX = 'stop_order'

PARAM_ZH_MAP = {'method': '交易方法', 'vt_symbol': '股票代码', 'symbol': '股票代码', 'strategy_name': '策略名称', 'include': 'K线包含',
                'build_pivot': '中枢类型', 'qjt': '用区间套',
                'gz': '使用共振', 'jb': '操作级别'}

PARAM_ZH_MAP_INV = {'股票代码': 'vt_symbol', '策略名称': 'strategy_name', 'K线包含': 'include', '中枢类型': 'build_pivot',
                    '用区间套': 'qjt', '使用共振': 'gz'}

SETTING_ZH_MAP = {

}

ZH_TRANS_MAP = {'标准操作方法': 'Chan_Strategy_STD', '激进操作方法': 'Chan_Strategy_JJ', '短线反弹操作方法': 'Chan_Strategy_DXFT',
                '缠论K线': True, '普通K线': False, '笔中枢': False, '线段中枢': True, '是': True, '否': False
                }


class BarData:
    def __init__(self, symbol, exchange, datetime, interval=None, volume=0, open_interest=0, open_price=0, high_price=0,
                 low_price=0, close_price=0):
        self.symbol = symbol
        self.exchange = exchange
        self.datetime = datetime

        self.interval = interval
        self.volume = volume
        self.open_interest = open_interest
        self.open_price = open_price
        self.high_price = high_price
        self.low_price = low_price
        self.close_price = close_price

    def __post_init__(self):
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"


# ===============================end constant==================================

# ===============================class 类==================================
class StrengthStock:
    """ 获取最近几天回落的强势股票 """

    def __init__(self, select_end_date, industry_compare_days=66, stock_compare_days=13,
                 select_industry_amount=6, select_stock_amount=10, fall_back_days=5,
                 prefer_industry_order=3, prefer_stock_order=5, prefer_stock_amount=5):
        # 选取强势股的参数
        self.industry_compare_days = industry_compare_days
        self.stock_compare_days = stock_compare_days
        self.select_industry_amount = select_industry_amount
        self.select_stock_amount = select_stock_amount

        # 选取回落时的参数
        self.prefer_industry_order = prefer_industry_order
        self.prefer_stock_order = prefer_stock_order
        self.prefer_stock_amount = prefer_stock_amount

        # 最近N天出现回落
        self.fall_back_days = fall_back_days
        # 当前选股时间
        self.select_end_date = select_end_date
        # fall_back_days之前都是强势的end date
        self.strength_end_date = get_trade_days(count=self.fall_back_days, end_date=select_end_date)[0].strftime(
            '%Y-%m-%d')

    # 总执行流程
    def select_strength_stocks(self):
        # 1. 获取强势板块
        strength_industry_codes = self.select_strength_industry()
        # 2. 获取强势板块里的强势个股
        strength_stocks_in_industry = self.select_strength_stocks_in_industry(strength_industry_codes)
        # 3. 获取强势个股近期回落较大的
        return self.select_fall_back_stocks(strength_stocks_in_industry)

    def select_strength_industry(self):
        # 获取大盘最近n个交易日的涨跌幅
        dapan_range = self.get_stock_range('000001.XSHG', self.industry_compare_days, self.strength_end_date)

        # 计算每个行业相对大盘的强弱
        industry_strength = dict()
        industries = get_industries(name='sw_l1')
        # industries_names = get_industries(name='sw_l1')['name']
        for industry in list(industries.index):
            # 获取申万行业最近n个交易日的涨跌幅
            industry_range = finance.run_query(query(finance.SW1_DAILY_PRICE)
                                               .filter(finance.SW1_DAILY_PRICE.code == industry,
                                                       finance.SW1_DAILY_PRICE.date >=
                                                       get_trade_days(count=self.industry_compare_days,
                                                                      end_date=self.strength_end_date)[0].strftime(
                                                           '%Y-%m-%d'),
                                                       finance.SW1_DAILY_PRICE.date <= self.strength_end_date)
                                               .order_by(finance.SW1_DAILY_PRICE.date.asc()))['change_pct']

            # 行业相对板块强弱打分
            industry_score = self.get_score(industry_range, dapan_range, self.industry_compare_days)
            if industry_score:
                industry_strength[industry] = industry_score

        # 取出最强的n个板块
        return self.get_top_selected(industry_strength, self.select_industry_amount)

    def select_strength_stocks_in_industry(self, strength_industry_codes):
        """ 获取强势板块里的强势股票 """

        strength_stocks_in_industry = dict()
        industries_names = get_industries(name='sw_l1')['name']
        compare_dapan_range = self.get_stock_range('000001.XSHG', self.stock_compare_days, self.strength_end_date)
        for index, code in enumerate(strength_industry_codes):
            stock_strength = dict()
            compare_industry_range = finance.run_query(query(finance.SW1_DAILY_PRICE)
                                                       .filter(finance.SW1_DAILY_PRICE.code == code,
                                                               finance.SW1_DAILY_PRICE.date >=
                                                               get_trade_days(count=self.stock_compare_days,
                                                                              end_date=self.strength_end_date)[
                                                                   0].strftime('%Y-%m-%d'),
                                                               finance.SW1_DAILY_PRICE.date <= self.strength_end_date)
                                                       .order_by(finance.SW1_DAILY_PRICE.date.asc()))['change_pct']

            # 对应行业里的强势股票
            industry_stocks = get_industry_stocks(code)
            for stock_code in industry_stocks:
                if not self.can_stock_operate(stock_code, self.strength_end_date):
                    continue
                # 获取个股的涨跌幅
                stock_range = self.get_stock_range(stock_code, self.stock_compare_days, self.strength_end_date)
                # 行业相对板块大盘强弱打分
                stock_score = self.get_score(stock_range, compare_industry_range,
                                             self.stock_compare_days) + self.get_score(
                    stock_range, compare_dapan_range, self.stock_compare_days)
                if stock_score:
                    stock_strength[stock_code] = stock_score

            # 取出每个板块里最强的10个个股
            strength_stock_codes = self.get_top_selected(stock_strength, self.select_stock_amount)
            strength_stocks_in_industry[code] = dict()
            strength_stocks_in_industry[code]['name'] = industries_names[code]
            strength_stocks_in_industry[code]['order'] = index
            strength_stocks_in_industry[code]['stocks'] = strength_stock_codes
        # send_message(json.dumps(industry_stock_strength))
        # log.info(json.dumps(industry_stock_strength))
        return strength_stocks_in_industry

    def select_fall_back_stocks(self, strength_stocks_in_industry):
        """ 获取强势股票里回落的股票 """
        prefer_stock_strength = dict()
        compare_dapan_range = self.get_stock_range('000001.XSHG', self.fall_back_days, self.select_end_date)
        for industry_select_stocks in strength_stocks_in_industry.values():
            if industry_select_stocks['order'] <= self.prefer_industry_order:
                # industry_name = industry_select_stocks['name']
                for index, stock_code in enumerate(industry_select_stocks['stocks']):
                    if index <= self.prefer_stock_order:
                        stock_range = self.get_stock_range(stock_code, self.fall_back_days, self.select_end_date)
                        stock_score = self.get_score(stock_range, compare_dapan_range, self.fall_back_days)
                        prefer_stock_strength[stock_code] = stock_score

        prefer_stock_codes = self.get_top_selected(prefer_stock_strength, self.prefer_stock_amount, False)
        # log.info(prefer_stock_codes)
        # send_message(prefer_stock_codes)
        return prefer_stock_codes

    # 选股用到的函数======================start==========================
    def get_stock_range(self, code, compare_days, select_end_date):
        stock = get_price(code,
                          count=compare_days + 1,
                          end_date=select_end_date,
                          frequency='daily', fields=['open', 'close'])
        stock_yesterday_close = stock.shift(1)
        return pd.Series(
            (((stock['close'] - stock_yesterday_close['close']) / stock_yesterday_close[
                'close']).dropna() * 100).values)

    def get_score(self, to_compare, base, compare_days):
        if to_compare.size == 0 or base.size == 0:
            return 0

        if to_compare.size != compare_days:
            print(
                f'warning: to_compare size is wrong, expect: {compare_days}, actual: {to_compare.size}, value: {to_compare}')
            to_compare = pd.Series((to_compare.append(pd.Series([0] * (compare_days - to_compare.size)))).values)
            print(to_compare)
        if base.size != compare_days:
            print(f'warning: base size is wrong, expect: {compare_days}, actual: {base.size}, value: {base}')
            base = pd.Series((base.append(pd.Series([0] * (compare_days - base.size)))).values)
            print(base)

        def restrain(number):
            '''
            缩紧猛涨猛跌对相对强弱的过大影响；
            '''
            if number <= 3 and number >= -3:
                return number
            elif number > 3:
                return number * 0.285 + 2.14
            else:
                return number * 0.285 - 2.14

        to_compare_restrain = to_compare.apply(restrain)
        # 添加一个相对时间对当前强弱的影响
        impact_coefficient = np.linspace(1, 1.1, compare_days)
        return (((to_compare - base) / base.abs()) * to_compare_restrain.abs() * impact_coefficient).sum()

    def get_top_selected(self, strength_map, select_amount, strong=True):
        strength_ordered = sorted(strength_map.items(), key=lambda x: x[1], reverse=strong)
        return [x[0] for x in strength_ordered][:select_amount]

    def can_stock_operate(self, stock_code, select_end_date):
        # 过滤掉ST, 科创板, 创业板， 新股
        if stock_code.startswith('688'):
            return False
        if stock_code.startswith('3'):
            return False
        if 'ST' in get_security_info(stock_code).display_name:
            return False
        if get_security_info(stock_code).start_date > (
                datetime.strptime(select_end_date, '%Y-%m-%d').date() + relativedelta(months=-6)):
            return False

        # 过滤亏损股
        net_profit = get_fundamentals(query(income.net_profit)
                                      .filter(valuation.code == stock_code), date=select_end_date)['net_profit']
        if (net_profit < 0).all():
            return False

        # 过滤三天连续下跌的股, 最近涨幅超过20个点的
        # stock_close_price = get_price(stock_code, count = 30, end_date=select_end_date, frequency='daily', fields=['open', 'close'])['close']
        # if (stock_close_price.max() - stock_close_price.min()) /stock_close_price.min() > 0.2:
        #     return False

        return True

    # 选股用到的函数======================end==========================


class Chan_Class:

    def __init__(self, freq, symbol, sell, buy, include=True, include_feature=False, build_pivot=False, qjt=True,
                 gz=False, buy1=100, buy2=200, buy3=200, sell1=100, sell2=200, sell3=200):

        self.freq = freq
        self.symbol = symbol
        self.prev = None
        self.next = None
        self.k_list = []
        self.chan_k_list = []
        self.fx_list = []
        self.stroke_list = []
        self.stroke_index_in_k = {}
        self.line_list = []
        self.line_index = {}
        self.line_index_in_k = {}
        self.line_feature = []
        self.s_feature = []
        self.x_feature = []

        self.pivot_list = []
        self.trend_list = []
        self.buy_list = []
        self.sell_list = []
        self.macd = {}
        self.buy = buy
        self.sell = sell
        self.buy1 = buy1
        self.buy2 = buy2
        self.buy3 = buy3
        self.sell1 = sell1
        self.sell2 = sell2
        self.sell3 = sell3
        # 动力减弱最小指标
        self.dynamic_reduce = 0
        # 笔生成方法，new, old
        # 是否进行K线包含处理
        self.include = include
        # 中枢生成方法，stroke, line
        # 使用笔还是线段作为中枢的构成, true使用线段
        self.build_pivot = build_pivot
        # 线段生成方法
        # 是否进行K线包含处理
        self.include_feature = include_feature
        # 是否使用区间套
        self.qjt = qjt
        # 是否使用共振
        # 采用买卖点共振组合方法，1分钟一类买卖点+5分钟二类买卖点或三类买卖点，都属于共振
        self.gz = gz
        # 计数
        self.gz_delay_k_num = 0
        # 最大
        self.gz_delay_k_max = 12
        # 潜在bs
        self.gz_tmp_bs = None
        # 高级别bs
        self.gz_prev_last_bs = None

    def set_prev(self, chan):
        self.prev = chan

    def set_next(self, chan):
        self.next = chan

    def on_bar(self, bar: BarData):
        self.k_list.append(bar)
        if self.gz and self.gz_tmp_bs:
            self.gz_delay_k_num += 1
            self.on_gz()
        if self.include:
            self.on_process_k_include(bar)
        else:
            self.on_process_k_no_include(bar)

    def on_process_k_include(self, bar: BarData):
        """合并k线"""
        if len(self.chan_k_list) < 2:
            self.chan_k_list.append(bar)
        else:
            pre_bar = self.chan_k_list[-2]
            last_bar = self.chan_k_list[-1]
            if (last_bar.high_price >= bar.high_price and last_bar.low_price <= bar.low_price) or (
                    last_bar.high_price <= bar.high_price and last_bar.low_price >= bar.low_price):
                if last_bar.high_price > pre_bar.high_price:
                    new_bar = copy(bar)
                    new_bar.high_price = max(last_bar.high_price, new_bar.high_price)
                    new_bar.low_price = max(last_bar.low_price, new_bar.low_price)
                    new_bar.open_price = max(last_bar.open_price, new_bar.open_price)
                    new_bar.close_price = max(last_bar.close_price, new_bar.close_price)
                else:
                    new_bar = copy(bar)
                    new_bar.high_price = min(last_bar.high_price, new_bar.high_price)
                    new_bar.low_price = min(last_bar.low_price, new_bar.low_price)
                    new_bar.open_price = min(last_bar.open_price, new_bar.open_price)
                    new_bar.close_price = min(last_bar.close_price, new_bar.close_price)

                self.chan_k_list[-1] = new_bar
                log.info(self.freq, self.symbol, "combine k line: " + str(new_bar.datetime))
            else:
                self.chan_k_list.append(bar)
            # 包含和非包含处理的k线都需要判断是否分型了
            self.on_process_fx(self.chan_k_list)

    def on_process_k_no_include(self, bar: BarData):
        """不用合并k线"""
        self.chan_k_list.append(bar)
        self.on_process_fx(self.chan_k_list)

    def on_process_fx(self, data):
        if len(data) > 2:
            flag = False
            if data[-2].high_price >= data[-1].high_price and data[-2].high_price >= data[-3].high_price:
                # 形成顶分型 [high_price, low, dt, direction, index of k_list]
                self.fx_list.append([data[-2].high_price, data[-2].low_price, data[-2].datetime, 'up', len(data) - 2])
                flag = True

            if data[-2].low_price <= data[-1].low_price and data[-2].low_price <= data[-3].low_price:
                # 形成底分型
                self.fx_list.append([data[-2].high_price, data[-2].low_price, data[-2].datetime, 'down', len(data) - 2])
                flag = True

            if flag:
                self.on_stroke(self.fx_list[-1])
                log.info(self.freq, self.symbol, "fx_list: ")
                log.info(self.freq, self.symbol, self.fx_list[-1])

    def on_stroke(self, data):
        """生成笔"""
        if len(self.stroke_list) < 1:
            self.stroke_list.append(data)
            log.info(self.freq, self.symbol, self.stroke_list)
        else:
            last_fx = self.stroke_list[-1]
            cur_fx = data
            pivot_flag = False
            # 分型之间需要超过三根chank线
            # 延申也是需要条件的
            if last_fx[3] == cur_fx[3]:
                if (last_fx[3] == 'down' and cur_fx[1] < last_fx[1]) or (
                        last_fx[3] == 'up' and cur_fx[0] > last_fx[0]):
                    # 笔延申
                    self.stroke_list[-1] = cur_fx
                    pivot_flag = True

            else:
                # if (cur_fx[4] - last_fx[4] > 3) and (
                #         (cur_fx[3] == 'down' and cur_fx[1] < last_fx[1] and cur_fx[0] < last_fx[0]) or (
                #         cur_fx[3] == 'up' and cur_fx[0] > last_fx[0] and cur_fx[1] > last_fx[1])):
                if (cur_fx[4] - last_fx[4] > 3) and (
                        (cur_fx[3] == 'down' and cur_fx[0] < last_fx[1]) or (
                        cur_fx[3] == 'up' and cur_fx[1] > last_fx[0])):
                    # 笔新增
                    self.stroke_list.append(cur_fx)
                    log.info(self.freq, self.symbol, "stroke_list: ")
                    log.info(self.freq, self.symbol, self.stroke_list[-1])
                    # log.info(self.freq, self.symbol, self.stroke_list)
                    pivot_flag = True

            # 修正倒数第二个分型是否是最高的顶分型或者是否是最低的底分型
            # 只修一笔，不修多笔
            start = -2
            stroke_change = None
            if pivot_flag and len(self.stroke_list) > 1:
                stroke_change = self.stroke_list[-2]
                if cur_fx[3] == 'down':
                    while len(self.fx_list) > abs(start) and self.fx_list[start][2] > self.stroke_list[-2][2]:
                        if self.fx_list[start][3] == 'up' and self.fx_list[start][0] > stroke_change[0]:
                            if len(self.stroke_list) < 3 or (cur_fx[4] - self.fx_list[start][4] > 3):
                                stroke_change = self.fx_list[start]
                        start -= 1
                else:
                    while len(self.fx_list) > abs(start) and self.fx_list[start][2] > self.stroke_list[-2][2]:
                        if self.fx_list[start][3] == 'down' and self.fx_list[start][1] < stroke_change[1]:
                            if len(self.stroke_list) < 3 or (cur_fx[4] - self.fx_list[start][4] > 3):
                                stroke_change = self.fx_list[start]
                        start -= 1
            if stroke_change and not stroke_change == self.stroke_list[-2]:
                log.info(self.freq, self.symbol, 'stroke_change')
                log.info(self.freq, self.symbol, stroke_change)
                self.stroke_list[-2] = stroke_change
                if len(self.stroke_list) > 2:
                    cur_fx = self.stroke_list[-2]
                    last_fx = self.stroke_list[-3]
                    self.macd[cur_fx[2]] = self.cal_macd(last_fx[4], cur_fx[4])
                # if cur_fx[4] - self.stroke_list[-2][4] < 4:
                #     self.stroke_list.pop()

            if self.build_pivot:
                self.on_line(self.stroke_list)
            else:
                if len(self.stroke_list) > 1:
                    cur_fx = self.stroke_list[-1]
                    last_fx = self.stroke_list[-2]
                    self.macd[cur_fx[2]] = self.cal_macd(last_fx[4], cur_fx[4])
                self.on_line(self.stroke_list)
                if pivot_flag:
                    self.on_pivot(self.stroke_list, None)

    def on_line(self, data):
        # line_list保持和stroke_list结构相同，都是由分型构成的
        # 特征序列则不同，
        if len(data) > 4:
            # log.info(self.freq, self.symbol, 'line_index:')
            # log.info(self.freq, self.symbol, self.line_index)
            pivot_flag = False
            if data[-1][3] == 'up' and data[-3][0] >= data[-1][0] and data[-3][0] >= data[-5][0]:
                if not self.line_list or self.line_list[-1][3] == 'down':
                    if not self.line_list or ((len(self.stroke_list) - 3) - self.line_index[
                        str(self.line_list[-1][2])] > 2 and self.line_list[-1][1] < data[-3][0]):
                        # 出现顶
                        self.line_list.append(data[-3])
                        self.line_index[str(self.line_list[-1][2])] = len(self.stroke_list) - 3
                        pivot_flag = True
                else:
                    # 延申顶
                    if self.line_list[-1][0] < data[-3][0]:
                        self.line_list[-1] = data[-3]
                        self.line_index[str(self.line_list[-1][2])] = len(self.stroke_list) - 3
                        pivot_flag = True
            if data[-1][3] == 'down' and data[-3][1] <= data[-1][1] and data[-3][1] <= data[-5][1]:
                if not self.line_list or self.line_list[-1][3] == 'up':
                    if not self.line_list or ((len(self.stroke_list) - 3) - self.line_index[
                        str(self.line_list[-1][2])] > 2 and self.line_list[-1][0] > data[-3][1]):
                        # 出现底
                        self.line_list.append(data[-3])
                        self.line_index[str(self.line_list[-1][2])] = len(self.stroke_list) - 3
                        pivot_flag = True
                else:
                    # 延申底
                    if self.line_list[-1][1] > data[-3][1]:
                        self.line_list[-1] = data[-3]
                        self.line_index[str(self.line_list[-1][2])] = len(self.stroke_list) - 3
                        pivot_flag = True

            line_change = None
            if pivot_flag and len(self.line_list) > 1:
                last_fx = self.line_list[-2]
                line_change = last_fx
                cur_fx = self.line_list[-1]
                cur_index = self.line_index[str(cur_fx[2])]
                start = -6
                last_index = self.line_index[str(last_fx[2])]
                if cur_index - last_index > 3:
                    while len(self.stroke_list) >= abs(start - 2) and self.stroke_list[start][2] > last_fx[2]:
                        if cur_fx[3] == 'down' and self.stroke_list[start][0] > self.stroke_list[start + 2][0] and \
                                self.stroke_list[start][0] > self.stroke_list[start - 2][0] and self.stroke_list[start][
                            0] > line_change[0]:
                            line_change = self.stroke_list[start]
                        if cur_fx[3] == 'up' and self.stroke_list[start][1] < self.stroke_list[start + 2][1] and \
                                self.stroke_list[start][1] < self.stroke_list[start - 2][1] and self.stroke_list[start][
                            1] < line_change[1]:
                            line_change = self.stroke_list[start]
                        start -= 2

            if line_change and not line_change == self.line_list[-2]:
                log.info(self.freq, self.symbol, 'line_change')
                log.info(self.freq, self.symbol, line_change)
                log.info(self.freq, self.symbol, self.line_list)
                self.line_index[str(line_change[2])] = self.line_index[str(self.line_list[-2][2])]
                self.line_list[-2] = line_change
                if len(self.line_list) > 2:
                    cur_fx = self.line_list[-2]
                    last_fx = self.line_list[-3]
                    self.macd[cur_fx[2]] = self.cal_macd(last_fx[4], cur_fx[4])

            if self.line_list and self.build_pivot:
                if len(self.line_list) > 1:
                    cur_fx = self.line_list[-1]
                    last_fx = self.line_list[-2]
                    self.macd[cur_fx[2]] = self.cal_macd(last_fx[4], cur_fx[4])
                log.info(self.freq, self.symbol, 'line_list:')
                log.info(self.freq, self.symbol, self.line_list[-1])
                self.on_pivot(self.line_list, None)

    def on_pivot(self, data, type):
        # 中枢列表[[日期1，日期2，中枢低点，中枢高点, 中枢类型，中枢进入段，中枢离开段, 形成时间, GG, DD,BS,BS,TS]]]
        # 日期1：中枢开始的时间
        # 日期2：中枢结束的时间，可能延申
        # 中枢类型： ‘up', 'down'
        # BS: 买点
        # BS: 卖点
        # TS: 背驰段
        if len(data) > 5:
            # 构成笔或者是线段的分型
            cur_fx = data[-1]
            last_fx = data[-2]
            new_pivot = None
            flag = False
            # 构成新的中枢
            # 判断形成新的中枢的可能性
            if not self.pivot_list or (len(self.pivot_list) > 0 and len(data) - self.pivot_list[-1][6] > 4):
                cur_pivot = [data[-5][2], last_fx[2]]
                if cur_fx[3] == 'down' and data[-2][0] > data[-5][1]:
                    ZD = max(data[-3][1], data[-5][1])
                    ZG = min(data[-2][0], data[-4][0])
                    DD = min(data[-3][1], data[-5][1])
                    GG = max(data[-2][0], data[-4][0])
                    if ZG > ZD:
                        cur_pivot.append(ZD)
                        cur_pivot.append(ZG)
                        cur_pivot.append('down')
                        cur_pivot.append(len(data) - 5)
                        cur_pivot.append(len(data) - 2)
                        cur_pivot.append(cur_fx[2])
                        cur_pivot.append(GG)
                        cur_pivot.append(DD)
                        cur_pivot.append([[], [], []])
                        cur_pivot.append([[], [], []])
                        cur_pivot.append([])
                        new_pivot = cur_pivot
                        # 中枢形成，判断背驰
                if cur_fx[3] == 'up' and data[-2][1] < data[-5][0]:
                    ZD = max(data[-2][1], data[-4][1])
                    ZG = min(data[-3][0], data[-5][0])
                    DD = min(data[-2][1], data[-4][1])
                    GG = max(data[-3][0], data[-5][0])
                    if ZG > ZD:
                        cur_pivot.append(ZD)
                        cur_pivot.append(ZG)
                        cur_pivot.append('up')
                        cur_pivot.append(len(data) - 5)
                        cur_pivot.append(len(data) - 2)
                        cur_pivot.append(cur_fx[2])
                        cur_pivot.append(GG)
                        cur_pivot.append(DD)
                        cur_pivot.append([[], [], []])
                        cur_pivot.append([[], [], []])
                        cur_pivot.append([])
                        new_pivot = cur_pivot
                if not self.pivot_list:
                    if new_pivot:
                        flag = True
                else:
                    last_pivot = self.pivot_list[-1]
                    if new_pivot and ((new_pivot[2] > last_pivot[3] and cur_fx[3] == 'up') or (
                            new_pivot[3] < last_pivot[2] and cur_fx[3] == 'down')):
                        flag = True
                    if type and new_pivot and type == new_pivot[4]:
                        flag = True

            if len(self.pivot_list) > 0 and not flag:
                last_pivot = self.pivot_list[-1]
                ts = last_pivot[12]
                # 由于stroke/line_change，不断change中枢
                start = last_pivot[5]
                # 防止异常
                if len(data) <= start:
                    self.pivot_list.pop()
                    if not self.pivot_list:
                        return
                    last_pivot = self.pivot_list[-1]
                    start = last_pivot[5]
                buy = last_pivot[10]
                sell = last_pivot[11]
                enter = data[start][2]
                exit = cur_fx[2]
                ee_data = [[data[start - 1], data[start]],
                           [data[len(data) - 2], data[len(data) - 1]]]

                if last_pivot[4] == 'up':
                    # stroke_change导致的笔减少了
                    if len(data) > start + 3:
                        last_pivot[2] = max(data[start + 1][1], data[start + 3][1])
                        last_pivot[3] = min(data[start][0], data[start + 2][0])
                        last_pivot[8] = max(data[start][0], data[start + 2][0])
                        last_pivot[9] = min(data[start + 1][1], data[start + 3][1])
                    if cur_fx[3] == 'up':
                        if sell[0]:
                            # 一卖后的顶分型判断一卖是否有效，无效则将上一个一卖置为无效
                            if sell[0][1] < cur_fx[0] and len(data) - last_pivot[6] < 3:
                                # 置一卖无效
                                sell[0][5] = 0
                                sell[0][6] = self.k_list[-1].datetime
                                sell[0] = []
                                # 置二卖无效
                                if sell[1]:
                                    sell[1][5] = 0
                                    sell[1][6] = self.k_list[-1].datetime
                                    sell[1] = []
                        # 判断背驰
                        if self.on_turn(enter, exit, ee_data, last_pivot[4]) and cur_fx[0] > last_pivot[8]:
                            ts.append([last_fx[2], cur_fx[2]])
                            if not sell[0]:
                                # 形成一卖
                                ans, qjt_pivot_list = self.qjt_turn(last_fx[2], cur_fx[2], 'up')
                                if ans:
                                    sell[0] = [cur_fx[2], cur_fx[0], 'S1', self.k_list[-1].datetime, len(data) - 1, 1,
                                               None, self.cal_bs_type(), None, qjt_pivot_list]
                                    self.on_buy_sell(sell[0])
                        if sell[0] and not sell[1]:
                            pos_sell1 = sell[0][4]
                            if len(data) > pos_sell1 + 2:
                                pos_fx = data[pos_sell1 + 2]
                                if pos_fx[3] == 'up':
                                    if pos_fx[1] < sell[0][1]:
                                        # 形成二卖
                                        ans, qjt_pivot_list = self.qjt_trend(last_fx[2], cur_fx[2], 'up')
                                        if ans:
                                            sell[1] = [pos_fx[2], pos_fx[0], 'S2', self.k_list[-1].datetime,
                                                       pos_sell1 + 2, 1, None, self.cal_bs_type(), None, qjt_pivot_list]
                                        self.on_buy_sell(sell[1])
                                    else:
                                        # 一卖无效
                                        sell[0][5] = 0
                                        sell[0][6] = self.k_list[-1].datetime
                                        sell[0] = []

                        if cur_fx[0] < last_pivot[2] and not sell[2] and not buy[0]:
                            # 形成三卖
                            ans, qjt_pivot_list = self.qjt_trend(last_fx[2], cur_fx[2], 'up')
                            if ans:
                                condition = len(data) > 2 and data[-3][0] < last_pivot[2] and data[-3][2] > last_pivot[
                                    1]
                                if not condition:
                                    sell[2] = [cur_fx[2], cur_fx[0], 'S3', self.k_list[-1].datetime, len(data) - 1, 1,
                                               None, self.cal_bs_type(), None, qjt_pivot_list]
                                    self.on_buy_sell(sell[2])

                        # if (not last_fx[1] > last_pivot[3]) and (not cur_fx[0] < last_pivot[2]):
                        #     last_pivot[1] = cur_fx[2]
                        #     last_pivot[6] = len(data) - 1

                    else:
                        # 判断是否延申
                        if (not cur_fx[1] > last_pivot[3]) and (not last_fx[0] < last_pivot[2]):
                            last_pivot[1] = cur_fx[2]
                            last_pivot[6] = len(data) - 1
                        else:
                            # 判断形成第三类买点
                            if cur_fx[1] > last_pivot[2] and not buy[2] and not sell[0]:
                                ans, qjt_pivot_list = self.qjt_trend(last_fx[2], cur_fx[2], 'down')
                                if ans:
                                    condition = len(data) > 2 and data[-3][1] > last_pivot[3] and data[-3][2] > \
                                                last_pivot[1]
                                    if not condition:
                                        sth_pivot = last_pivot
                                        # if len(self.pivot_list) > 1:
                                        #     sth_pivot = self.pivot_list[-2]
                                        buy[2] = [cur_fx[2], cur_fx[1], 'B3', self.k_list[-1].datetime, len(data) - 1,
                                                  1, None, self.cal_bs_type(),
                                                  self.cal_b3_strength(cur_fx[1], sth_pivot), qjt_pivot_list]
                                        log.info(self.freq, self.symbol, 'B3-pivot')
                                        log.info(self.freq, self.symbol, sth_pivot)
                                        log.info(self.freq, self.symbol, buy[2])
                                        self.on_buy_sell(buy[2])


                else:
                    # stroke_change导致的笔减少了
                    if len(data) > start + 3:
                        last_pivot[2] = max(data[start][1], data[start + 2][1])
                        last_pivot[3] = min(data[start + 1][0], data[start + 3][0])
                        last_pivot[8] = max(data[start + 1][0], data[start + 3][0])
                        last_pivot[9] = min(data[start][1], data[start + 2][1])
                    if cur_fx[3] == 'down':
                        if buy[0]:
                            # 一买后的底分型判断一买是否有效，无效则将上一个一买置为无效
                            if buy[0][1] > cur_fx[1] and len(data) - last_pivot[6] < 3:
                                # 置一买无效
                                buy[0][5] = 0
                                buy[0][6] = self.k_list[-1].datetime
                                buy[0] = []
                                # 置二买无效
                                if buy[1]:
                                    buy[1][5] = 0
                                    buy[1][6] = self.k_list[-1].datetime
                                    buy[1] = []

                        # 判断背驰
                        if self.on_turn(enter, exit, ee_data, last_pivot[4]) and cur_fx[1] < last_pivot[9]:
                            ts.append([last_fx[2], cur_fx[2]])
                            if not buy[0]:
                                # 形成一买
                                ans, qjt_pivot_list = self.qjt_turn(last_fx[2], cur_fx[2], 'down')
                                if ans:
                                    buy[0] = [cur_fx[2], cur_fx[1], 'B1', self.k_list[-1].datetime, len(data) - 1, 1,
                                              None, self.cal_bs_type(), None, qjt_pivot_list]
                                    if self.gz:
                                        self.gz_prev_last_bs = self.get_prev_last_bs()
                                        self.gz_tmp_bs = buy
                                        buy[0][5] = 0
                                    else:
                                        self.on_buy_sell(buy[0])

                        if buy[0] and buy[0][5] == 1 and not buy[1]:
                            pos_buy1 = buy[0][4]
                            if len(data) > pos_buy1 + 2:
                                pos_fx = data[pos_buy1 + 2]
                                if pos_fx[3] == 'down':
                                    if pos_fx[1] > buy[0][1]:
                                        # 形成二买
                                        ans, qjt_pivot_list = self.qjt_trend(last_fx[2], cur_fx[2], 'down')
                                        if ans:
                                            sth_pivot = last_pivot
                                            # if len(self.pivot_list) > 1:
                                            #     sth_pivot = self.pivot_list[-2]
                                            buy[1] = [pos_fx[2], pos_fx[1], 'B2', self.k_list[-1].datetime,
                                                      pos_buy1 + 2, 1, None, self.cal_bs_type(),
                                                      self.cal_b2_strength(pos_fx[1], last_fx, sth_pivot),
                                                      qjt_pivot_list]
                                            self.on_buy_sell(buy[1])
                                    else:
                                        # 一买无效
                                        buy[0][5] = 0
                                        buy[0][6] = self.k_list[-1].datetime
                                        buy[0] = []

                        if cur_fx[1] > last_pivot[3] and not buy[2] and not sell[0]:
                            # 形成三买
                            ans, qjt_pivot_list = self.qjt_trend(last_fx[2], cur_fx[2], 'down')
                            if ans:
                                condition = len(data) > 2 and data[-3][1] > last_pivot[3] and data[-3][2] > \
                                            last_pivot[1]
                                if not condition:
                                    sth_pivot = last_pivot
                                    # if len(self.pivot_list) > 1:
                                    #     sth_pivot = self.pivot_list[-2]
                                    buy[2] = [cur_fx[2], cur_fx[1], 'B3', self.k_list[-1].datetime, len(data) - 1, 1,
                                              None, self.cal_bs_type(), self.cal_b3_strength(cur_fx[1], sth_pivot),
                                              qjt_pivot_list]
                                    log.info(self.freq, self.symbol, 'B3-pivot')
                                    log.info(self.freq, self.symbol, sth_pivot)
                                    log.info(self.freq, self.symbol, buy[2])
                                    self.on_buy_sell(buy[2])

                        # if (not cur_fx[1] > last_pivot[3]) and (not last_fx[0] < last_pivot[2]):
                        #     last_pivot[1] = cur_fx[2]
                        #     last_pivot[6] = len(data) - 1
                    else:
                        # 判断是否延申
                        if (not last_fx[1] > last_pivot[3]) and (not cur_fx[0] < last_pivot[2]):
                            last_pivot[1] = cur_fx[2]
                            last_pivot[6] = len(data) - 1
                        else:
                            # 判断形成第三类卖点
                            if cur_fx[1] < last_pivot[3] and not sell[2] and not buy[0]:
                                ans, qjt_pivot_list = self.qjt_trend(last_fx[2], cur_fx[2], 'up')
                                if ans:
                                    condition = len(data) > 2 and data[-3][0] < last_pivot[2] and data[-3][2] > \
                                                last_pivot[1]
                                    if not condition:
                                        sell[2] = [cur_fx[2], cur_fx[0], 'S3', self.k_list[-1].datetime, len(data) - 1,
                                                   1, None, self.cal_bs_type(), None, qjt_pivot_list]
                                        self.on_buy_sell(sell[2])

                # 判断一二类买卖点失效
                if len(self.pivot_list) > 1:
                    pre = self.pivot_list[-2]
                    pre_buy = pre[10]
                    pre_sell = pre[11]
                    if pre_sell[0] and not pre_sell[1]:
                        pos_sell1 = pre_sell[0][4]
                        if len(data) > pos_sell1 + 2:
                            pos_fx = data[pos_sell1 + 2]
                            if pos_fx[3] == 'up':
                                if pos_fx[0] < pre_sell[0][1]:
                                    # 形成二卖
                                    pre_sell[1] = [pos_fx[2], pos_fx[0], 'S2', self.k_list[-1].datetime, pos_sell1 + 2,
                                                   1, None, pre_sell[0][7], None]
                                    self.on_buy_sell(pre_sell[1])
                                else:
                                    # 一卖无效
                                    pre_sell[0][5] = 0
                                    pre_sell[0][6] = self.k_list[-1].datetime
                                    pre_sell[0] = []

                    if pre_buy[0] and pre_buy[0][5] == 1 and not pre_buy[1]:
                        pos_buy1 = pre_buy[0][4]
                        if len(data) > pos_buy1 + 2:
                            pos_fx = data[pos_buy1 + 2]
                            if pos_fx[3] == 'down':
                                if pos_fx[1] > pre_buy[0][1]:
                                    sth_pivot = None
                                    # if len(self.pivot_list) > 2:
                                    #     sth_pivot = self.pivot_list[-3]
                                    if len(self.pivot_list) > 1:
                                        sth_pivot = self.pivot_list[-2]
                                    # 形成二买
                                    pre_buy[1] = [pos_fx[2], pos_fx[1], 'B2', self.k_list[-1].datetime, pos_buy1 + 2, 1,
                                                  None, pre_buy[0][7],
                                                  self.cal_b2_strength(pos_fx[1], data[pos_buy1 + 1], sth_pivot)]
                                    self.on_buy_sell(pre_buy[1])
                                else:
                                    # 一买无效
                                    pre_buy[0][5] = 0
                                    pre_buy[0][6] = self.k_list[-1].datetime
                                    pre_buy[0] = []

                    # B2失效的判断标准：以B2为起点的笔的顶不大于反转笔的顶。
                    # 判断条件有问题
                    if pre_buy[1] and len(data) > pre_buy[1][4] + 2:
                        start = pre_buy[1][4] + 1
                        if data[start] < data[start - 2]:
                            if pre_buy[0]:
                                # 一买无效
                                pre_buy[0][5] = 0
                                pre_buy[0][6] = self.k_list[-1].datetime
                                pre_buy[0] = []
                                pre_buy[1][5] = 0
                                pre_buy[1][6] = self.k_list[-1].datetime
                                pre_buy[1] = []

                    sth_pivot = None
                    # if len(self.pivot_list) > 2:
                    #     sth_pivot = self.pivot_list[-3]
                    if len(self.pivot_list) > 1:
                        sth_pivot = self.pivot_list[-2]
                    self.x_bs_pos(data, pre_buy, pre_sell, pre, sth_pivot)

                if len(self.pivot_list) > 2:
                    pre2 = self.pivot_list[-3]
                    pre_buy = pre2[10]
                    pre_sell = pre2[11]
                    pre1 = self.pivot_list[-2]
                    if pre1[3] < last_pivot[2] and pre2[3] < pre1[2]:
                        # 上升趋势
                        if pre_sell[0]:
                            # 置一卖无效
                            pre_sell[0][5] = 0
                            pre_sell[0][6] = self.k_list[-1].datetime
                            pre_sell[0] = []

                        if pre_sell[1]:
                            # 置二卖无效
                            pre_sell[1][5] = 0
                            pre_sell[1][6] = self.k_list[-1].datetime
                            pre_sell[1] = []
                    # if pre1[2] > last_pivot[3]:
                    #     # 下降趋势
                    #     if pre_buy[0]:
                    #         # 置一买无效
                    #         pre_buy[0][5] = 0
                    #         pre_buy[0][6] = self.k_list[-1].datetime
                    #         pre_buy[0] = []
                    #
                    #     if pre_buy[1]:
                    #         # 置二买无效
                    #         pre_buy[1][5] = 0
                    #         pre_buy[1][6] = self.k_list[-1].datetime
                    #         pre_buy[1] = []
                # 判断三类买卖点失效
                if sell[2] and sell[2][0] < last_pivot[1]:
                    sell[2][5] = 0
                    sell[2][6] = self.k_list[-1].datetime
                    sell[2] = []

                if buy[2] and buy[2][0] < last_pivot[1]:
                    buy[2][5] = 0
                    buy[2][6] = self.k_list[-1].datetime
                    buy[2] = []
                sth_pivot = last_pivot
                # if len(self.pivot_list) > 1:
                #     sth_pivot = self.pivot_list[-2]
                self.x_bs_pos(data, buy, sell, last_pivot, sth_pivot)

            if flag:
                if new_pivot:
                    self.pivot_list.append(new_pivot)
                    # 中枢形成，判断背驰
                    ts = new_pivot[12]
                    buy = new_pivot[10]
                    sell = new_pivot[11]
                    enter = data[new_pivot[5]][2]
                    exit = data[new_pivot[6]][2]
                    ee_data = [[data[new_pivot[5] - 1], data[new_pivot[5]]],
                               [data[new_pivot[6] - 1], data[new_pivot[6]]]]
                    if new_pivot[4] == 'up':
                        if self.on_turn(enter, exit, ee_data, new_pivot[4]) and cur_fx[0] > new_pivot[8]:
                            ts.append([last_fx[2], cur_fx[2]])
                            if not sell[0]:
                                # 形成一卖
                                ans, qjt_pivot_list = self.qjt_turn(last_fx[2], cur_fx[2], 'up')
                                if ans:
                                    sell[0] = [cur_fx[2], cur_fx[0], 'S1', self.k_list[-1].datetime, len(data) - 1, 1,
                                               None, self.cal_bs_type(), None, qjt_pivot_list]
                                    self.on_buy_sell(sell[0])

                    if new_pivot[4] == 'down':
                        if self.on_turn(enter, exit, ee_data, new_pivot[4]) and cur_fx[1] < new_pivot[9]:
                            ts.append([last_fx[2], cur_fx[2]])
                            if not buy[0]:
                                # 形成一买
                                ans, qjt_pivot_list = self.qjt_turn(last_fx[2], cur_fx[2], 'down')
                                if ans:
                                    buy[0] = [cur_fx[2], cur_fx[1], 'B1', self.k_list[-1].datetime, len(data) - 1, 1,
                                              None, self.cal_bs_type(), None, qjt_pivot_list]
                                    if self.gz:
                                        self.gz_prev_last_bs = self.get_prev_last_bs()
                                        self.gz_tmp_bs = buy
                                        buy[0][5] = 0
                                    else:
                                        self.on_buy_sell(buy[0])

                    log.info(self.freq, self.symbol, "pivot_list:")
                    log.info(self.freq, self.symbol, new_pivot)
                    self.on_trend(new_pivot, data)

    def x_bs_pos(self, data, buy, sell, last_pivot, sth_pivot):
        if not self.gz:
            if buy[0] and len(data) > buy[0][4] and data[buy[0][4]][2] != buy[0][0]:
                pos_fx = data[buy[0][4]]
                buy[0][5] = 0
                buy[0][6] = self.k_list[-1].datetime
                # B1<DD
                buy[0] = [pos_fx[2], pos_fx[1], 'B1', self.k_list[-1].datetime, buy[0][4], 1, None, buy[0][7], None]
                self.on_buy_sell(buy[0])

        if sell[0] and len(data) > sell[0][4] and data[sell[0][4]][2] != sell[0][0]:
            pos_fx = data[sell[0][4]]
            sell[0][5] = 0
            sell[0][6] = self.k_list[-1].datetime
            # S1>GG
            sell[0] = [pos_fx[2], pos_fx[0], 'S1', self.k_list[-1].datetime, sell[0][4], 1, None, sell[0][7], None]
            self.on_buy_sell(sell[0])

        if buy[1] and len(data) > buy[1][4] and data[buy[1][4]][2] != buy[1][0]:
            pos_fx = data[buy[1][4]]
            buy[1][5] = 0
            buy[1][6] = self.k_list[-1].datetime
            if buy[0]:
                if pos_fx[1] > buy[0][1]:
                    # todo 笔延申重新判断为强弱
                    buy[1] = [pos_fx[2], pos_fx[1], 'B2', self.k_list[-1].datetime, buy[1][4], 1, None, buy[1][7],
                              self.cal_b2_strength(pos_fx[1], data[buy[1][4]], sth_pivot)]
                    self.on_buy_sell(buy[1])
                else:
                    # 一买无效
                    buy[0][5] = 0
                    buy[0][6] = self.k_list[-1].datetime

        if sell[1] and len(data) > sell[1][4] and data[sell[1][4]][2] != sell[1][0]:
            pos_fx = data[sell[1][4]]
            sell[1][5] = 0
            sell[1][6] = self.k_list[-1].datetime

            if pos_fx[0] < sell[0][1]:
                sell[1] = [pos_fx[2], pos_fx[0], 'S2', self.k_list[-1].datetime, sell[1][4], 1, None, sell[1][7], None]
                self.on_buy_sell(sell[1])
            else:
                # 一卖无效
                sell[0][5] = 0
                sell[0][6] = self.k_list[-1].datetime

        if buy[2] and len(data) > buy[2][4] and data[buy[2][4]][2] != buy[2][0] and buy[2][0] > last_pivot[1]:
            pos_fx = data[buy[2][4]]
            buy[2][5] = 0
            buy[2][6] = self.k_list[-1].datetime
            if pos_fx[1] > last_pivot[3]:
                buy[2] = [pos_fx[2], pos_fx[1], 'B3', self.k_list[-1].datetime, buy[2][4], 1, None, buy[2][7],
                          self.cal_b3_strength(pos_fx[1], sth_pivot)]
                log.info(self.freq, self.symbol, 'B3-pivot')
                log.info(self.freq, self.symbol, sth_pivot)
                log.info(self.freq, self.symbol, buy[2])
                self.on_buy_sell(buy[2])
        if sell[2] and len(data) > sell[2][4] and data[sell[2][4]][2] != sell[2][0] and sell[2][0] > last_pivot[1]:
            pos_fx = data[sell[2][4]]
            sell[2][5] = 0
            sell[2][6] = self.k_list[-1].datetime
            if pos_fx[0] < last_pivot[2]:
                sell[2] = [pos_fx[2], pos_fx[0], 'S3', self.k_list[-1].datetime, sell[2][4], 1, None, sell[2][7], None]
                self.on_buy_sell(sell[2])

    def cal_bs_type(self):
        if len(self.pivot_list) > 1 and self.pivot_list[-1][4] == self.pivot_list[-2][4]:
            return '趋势'
        return '盘整'

    def cal_b3_strength(self, price, last_pivot):
        if last_pivot:
            if price > last_pivot[8]:
                return '强'
        return '弱'

    def cal_b2_strength(self, price, fx, last_pivot):
        if last_pivot:
            if price > last_pivot[3]:
                return '超强'
            if fx[0] > last_pivot[3]:
                return '强'
            if fx[0] > last_pivot[2]:
                return '中'
        return '弱'

    def cal_macd(self, start, end):
        sum = 0
        if start >= end:
            return sum
        if self.include:
            close_list = np.array([x.close_price for x in self.chan_k_list], dtype=np.double)
        else:
            close_list = np.array([x.close_price for x in self.k_list], dtype=np.double)
        dif, dea, macd = tl.MACD(close_list, fastperiod=12,
                                 slowperiod=26, signalperiod=9)
        for i, v in enumerate(macd.tolist()):
            if start <= i <= end:
                sum += abs(round(v, 4))
        return round(sum, 4)

    def on_turn(self, start, end, ee_data, type):
        # ee_data: 笔/段列表 [[start, end]]
        # 判断背驰
        start_macd = None
        if start in self.macd:
            start_macd = self.macd[start]
        end_macd = None
        if end in self.macd:
            end_macd = self.macd[end]
        if start_macd and end_macd:
            if math.isnan(start_macd) or math.isnan(end_macd):
                if len(ee_data) > 1:
                    if type == 'down':
                        enter_slope = (ee_data[0][0][0] - ee_data[0][1][1]) / (ee_data[0][1][4] - ee_data[0][0][4] + 1)
                        exit_slope = (ee_data[1][0][0] - ee_data[1][1][1]) / (ee_data[1][1][4] - ee_data[1][0][4] + 1)
                        return abs(enter_slope) > abs(exit_slope)
                    else:
                        enter_slope = (ee_data[0][0][1] - ee_data[0][1][0]) / (ee_data[0][1][4] - ee_data[0][0][4] + 1)
                        exit_slope = (ee_data[1][0][1] - ee_data[1][1][0]) / (ee_data[1][1][4] - ee_data[1][0][4] + 1)
                        return abs(enter_slope) > abs(exit_slope)
            else:
                return start_macd > end_macd
        return False

    def qjt_turn0(self, start, end, type):
        # 区间套判断背驰：判断有无中枢和qjt_trend相同
        qjt_pivot_list = []
        if not self.qjt:
            return True, qjt_pivot_list
        chan = self.next
        if not chan:
            return True, qjt_pivot_list
        ans = False
        log.info(self.freq, self.symbol, '区间套判断背驰：')
        log.info(self.freq, self.symbol, self.freq)
        log.info(self.freq, self.symbol, str(self.pivot_list[-1]) + ':' + str(start))
        while chan:
            last_pivot = chan.pivot_list[-1]
            tmp = False
            if last_pivot[1] > start:
                if last_pivot[11][0]:
                    tmp = True
                    start = chan.stroke_list[last_pivot[11][0][4] - 1][2]
                    if chan.build_pivot:
                        start = chan.stroke_list[last_pivot[11][0][4] - 1][2]
                if last_pivot[10][0]:
                    tmp = True
                    start = chan.stroke_list[last_pivot[10][0][4] - 1][2]
                    if chan.build_pivot:
                        start = chan.stroke_list[last_pivot[10][0][4] - 1][2]
            log.info(self.freq, self.symbol, chan.freq + ':' + str(tmp))
            log.info(self.freq, self.symbol, str(last_pivot) + ':' + str(start))
            ans = ans or tmp
            chan = chan.next
        return ans, qjt_pivot_list

    def qjt_turn1(self, start, end, type):
        # 区间套判断背驰: 利用低级别的买卖点
        qjt_pivot_list = []
        if not self.qjt:
            return True, qjt_pivot_list
        chan = self.next
        if not chan:
            return True, qjt_pivot_list
        ans = False
        log.info(self.freq, self.symbol, '区间套判断背驰：')
        log.info(self.freq, self.symbol, self.freq)
        log.info(self.freq, self.symbol, str(self.pivot_list[-1]) + ':' + str(start))
        while chan:
            tmp = False
            for i in range(-1, -len(chan.buy_list), -1):
                buy_dt = chan.buy_list[i]
                if buy_dt >= end and buy_dt < start:
                    tmp = True
                    break
            tmp = False
            for i in range(-1, -len(chan.sell_list), -1):
                sell_dt = chan.sell_list[i]
                if sell_dt >= end and sell_dt < start:
                    tmp = True
                    break
            ans = ans or tmp
            chan = chan.next
        return ans, qjt_pivot_list

    def qjt_pivot(self, data, type):
        chan_pivot = Chan_Class(freq=self.freq, symbol=self.symbol, sell=None, buy=None, include=self.include,
                                include_feature=self.include_feature, build_pivot=self.build_pivot, qjt=False)
        chan_pivot.macd = self.macd
        chan_pivot.k_list = self.chan_k_list
        new_data = []
        for d in data:
            new_data.append(d)
            chan_pivot.on_pivot(new_data, type)
        return chan_pivot.pivot_list

    def qjt_turn(self, start, end, type):
        # 区间套判断背驰：重新形成新的中枢和买卖点
        qjt_pivot_list = []
        # if not self.qjt:
        #     return True, qjt_pivot_list
        chan = self.next
        if not chan:
            return True, qjt_pivot_list
        ans = True
        log.info(self.freq, self.symbol, '区间套判断背驰：')
        log.info(self.freq, self.symbol, self.freq)

        while chan:
            tmp = False
            data = []
            if chan.build_pivot:
                for i in range(-1, -len(chan.line_list), -1):
                    d = chan.line_list[i]
                    if d[2] >= start:
                        if d[2] <= end:
                            data.append(d)
                    else:
                        if type == 'up' and d[3] == 'down':
                            data.append(d)
                        if type == 'down' and d[3] == 'up':
                            data.append(d)
                        break
            else:
                for i in range(-1, -len(chan.stroke_list), -1):
                    d = chan.stroke_list[i]
                    if d[2] >= start:
                        if d[2] <= end:
                            data.append(d)
                    else:
                        if type == 'up' and d[3] == 'down':
                            data.append(d)
                        if type == 'down' and d[3] == 'up':
                            data.append(d)
                        break
            data.reverse()
            chan_pivot_list = chan.qjt_pivot(data, type)
            log.info(self.freq, self.symbol, str(self.pivot_list[-1]) + ':' + str(start))
            log.info(self.freq, self.symbol, chan_pivot_list)
            qjt_pivot_list.append(chan_pivot_list)
            if chan_pivot_list and len(chan_pivot_list[-1][12]) > 0:
                ts_item = chan_pivot_list[-1][12][-1]
                start = ts_item[0]
                end = ts_item[1]
                tmp = True
                chan = chan.next

            ans = tmp and ans
            if not ans:
                break

        return ans, qjt_pivot_list

    def qjt_trend0(self, start, end, type):
        # 区间套判断有无走势：判断有无中枢
        qjt_pivot_list = []
        if not self.qjt:
            return True, qjt_pivot_list
        log.info(self.freq, self.symbol, '区间套判断有无走势：')
        log.info(self.freq, self.symbol, str(start) + '--' + str(end))
        log.info(self.freq, self.symbol, str(self.pivot_list[-1]))
        chan = self.next
        if not chan:
            return True, qjt_pivot_list
        ans = False
        while chan:
            tmp = False
            for i in range(-1, -len(chan.pivot_list), -1):
                last_pivot = chan.pivot_list[i]
                if last_pivot[1] <= end and last_pivot[0] >= start:
                    tmp = True
                    break
            ans = ans or tmp
            log.info(self.freq, self.symbol, chan.freq + ':' + str(tmp))
            chan = chan.next
        return ans, qjt_pivot_list

    def qjt_trend(self, start, end, type):
        # 区间套判断有无走势：重新形成中枢
        qjt_pivot_list = []
        if not self.qjt:
            return True, qjt_pivot_list
        chan = self.next
        if not chan:
            return True, qjt_pivot_list
        ans = False
        log.info(self.freq, self.symbol, '区间套判断背驰：')
        log.info(self.freq, self.symbol, self.freq)

        while chan:
            tmp = False
            data = []
            if chan.build_pivot:
                for i in range(-1, -len(chan.line_list), -1):
                    d = chan.line_list[i]
                    if d[2] >= start:
                        if d[2] <= end:
                            data.append(d)
                    else:
                        if type == 'up' and d[3] == 'down':
                            data.append(d)
                        if type == 'down' and d[3] == 'up':
                            data.append(d)
                        break
            else:
                for i in range(-1, -len(chan.stroke_list), -1):
                    d = chan.stroke_list[i]
                    if d[2] >= start:
                        if d[2] <= end:
                            data.append(d)
                    else:
                        if type == 'up' and d[3] == 'down':
                            data.append(d)
                        if type == 'down' and d[3] == 'up':
                            data.append(d)
                        break
            data.reverse()
            chan_pivot_list = chan.qjt_pivot(data, type)
            log.info(self.freq, self.symbol, str(self.pivot_list[-1]) + ':' + str(start))
            log.info(self.freq, self.symbol, chan_pivot_list)
            qjt_pivot_list.append(chan_pivot_list)
            if not len(chan_pivot_list) > 0:
                chan = chan.next
            else:
                tmp = True
            ans = tmp or ans
            if ans:
                break

        return ans, qjt_pivot_list

    def on_gz(self):
        """共振处理：只关联上一个级别"""
        # 暂时 只处理买点B1
        chan = self.prev
        if not chan:
            return
        last_bs = None
        if len(chan.buy_list) > 0:
            last_bs = chan.buy_list[-1]
        # B1不成立
        if self.gz_delay_k_num >= self.gz_delay_k_max or (len(self.gz_tmp_bs) > 4 and self.gz_tmp_bs[0][5] == 0) or not \
                self.gz_tmp_bs[0]:
            self.gz_delay_k_num = 0
            self.gz_prev_last_bs = None
            self.gz_tmp_bs[0] = []
            self.gz_tmp_bs = None
        else:
            if last_bs and last_bs != self.gz_prev_last_bs and (
                    last_bs[1] == 'B2' or last_bs[2] == 'B3' or last_bs[2] == 'B1'):
                log.info(self.freq, self.symbol, 'gz:' + str(self.gz_delay_k_num) + ':')
                log.info(self.freq, self.symbol, last_bs)
                log.info(self.freq, self.symbol, self.gz_prev_last_bs)
                log.info(self.freq, self.symbol, self.gz_tmp_bs[0])
                if self.gz_tmp_bs[0]:
                    self.gz_tmp_bs[0][3] = self.k_list[-1].datetime
                    self.gz_tmp_bs[0][5] = 1
                    self.on_buy_sell(self.gz_tmp_bs[0])
                self.gz_delay_k_num = 0
                self.gz_prev_last_bs = None
                self.gz_tmp_bs = None

    def get_prev_last_bs(self):
        chan = self.prev
        if not chan or len(chan.buy_list) < 1:
            return None
        return chan.buy_list[-1]

    def on_trend(self, new_pivot, data):
        # 走势列表[[日期1，日期2，走势类型，[背驰点], [中枢]]]
        if not self.trend_list:
            type = 'pzup'
            if new_pivot[4] == 'down':
                type = 'pzdown'
            self.trend_list.append([new_pivot[0], new_pivot[1], type, [], [len(self.pivot_list) - 1]])
        else:
            last_trend = self.trend_list[-1]
            if last_trend[2] == 'up':
                if new_pivot[4] == 'up':
                    last_trend[1] = new_pivot[1]
                    last_trend[4].append(len(self.pivot_list) - 1)
                else:
                    self.trend_list.append([new_pivot[0], new_pivot[1], 'pzdown', [], [len(self.pivot_list) - 1]])
            if last_trend[2] == 'down':
                if new_pivot[4] == 'down':
                    last_trend[1] = new_pivot[1]
                    last_trend[4].append(len(self.pivot_list) - 1)
                else:
                    self.trend_list.append([new_pivot[0], new_pivot[1], 'pzup', [], [len(self.pivot_list) - 1]])
            if last_trend[2] == 'pzup':
                if new_pivot[4] == 'up':
                    last_trend[1] = new_pivot[1]
                    last_trend[4].append(len(self.pivot_list) - 1)
                    last_trend[2] = 'up'
                else:
                    self.trend_list.append([new_pivot[0], new_pivot[1], 'pzdown', [], [len(self.pivot_list) - 1]])
            if last_trend[2] == 'pzdown':
                if new_pivot[4] == 'down':
                    last_trend[1] = new_pivot[1]
                    last_trend[4].append(len(self.pivot_list) - 1)
                    last_trend[2] = 'down'
                else:
                    self.trend_list.append([new_pivot[0], new_pivot[1], 'pzup', [], [len(self.pivot_list) - 1]])

    def on_buy_sell(self, data, valid=True):
        if not data:
            return
        # 买点列表[[日期，值，类型, evaluation_time, 买点位置=index of stroke/line, valid, invalid_time, 类型, 强弱, qjt_pivot_list]]
        # 卖点列表[[日期，值，类型, evaluation_time, 买点位置=index of stroke/line, valid, invalid_time, 类型, 强弱, qjt_pivot_list]]
        if valid:
            if data[2].startswith('B'):
                log.info(self.freq, self.symbol, 'buy:')
                log.info(self.freq, self.symbol, data)
                self.buy_list.append(data)
                if self.buy:
                    self.buy(self.symbol, self.k_list[-1].close_price, 100, self.freq)
            else:
                log.info(self.freq, self.symbol, 'sell:')
                log.info(self.freq, self.symbol, data)
                self.sell_list.append(data)
                if self.sell:
                    self.sell(self.symbol, self.k_list[-1].close_price, 100, self.freq)
        else:
            pass


class BarGenerator:
    """
    Target:
    1. generating 1 minute bar data from tick data
    2. generateing x minute bar/x hour bar data from 1 minute data

    Notice:
    1. for x minute bar, x must be able to divide 60: 2, 3, 5, 6, 10, 15, 20, 30
    2. for x hour bar, x can be any number
    """

    def __init__(
            self,
            on_bar: Callable,
            window: int = 0,
            on_window_bar: Callable = None,
            interval: Interval = Interval.MINUTE,
            target: Interval = Interval.MINUTE
    ):
        self.bar: BarData = None
        self.on_bar: Callable = on_bar

        self.interval: Interval = interval
        self.interval_count: int = 0

        self.window: int = window
        self.window_bar: BarData = None
        self.on_window_bar: Callable = on_window_bar

        self.last_tick = None
        self.last_bar: BarData = None

        self.target = target

    def update_bar(self, bar: BarData) -> None:
        """
        Update 1 minute bar into generator
        """
        # If not inited, create window bar object
        if not self.window_bar:
            # Generate timestamp for bar data
            if self.interval == Interval.MINUTE:
                dt = bar.datetime.replace(second=0, microsecond=0)
            else:
                dt = bar.datetime.replace(minute=0, second=0, microsecond=0)

            self.window_bar = BarData(
                symbol=bar.symbol,
                exchange=bar.exchange,
                datetime=dt,
                open_price=bar.open_price,
                high_price=bar.high_price,
                low_price=bar.low_price
            )
        # Otherwise, update high/low price into window bar
        else:
            dt = bar.datetime.replace(second=0, microsecond=0)
            if not self.interval == Interval.MINUTE:
                dt = bar.datetime.replace(minute=0, second=0, microsecond=0)
            self.window_bar.datetime = dt
            self.window_bar.high_price = max(
                self.window_bar.high_price, bar.high_price)
            self.window_bar.low_price = min(
                self.window_bar.low_price, bar.low_price)

        # Update close price/volume into window bar
        self.window_bar.close_price = bar.close_price
        self.window_bar.volume += int(bar.volume)
        self.window_bar.open_interest = bar.open_interest
        self.window_bar.interval = self.target
        # Check if window bar completed
        finished = False

        if self.interval == Interval.MINUTE:
            # x-minute bar
            self.interval_count += 1

            if not self.interval_count % self.window:
                finished = True
                self.interval_count = 0
        elif self.interval == Interval.HOUR:
            if self.last_bar and bar.datetime.hour != self.last_bar.datetime.hour:
                # 1-hour bar
                if self.window == 1:
                    finished = True
                # x-hour bar
                else:
                    self.interval_count += 1

                    if not self.interval_count % self.window:
                        finished = True
                        self.interval_count = 0

        if finished:
            self.on_window_bar(self.window_bar)
            self.window_bar = None

        # Cache last bar object
        self.last_bar = bar

    def generate(self) -> Optional[BarData]:
        """
        Generate the bar data and call callback immediately.
        """
        bar = self.bar

        if self.bar:
            bar.datetime = bar.datetime.replace(second=0, microsecond=0)
            self.on_bar(bar)

        self.bar = None
        return bar


class Chan_Strategy():
    """首页展示行情"""

    method = METHOD.BZ
    symbol = ''
    include = True
    build_pivot = False
    qjt = False
    gz = False
    jb = Interval.MINUTE

    parameters = ['method', 'symbol', 'include', 'build_pivot', 'qjt', 'gz', 'jb']
    buy1 = 100
    buy2 = 200
    buy3 = 200
    sell1 = 100
    sell2 = 200
    sell3 = 200
    variables = ['buy1', 'buy2', 'buy3', 'sell1', 'sell2', 'sell3']

    # parameters = ["period", "stroke_type", "pivot_type", "buy1", "buy2", "buy3", "sell1", "sell2", "sell3",
    #               "dynamic_reduce"]
    # variables = ["stroke_list", "line_list", "pivot_list", "trend_list", "buy_list", "sell_list"]

    def __init__(self, vt_symbol, setting, buy, sell):
        """
        从1分钟->5->30->1d
        先做一个级别，之后再做其他的级别
        """
        if setting:
            if 'method' in setting.keys():
                self.method = setting['method']
            if 'symbol' in setting.keys():
                self.symbol = setting['symbol']
            # 笔生成方法，new, old
            # 是否进行K线包含处理
            if 'include' in setting.keys():
                self.include = setting['include']
            # 中枢生成方法，stroke, line
            # 使用笔还是线段作为中枢的构成, true使用线段
            if 'build_pivot' in setting.keys():
                self.build_pivot = setting['build_pivot']
            if 'qjt' in setting.keys():
                self.qjt = setting['qjt']
            if 'gz' in setting.keys():
                self.gz = setting['gz']
            # 买卖的级别
            if 'jb' in setting.keys():
                self.jb = setting['jb']
            # 线段生成方法
            # if 'include_feature' in setting.keys():
            #     self.include_feature = setting['include_feature']

        self.vt_symbol = vt_symbol
        self.include_feature = False

        self.buy = buy
        self.sell = sell
        # map
        self.chan_freq_map = {}
        self.bg_freq_map = {}

        # 初始化缠论类和bg
        self.bg = BarGenerator(on_bar=self.on_bar, interval=Interval.MINUTE)
        i = 0
        prev = None

        for freq in FREQS:
            chan = Chan_Class(freq=freq, symbol=self.vt_symbol, sell=self.sell, buy=self.buy, include=self.include,
                              include_feature=self.include_feature, build_pivot=self.build_pivot, qjt=self.qjt,
                              gz=self.gz)
            self.chan_freq_map[freq] = chan
            if prev:
                prev.set_next(chan)
                chan.set_prev(prev)
            prev = chan
            # 限定共振作用级别
            if chan.prev == None or chan.freq != FREQS[-1]:
                chan.gz = False
            if i > 0:
                wlist = FREQS_WINDOW[FREQS[i - 1]]
                self.bg_freq_map[freq] = BarGenerator(on_bar=self.on_pass, on_window_bar=self.on_bar, window=wlist[0],
                                                      interval=wlist[1], target=wlist[2])
            i += 1

    def on_bar(self, bar: BarData):
        freq = INTERVAL_FREQ[bar.interval.value]
        if bar.interval.value == Interval.MINUTE.value:
            for freq in self.bg_freq_map:
                self.bg_freq_map[freq].update_bar(bar)
        self.chan_freq_map[freq].on_bar(bar)

    def on_pass(self):
        pass

    # def buy(self, price: float, volume: float, freq: str = '', stop: bool = False, lock: bool = False):
    #     # todo 修改下单方式
    #
    #
    # def sell(self, price: float, volume: float, freq: str = '', stop: bool = False, lock: bool = False):
    #     # todo 修改下单方式


# ===============================主入口======================================
# 初始化函数，设定基准等等
chan_strategy_dict = dict()


def initialize(context):
    # 强势回落选股变量
    g.industry_compare_days = 66
    g.stock_compare_days = 13
    g.select_industry_amount = 6
    g.select_stock_amount = 10
    g.fall_back_days = 5
    g.daily_buy_count = 5

    # 买卖变量
    g.total_hold_amount = 8

    # 缠论设置
    g.chan_setting = {
        'include': True,
        'interval': Interval.MINUTE,
        'include_feature': False,
        'qjt': True,
        'gz': True,
        'build_pivot': False,
        'time_interval': 10
    }

    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 输出内容到日志 log.info()
    log.info('初始函数开始运行且全局只运行一次')
    # 过滤掉order系列API产生的比error级别低的log
    # log.set_level('order', 'error')

    ### 股票相关设定 ###
    # 股票类每笔交易时的手续费是：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易佣金最低扣5块钱
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5),
                   type='stock')

    ## 运行函数（reference_security为运行时间的参考标的；传入的标的只做种类区分，因此传入'000300.XSHG'或'510300.XSHG'是一样的）
    # 开盘前运行
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG')
    # 开盘时运行
    run_daily(market_open, time='every_bar', reference_security='000300.XSHG')
    # 收盘后运行
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')


## 开盘前运行函数
def before_market_open(context):
    # 输出运行时间
    log.info('函数运行时间(before_market_open)：' + str(context.current_dt.time()))

    # 选取强势近期回落股票
    select_end_date = (context.current_dt.date() + relativedelta(days=-1)).strftime("%Y-%m-%d")
    strength_codes = StrengthStock(select_end_date).select_strength_stocks()

    # strength_codes = ['000966.XSHE', '600008.XSHG']

    # 缠论操作
    def buy(symbol, price: float, volume: float, freq: str = '', stop: bool = False, lock: bool = False):
        # FREQS = ['日线', '30分钟', '5分钟', '1分钟']
        if freq == '1分钟' and check_run_time(context):
            current_positions = context.portfolio.positions.values()
            if len(current_positions) < g.total_hold_amount:
                current_hold_securities = [x.security for x in current_positions]
                if symbol not in current_hold_securities:
                    cash = context.portfolio.available_cash / (g.total_hold_amount - len(current_positions))
                    order_value(symbol, cash)

    def sell(symbol, price: float, volume: float, freq: str = '', stop: bool = False, lock: bool = False):
        if freq == '1分钟' and check_run_time(context):
            if symbol in [x.security for x in context.portfolio.positions.values()]:
                order_target(symbol, 0)
                del chan_strategy_dict[symbol]

    # 只保留N支观察的股票，超过的删除过旧的
    if len(chan_strategy_dict) > 15:
        current_hold_securities = [x.security for x in context.portfolio.positions.values()]
        for stock, stock_chan in list(chan_strategy_dict.items()):
            if stock in strength_codes or stock in current_hold_securities:
                continue
            if (context.current_dt.date() - stock_chan['select_time']).days > 4:
                del chan_strategy_dict[stock]

    # 对选中的股，获取最近15天(60 * 4 * 15)的缠论分析
    for stock in strength_codes:
        df = get_bars(stock, 3600, unit='1m', fields=('date', 'open', 'high', 'low', 'close'),
                      include_now=False, end_dt=f'{select_end_date} 9:00:00')

        if df is not None:
            strategy = Chan_Strategy(stock, g.chan_setting, buy, sell)
            for row in df:
                bar = BarData(symbol=stock, exchange=stock, interval=g.chan_setting['interval'],
                              datetime=row[0], open_price=row[1], high_price=row[2],
                              low_price=row[3], close_price=row[4], volume=1, open_interest=1)
                strategy.on_bar(bar)
            stock_chan = dict()
            stock_chan['select_time'] = context.current_dt.date()
            stock_chan['strategy'] = strategy

            chan_strategy_dict[stock] = stock_chan


## 开盘时运行函数
def market_open(context):
    log.info('函数运行时间(market_open):' + str(context.current_dt.time()))
    for stock, stock_chan in list(chan_strategy_dict.items()):
        # 获取股票的收盘价
        df = get_bars(stock, count=1, unit='1m', fields=['date', 'open', 'high', 'low', 'close'])
        if df is not None:
            for row in df:
                print(row)
                bar = BarData(symbol=stock, exchange=stock, interval=g.chan_setting['interval'],
                              datetime=row[0], open_price=row[1], high_price=row[2], low_price=row[3],
                              close_price=row[4], volume=1, open_interest=1)

                stock_chan['strategy'].on_bar(bar)


## 收盘后运行函数
def after_market_close(context):
    log.info(str('函数运行时间(after_market_close):' + str(context.current_dt.time())))
    # 得到当天所有成交记录
    trades = get_trades()
    for _trade in trades.values():
        log.info('成交记录：' + str(_trade))
    log.info('一天结束')
    log.info('##############################################################')
    log.info('当前持仓：')
    log.info(str(context.portfolio.positions))
    log.info('##############################################################')


def check_run_time(context) -> bool:
    """ 当前时间是否是开盘时间 """
    dtime = datetime
    now = context.current_dt
    now_str = str(now.date())
    start_sw = dtime.strptime(now_str + " 9:30", '%Y-%m-%d %H:%M')
    end_sw = dtime.strptime(now_str + " 11:32", '%Y-%m-%d %H:%M')
    start_xw = dtime.strptime(now_str + " 13:00", '%Y-%m-%d %H:%M')
    end_xw = dtime.strptime(now_str + " 15:02", '%Y-%m-%d %H:%M')
    if (start_sw <= now <= end_sw) or (start_xw <= now <= end_xw):
        return True
    else:
        return False

