import drawpyo
import os

if os.path.exists("/workspaces/Fragmos/webapp/pages/fragmos/Xuita.xml"):
    os.remove("/workspaces/Fragmos/webapp/pages/fragmos/Xuita.xml")
#========================================================================
#Описание классов для блоков диаграммы
#========================================================================

# Блок начало / конец
class Base(drawpyo.diagram.Object):  
    def __init__(self, page, value, x, y):
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

# Блок условия
class If(drawpyo.diagram.Object):
    def __init__(self, page,  value, x, y):
        super().__init__(page=page)
        self.value = value
        self.width = 200 * (( len(value) // 50 ) + 1)
        self.height = 80 * (( len(value) // 50 ) + 1)
        self.position = (x, y)
        self.apply_style_string("whiteSpace=wrap;html=1;shape=rhombus;")

class While(drawpyo.diagram.Object):
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
    def __init__(self, page, source, target,root=None):
        super().__init__(page=page,)
        self.source = source
        self.target = target
        self.root = root
        self.pointer_type()
    def pointer_type(self):
        if self.source.position[1] > self.target.position[1]:
            self.apply_style_string("endArrow=classic;html=1;rounded=0;waypoint=orthogonal;exitX=0.5;exitY=1;entryX=0;entryY=0.5;") 
        if self.source.position[1] < self.target.position[1]:
            self.apply_style_string("endArrow=none;html=1;rounded=0;waypoint=orthogonal;exitX=0.5;exitY=1;")
        if (type(self.source) == If and self.root == "yes"):
            self.apply_style_string("exitX=1;exitY=0.5;waypoint=orthogonal;")
        if (type(self.source) == If and self.root == "no"):
            self.apply_style_string("exitX=0;exitY=0.5;waypoint=orthogonal;")


        if (type(self.source) == While and self.root == "yes"):
            self.apply_style_string("exitX=0.5;exitY=1;waypoint=orthogonal;")

        if (type(self.source) == While and self.root == "no"):
            self.apply_style_string("exitX=1;exitY=0.5;waypoint=orthogonal;")
            
            
    

# TODO : класс форматирования текста 

class Text_format(drawpyo.diagram.Object):
    def __init__(self, page,  value, x, y,width=20,height=15):
        super().__init__(page=page)
        self.value = value
        self.width = width
        self.height = height
        self.position = (x, y)    
        self.apply_style_string("text;html=1;whiteSpace=wrap;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;rounded=0;")


test = drawpyo.File()

test.file_path = "/workspaces/Fragmos/webapp/pages/fragmos"
test.file_name = "Xuita.xml"

page = drawpyo.Page(file=test)

# obj_start = Base(page, "Начало", 140,20)

# obj_if1 = If(page, "Если пенис большой", 100, 100)
# obj1_if1_no = Proccess(page, "Выполнение", 10, 280)

# obj_if2_if1_yes = If(page, "Если пенис очень большой", 240, 240) 
# obj_if2_yes = Proccess(page, "Выполнение 3", 350, 360) 
# obj_if2_no = Proccess(page, "Выполнение 4", 140, 360) 

# obj_end = Base(page, "Конец", 140, 510)

# pointer = Pointer(page, obj_start, obj_if1)

# pointer1 = Pointer(page, obj_if1, obj1_if1_no, root="no")
# pointer2 = Pointer(page, obj_if1, obj_if2_if1_yes, root="yes")
# pointer3 = Pointer(page, obj_if2_if1_yes, obj_if2_yes, root="yes")
# pointer4 = Pointer(page, obj_if2_if1_yes, obj_if2_no, root="no")


# pointer5 = Pointer(page, obj1_if1_no, obj_end)
# pointer6 = Pointer(page, obj_if2_yes, obj_end)
# pointer7 = Pointer(page, obj_if2_no, obj_end)

obj_start = Base(page, "Начало", 450,20)
obj_end = Base(page, "Конец", 460, 410)

obj_while = While(page, "Пока пенис большой", 410, 110)
anker = Text_format(page, "", 507.7, 100,5,5)
obj1_while = Proccess(page, "Выполнение 1", 450, 220)
obj2_while = Proccess(page, "Выполнение 2", 450, 300)

pointer  = Pointer(page, obj_start, obj_while)
pointer1 = Pointer(page, obj_while, obj1_while, root="yes")
pointer2 = Pointer(page, obj1_while, obj2_while)
pointer3 = Pointer(page, obj2_while, anker)

pointer5 = Pointer(page, obj_while, obj_end, root="no")




test.write()

