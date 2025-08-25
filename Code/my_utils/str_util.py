def str_reverse(s):
  return "".join(reversed(s))


def substr(s,star,end):
  return s[star:end]


if __name__ == "__main__":
  s = "abcdef"
  print(str_reverse(s))