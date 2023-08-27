# import matplotlib.pyplot as plt
import plotly.express as px
from PIL import Image
import io

async def generate_dynamic_plot():
    # Создание данных для графика (например, случайные значения)
    x = [i for i in range(100)]
    y = [i * 0.1 for i in range(100)]

    data = {'x':x,'y':y}
    fig = px.line(data, x='x', y='y', title='Простой график')

    # Преобразование графика в изображение
    image_bytes = fig.to_image(format="png")
    image=io.BytesIO(image_bytes)

    return image
    # # Создание графика
    # plt.figure(figsize=(6, 4))
    # plt.plot(x, y)
    # plt.xlabel('X-axis')
    # plt.ylabel('Y-axis')
    # plt.title('Dynamic Plot')
    # plt.grid()

    # # Сохранение графика как изображения в памяти
    # image_stream = io.BytesIO()
    # plt.savefig(image_stream, format='png')
    # plt.close()

    # return image_stream.getvalue()

