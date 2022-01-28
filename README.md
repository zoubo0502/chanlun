# 缠论图形工具项目

## 安装依赖包

**系统使用win10或者win11**

**python环境最好使用Anaconda或者python3.7**

**python一定要使用3.7版本, 并且安装路径不能包含有中文**

安装程序依赖

````shell
install.bat
````

## 运行项目

````shell
run.bat
````

## 使用说明

1. 通过菜单: 功能->股票缠图，在对话框中选择参数，默认参数仅供参考，参数意义：
聚宽账号：聚宽账号
聚宽密码：聚宽密码
股票代码：股票代码
开始日期：填写开始日期，以'-'分割
K线类型： 缠论K线（经过包含处理）、普通K线（未经过包含处理）
中枢类型：笔、线段
用区间套：区间套对于二三类买卖点可选，第一类买卖点一定使用
使用共振：共振只针对1分钟级别和5分钟的B1、B2、B3
展现间隔：如果填写数字>0，则没隔多少根分钟K线渲染缠图

2. 聚宽账号需要申请试用API

## 缠论规则

1. 区间套对于二三类买卖点可选，第一类买卖点一定使用
2. 共振只针对1分钟级别和5分钟的B1、B2、B3

### 缠论实现 处理原则：
1、三买的类型：强和弱，高于前中枢的GG为强，否则为弱。

2、二买的类型：超强、强、中和弱，二买大于前中枢的ZG，反转笔突破前中枢的ZG为强，反转笔突破前中枢的ZD为中，否则为弱。

3、买卖点的类型分为：趋势类和盘整类。

4、B2失效的判断标准：以B2为起点的笔的顶不大于反转笔的顶。

5、S1有效的判断标准：必须有同级别向下的走势（盘整下或趋势下）完成。

6、出现第一类买卖点时的中枢处理：如果出现了一买，此时趋势由向下转为向上，以B1为起点的反转笔作为下一个中枢的进入笔；如果出现了一卖，此时趋势由向上转为向下，以S1为起点的反转笔作为下一个中枢的进入笔。

7、出现S1后，回撤不碰前中枢也不判断为B3，判断B3的前提是向上离开中枢的笔的顶点不是S1。

8、出现B1后，向上不碰前中枢也不判断为S3，判断S3的前提是向下离开中枢的笔的底点不是B1。
