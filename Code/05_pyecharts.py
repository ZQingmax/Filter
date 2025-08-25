from pyecharts.charts import Line
import pyecharts.options as opts
line  = Line()

line.add_xaxis(["日本","美国","中国"])
line.add_yaxis("GDP",[10,20,30])


#全局配置
line.set_global_opts(
  title_opts=opts.TitleOpts("GDP展示"),
  legend_opts=opts.LegendOpts(is_show = True),
  visualmap_opts=opts.VisualMapOpts(is_show = True),
  toolbox_opts=opts.ToolboxOpts(is_show = True)
)
#通过render方法生成图像（HTML文件）
line.render_notebook()