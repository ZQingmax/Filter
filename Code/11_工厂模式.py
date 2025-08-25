class Person:
  pass

class Student(Person):
  pass
class Teacher(Person):
  pass
class Worker(Person):
  pass

class Factory:
  def get_person(self,p_type):
    if p_type == 's':
      return Student()
    elif p_type == 't':
      return Teacher()
    else:
      return Worker()
    
factory = Factory()
student = factory.get_person('s')
teacher = factory.get_person('t')
worker = factory.get_person('w')

print(student)
print(teacher)
print(worker)