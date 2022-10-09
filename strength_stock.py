from jqdata import *
from dateutil.relativedelta import relativedelta
import pandas as pd
import jqdata
import datetime
import json

class StrengthStock:
    """ 获取最近几天回落的强势股票 """

    def __init__(self, select_end_date, industry_compare_days=66, stock_compare_days=13,
                 select_industry_amount=6, select_stock_amount=10, fall_back_days=5,
                 prefer_industry_order=3, prefer_stock_order=5, prefer_stock_amount=15):
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
                stock_score = self.get_score(stock_range, compare_industry_range, self.stock_compare_days) + self.get_score(
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
                datetime.datetime.strptime(select_end_date, '%Y-%m-%d').date() + relativedelta(months=-6)):
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