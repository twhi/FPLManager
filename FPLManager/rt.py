a = [3, 3, 3, 4]
b = [1, 0, 1, 1]

ss = sum([1 for i in range(len(a)) if a[i] == 3 and b[i] == 1])
tt = sum([1 for i in range(len(a)) if a[i] == 4 and b[i] == 1])
print(ss, tt)