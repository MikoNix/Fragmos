import drawpyo
import os

os.remove("/workspaces/Fragmos/webapp/pages/fragmos/Xuita.xml")
#========================================================================
#Описание классов для блоков диаграммы
#========================================================================

# Блок начало / конец
class Base(drawpyo.diagram.Object):  
    def __init__(self, page, value, x, y, type):
        super().__init__(page=page)
        self.value = value
        self.width = 120
        self.height = 40
        self.position = (x, y)
        self.type = type
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

# Блок условия
class IF(drawpyo.diagram.Object):
    def __init__(self, page,  value, x, y):
        super().__init__(page=page)
        self.value = value
        self.width = 200 * (( len(value) // 50 ) + 1)
        self.height = 80 * (( len(value) // 50 ) + 1)
        self.position = (x, y)
        self.apply_style_string("whiteSpace=wrap;html=1;shape=rhombus;")

# Блок цикла
class For_default(drawpyo.diagram.Object):
    def __init__(self, page,  value, x, y):
        super().__init__(page=page)
        self.value = value
        self.width = 120 * (( len(value) // 50 ) + 1)
        self.height = 40 * (( len(value) // 50 ) + 1)
        self.position = (x, y)
        self.apply_style_string("shape=hexagon;perimeter=hexagonPerimeter2;whiteSpace=wrap;html=1;fixedSize=1;")

# Блок цикла с ограничением(начало)
class Loop_limit_start(drawpyo.diagram.Object):
    def __init__(self, page,  value, x, y):
        super().__init__(page=page)
        self.value = value
        self.width = 120 * (( len(value) // 50 ) + 1)
        self.height = 40 * (( len(value) // 50 ) + 1)
        self.position = (x, y)
        self.apply_style_string("shape=loopLimit;whiteSpace=wrap;html=1;")
    
# Блок цикла с ограничением (конец)
class Loop_limit_end(drawpyo.diagram.Object):
    def __init__(self, page,  value, x, y):
        super().__init__(page=page)
        self.value = value
        self.width = 120 * (( len(value) // 50 ) + 1)
        self.height = 40 * (( len(value) // 50 ) + 1)
        self.position = (x, y)
        self.apply_style_string("shape=loopLimit;whiteSpace=wrap;html=1;direction=west;")

# Блок подпрограммы
class Proccess(drawpyo.diagram.Object):
    def __init__(self, page,  value, x, y):
        super().__init__(page=page)
        self.value = value
        self.width = 120 * (( len(value) // 50 ) + 1)
        self.height = 40 * (( len(value) // 50 ) + 1)
        self.position = (x, y)
        self.apply_style_string("shape=process;whiteSpace=wrap;html=1;backgroundOutline=1;")

# Отрисовка стрелок

class Pointer(drawpyo.diagram.Edge):
    def __init__(self, page, source, target):
        super().__init__(page=page,)
        self.source = source
        self.target = target
        self.pointer_type()
        
    def pointer_type(self):
        if self.source.position[1] > self.target.position[1]:
            self.apply_style_string("endArrow=classic;html=1;rounded=0;waypoint=orthogonal;") 
        if self.source.position[1] < self.target.position[1]:
            self.apply_style_string("endArrow=none;html=1;rounded=0;waypoint=orthogonal;")
    

# TODO : класс форматирования текста 

class Text_format(drawpyo.diagram.Object):
    def __init__(self, page,  value, x, y):
        super().__init__(page=page)
        self.value = value
        


test = drawpyo.File()

test.file_path = "/workspaces/Fragmos/webapp/pages/fragmos"
test.file_name = "Xuita.xml"

page = drawpyo.Page(file=test)


base_obj = Base(page, "Начало", 100, 100, "start")
base_obj2 = Base(page, "Конец", 100, 300, "end")
point = Pointer(page, base_obj, base_obj2)
base_obj3 = Base(page, "Начало 2", -250, 100, "start")
point2 = Pointer(page, base_obj2, base_obj3)

test.write()

