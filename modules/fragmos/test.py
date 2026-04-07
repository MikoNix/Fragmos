import os
import sys

# Добавляем папку fragmos в путь чтобы работали локальные импорты
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from builder import generate_from_code

CODE = """
using System;

class Program
{
    static void BubbleSort(int[] arr)
    {
        int n = arr.Length;
        bool swapped;
        
        for (int i = 0; i < n - 1; i++)
        {
            swapped = false;
            // n - i - 1, так как последние i элементов уже на своих местах
            for (int j = 0; j < n - i - 1; j++)
            {
                if (arr[j] > arr[j + 1])
                {
                    // Обмен элементов
                    int temp = arr[j];
                    arr[j] = arr[j + 1];
                    arr[j + 1] = temp;
                    swapped = true;
                }
            }

            // Если за проход не было ни одного обмена, массив готов
            if (!swapped) break;
        }
    }

    static void Main()
    {
        int[] data = { 64, 34, 25, 12, 22, 11, 90 };
        
        BubbleSort(data);
        
        Console.WriteLine("Отсортированный массив:");
        Console.WriteLine(string.Join(" ", data));
    }
}


"""

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_output.xml")

result_path = generate_from_code(
    code=CODE,
    language="C#",
    out_path=out,
    mode_id="default",
)

print(f"XML сохранён: {result_path}")
