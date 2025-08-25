"""
文件读取
"""
from file_define import Record
import json

class FileReader:
  def read_data(self)-> list[Record]:
    pass

class TextFileReader(FileReader):
  def __init__(self,path):
    self.path = path
  
  def read_data(self) -> list[Record]:
    f = open(self.path,"r",encoding="UTF-8")
    res = []
    for line in f.readlines():
      line = line.strip()
      line_data = line.split(',')
      record = Record(line_data[0],line_data[1],int(line_data[2]),line_data[3])
      res.append(record)

    f.close()
    return res

class JsonFileReader(FileReader):
  def __init__(self,path):
    self.path = path
  
  def read_data(self) -> list[Record]:
    f = open(self.path,"r",encoding="UTF-8")
    res = []
    for line in f.readlines():
      line = line.strip()
      d = json.loads(line)
      
      record = Record(d["date"],d["order_id"],d["money"],d["province"])
      res.append(record)

    f.close()
    return res

