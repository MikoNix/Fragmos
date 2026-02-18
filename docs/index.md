<link rel="stylesheet" href="assets/css/dark.css">

[Домой](index.md) 
## Структура документации

| Раздел                              | Описание                                         |
| ----------------------------------- | ------------------------------------------------ |
| [Введение в bock](Firstbork.md) | Базовый синтаксис, переменные, ввод/вывод        |
| [Синтаксис Bock](Syntax.md)         | Полный справочник по синтаксису                  |
| [Block Json Description](JsonBock.md) | Формат `block.json` — описание всех полей        |
| [fragmos](AboutFragmos.md)           | Как Fragmos интерпретирует Bock и рендерит схему |

---

## Быстрый старт

Минимальная программа на Bock:

```bock
function main {
    output >> "Hello, world!";
}
```

Программа с вводом и условием:

```bock
function check_input {
    input >> "x";
    if (x > 0) {
        output >> "positive";
    };
    else {
        output >> "not positive";
    };
}
```

---

