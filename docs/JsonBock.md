# Block Json Description
<link rel="stylesheet" href="assets/css/dark.css">

Каждая функция на Bock компилируется в `block.json` — файл, описывающий топологию блок-схемы: набор блоков и стрелок между ними.

---

## Структура файла

```json
{
  "blocks": [ /* массив блоков */ ],
  "arrows": [ /* массив стрелок */ ],
  "x0": 47,
  "y0": 251
}
```

`x0`, `y0` — начальные координаты холста (обычно фиксированы).

---

## Блок (объект в `blocks`)

```json
{
  "x": 100,
  "y": 200,
  "text": "текст внутри блока",
  "width": 160,
  "height": 60,
  "type": "Блок",
  "isMenuBlock": false,
  "fontSize": 14,
  "textHeight": 14,
  "isBold": false,
  "isItalic": false,
  "textAlign": "center",
  "labelsPosition": 1
}
```

### Поля блока

| Поле | Тип | Описание |
|---|---|---|
| `x` | число | Координата X левого верхнего угла блока |
| `y` | число | Координата Y левого верхнего угла блока |
| `text` | строка | Текст, отображаемый внутри блока |
| `width` | число | Ширина блока в пикселях |
| `height` | число | Высота блока в пикселях |
| `type` | строка | Тип блока (см. ниже) |
| `isMenuBlock` | bool | Всегда `false` для блок-схем |
| `fontSize` | число | Размер шрифта текста |
| `textHeight` | число | Высота строки текста |
| `isBold` | bool | Жирный шрифт |
| `isItalic` | bool | Курсив |
| `textAlign` | строка | Выравнивание текста: `"center"`, `"left"`, `"right"` |
| `labelsPosition` | число | Позиция меток на стрелках (обычно `1`) |

### Типы блоков (`type`)

| Значение | Описание | Bock-команда |
|---|---|---|
| `"Начало / конец"` | Блок начала или конца схемы | Автоматически |
| `"Блок"` | Обычный блок действия | Присвоение, выражение |
| `"Условие"` | Ромб условия | `if`, `while` |
| `"Ввод / вывод"` | Блок ввода или вывода | `input >>`, `output >>` |
| `"Цикл for"` | Блок цикла for (ГОСТ) | `for x in y` |

---

## Стрелка (объект в `arrows`)

```json
{
  "startIndex": 0,
  "endIndex": 1,
  "startConnectorIndex": 2,
  "endConnectorIndex": 0,
  "nodes": [
    { "x": 150, "y": 300 }
  ],
  "counts": [1]
}
```

### Поля стрелки

| Поле | Тип | Описание |
|---|---|---|
| `startIndex` | число | Индекс блока-источника в массиве `blocks` |
| `endIndex` | число | Индекс блока-назначения в массиве `blocks` |
| `startConnectorIndex` | 0–3 | Сторона выхода из блока-источника |
| `endConnectorIndex` | 0–3 | Сторона входа в блок-назначения |
| `nodes` | массив точек | Промежуточные точки маршрута стрелки |
| `counts` | массив чисел | Вспомогательные данные рендера (обычно `[1]`) |

### Индексы коннекторов

```
        0 (верх)
         ↑
3 (лево) ← [блок] → 1 (право)
         ↓
        2 (низ)
```

| Значение | Сторона |
|---|---|
| `0` | Верх |
| `1` | Право |
| `2` | Низ |
| `3` | Лево |

---

## Пример: Hello World

```json
{
  "blocks": [
    {
      "x": 100, "y": 50, "text": "Начало",
      "width": 120, "height": 60, "type": "Начало / конец",
      "isMenuBlock": false, "fontSize": 14, "textHeight": 14,
      "isBold": false, "isItalic": false,
      "textAlign": "center", "labelsPosition": 1
    },
    {
      "x": 100, "y": 160, "text": "Hewoo world",
      "width": 120, "height": 60, "type": "Ввод / вывод",
      "isMenuBlock": false, "fontSize": 14, "textHeight": 14,
      "isBold": false, "isItalic": false,
      "textAlign": "center", "labelsPosition": 1
    },
    {
      "x": 100, "y": 270, "text": "Конец",
      "width": 120, "height": 60, "type": "Начало / конец",
      "isMenuBlock": false, "fontSize": 14, "textHeight": 14,
      "isBold": false, "isItalic": false,
      "textAlign": "center", "labelsPosition": 1
    }
  ],
  "arrows": [
    {
      "startIndex": 0, "endIndex": 1,
      "startConnectorIndex": 2, "endConnectorIndex": 0,
      "nodes": [], "counts": [1]
    },
    {
      "startIndex": 1, "endIndex": 2,
      "startConnectorIndex": 2, "endConnectorIndex": 0,
      "nodes": [], "counts": [1]
    }
  ],
  "x0": 47,
  "y0": 251
}
```

---

> Как Fragmos рендерит этот JSON: [[Fragmos - рендер для bock]]  
> Визуальный вид всех типов блоков: [[Блоки и их отрендеренные версии]]
