import drawpyo
import os

os.remove("/workspaces/Fragmos/webapp/pages/fragmos/Xuita.xml")
#========================================================================
#Описание классов для блоков диаграммы
#========================================================================

# Блок начало / конец
class Base(drawpyo.diagram.Object):  
    def __init__(self, page,  value, x, y):
        super().__init__(page=page)
        self.value = value
        self.width = 120
        self.height = 40
        self.position = (x, y)
        self.apply_style_string("whiteSpace=wrap;rounded=1;dashed=0; whiteSpace=wrap; html=1; arcSize=50;arcSize=50;")

# Блок выполнения
class Execute(drawpyo.diagram.Object):
    def __init__(self, page,  value, x, y):
        super().__init__(page=page)
        self.value = value
        self.width = 120 * (( len(value) // 50 ) + 1)
        self.height = 40 * (( len(value) // 50 ) + 1)
        self.position = (x, y)
        self.apply_style_string("rounded=0;whiteSpace=wrap;html=1;")

class IF(drawpyo.diagram.Object):
    def __init__(self, page,  value, x, y):
        super().__init__(page=page)
        self.value = value
        self.width = 120 * (( len(value) // 50 ) + 1)
        self.height = 50 * (( len(value) // 50 ) + 1)
        self.position = (x, y)
        self.apply_style_string("whiteSpace=wrap;html=1;shape=rhombus;")

# Отрисовка стрелок
class Pointer(drawpyo.diagram.Object):
    pass

# TODO : класс форматирования текста 




test = drawpyo.File()

test.file_path = "/workspaces/Fragmos/webapp/pages/fragmos"
test.file_name = "Xuita.xml"

page = drawpyo.Page(file=test)

text = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n aaaaaaaaaaaaaaaaaaaaaaaa"

base_obj  = Execute(page, value=text, x=100, y=100)
base_obj1 = Base(page, value="123", x=100, y=200)
base_obj2 = IF(page, value="if (sum + files[i] <= s)", x=100, y=300)
test.write()

