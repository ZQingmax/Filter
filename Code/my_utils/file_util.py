def print_file_info(file_name):
  try:
    f = open("file_name","r",encoding="UTF-8")
    print(f"文件的全部内容是{f.read()}")
  except Exception as e:
    print(e)
    f = open("file_name","w",encoding="UTF-8")
  finally:
    f.close()

def append_to_file(file_name,data):
  try:
    f = open("file_name","a",encoding="UTF-8")
    f.write(data)
  except Exception as e:
    print(e)
  finally:
    f.close()