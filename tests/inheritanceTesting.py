class ElementClass:
    def __init__(self, num=0):
        self._num = num

    def setNum(self, num):
        self._num = num

    def getNum(self):
        return self._num

class ListClass:
    def __init__(self):
        self._list = []

    def addElement(self, element):
        self._list.append(element)

    def getElement(self, num):
        for element in self._list:
            if element.getNum() == num:
                return element
        return None

    def debugString(self):
        ret_str = ">>\n"

        i = 0
        for element in self._list:
            ret_str += str(i) + ": " + str(element.getNum()) + "\n"
            i += 1
        ret_str += ">>\n"

        return ret_str


if __name__ == "__main__":
    lc = ListClass()

    e1 = ElementClass(1)
    e2 = ElementClass(2)

    lc.addElement(e1)
    lc.addElement(e2)

    print(lc.debugString())

    lc.getElement(1).setNum(9)

    print(lc.debugString())
