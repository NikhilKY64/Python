n=input("Write your name: ")
e=int(input("English Marks: "))
h=int(input("Hindi Marks: "))
m=int(input("Maths Marks: "))
s=int(input("Science Marks: "))
c=int(input("Computer science Marks: "))

p=(e+h+m+s+c)/5

print("Your percentage is: ",p)

if p>33:
    print(n + ",You are Pass!")
else:
    print(n + ",You are fail!")
