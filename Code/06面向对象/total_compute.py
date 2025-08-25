#计算每月销售额并作图
import file_define
from pyecharts.charts import Bar
from pyecharts.options import *
from pyecharts.globals import ThemeType

class Compute:
  def __init__(self,records):
    self.records = records
    self.sale = {}
  
  #计算每日销售额
  def __CalulateSales(self) -> dict:
    for record in  self.records:
      if record.date in self.sale:
        self.sale[record.date] += record.money
      else:
        self.sale[record.date] = record.money
    #按日期排序
    self.sale = dict(sorted(self.sale.items(),key=lambda x: x[0]))
    return self.sale
  
  def make_picture(self):
    d = self.__CalulateSales()
    bar = Bar()

    bar.add_xaxis(list(d.keys()))
    bar.add_yaxis("销售额",list(d.values()),label_opts=LabelOpts(is_show=False))

    bar.set_global_opts(
      title_opts=TitleOpts(title="每日销售额")
    )

    bar.render("每日销售额.html")


