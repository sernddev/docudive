import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import base64
import plotly.io as pio

from danswer.configs.app_configs import IMAGE_SERVER_PROTOCOL
from danswer.configs.app_configs import IMAGE_SERVER_HOST
from danswer.configs.app_configs import IMAGE_SERVER_PORT

from danswer.utils.logger import setup_logger
import uuid
import kaleido
import os

# Setup logger
logger = setup_logger()


class PlotFactory:
    """ Factory class to generate different types of plots. """

    @staticmethod
    def create_chart(chart_type, df, column_names):
        try:
            """ Factory method to create charts based on the type. """
            charts = {
                "PIE": lambda: px.pie(df, names=column_names['x'], values=column_names['y'], title='Pie Chart'),
                "BAR": lambda: px.bar(df, x=column_names['x'], y=column_names['y'], title='Bar Chart'),
                "SCATTER": lambda: px.scatter(df, x=column_names['x'], y=column_names['y'], color=column_names['color'],
                                              title='Scatter Chart'),
                "HEATMAP": lambda: go.Figure(data=[go.Heatmap(x=column_names['x'], y=column_names['y'], z=df)]),
                "SCATTER_MATRIX": lambda: px.scatter(df, x=column_names['x'], y=column_names['y'], color=column_names['color'],
                                                     size=column_names['size'], title='Scatter Chart')
            }
            figure = charts.get(chart_type, lambda: logger.error("Unsupported chart type"))()
            logger.info(f'figure: {figure} generated for {chart_type} and dataframe: {df.dtypes}')
            return figure
        except Exception as e:
            logger.error(f"Error creating chart: {e}")
            return None


def format_image_url(file_name, image_title="title image") -> str:
    image_url = "![" + image_title + "](" + IMAGE_SERVER_PROTOCOL + "://" + IMAGE_SERVER_HOST + ":" + IMAGE_SERVER_PORT + "/" + "images/" + file_name + ")"
    logger.info(f'Formatted image url: {image_url}')
    return image_url


class PlotCharts:
    """ Main class to handle plotting operations. """

    def __init__(self):
        logger.info('Initializing PlotCharts')

    def generate_chart_and_save(self, dataframe, field_names, chart_type) -> str:
        """ Generate specified chart and convert to markdown with base64 image. """
        figure = PlotFactory.create_chart(chart_type, dataframe, field_names)
        file_name = str(uuid.uuid4()) + '.jpg'
        image_path = os.path.join('/images', file_name)
        figure.write_image(image_path)
        logger.info(f'Plotly figure saved to {image_path}')
        return format_image_url(file_name=file_name)
        # base64_image = self.base64_from_fig(figure)
        # self.format_as_markdown_image(base64_image=base64_image, alt_text='plot') if figure else None

    @staticmethod
    def base64_from_fig(fig):
        """ Convert a Plotly figure to a base64 string. """
        try:
            image_bytes = pio.to_image(fig, format='png', engine='kaleido')
            return base64.b64encode(image_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to convert figure to base64: {e}")
            return None

    @staticmethod
    def format_as_markdown_image(base64_image, alt_text="plot"):
        """ Format a base64 image string as a Markdown image. """
        return f'![{alt_text}](data:image/png;base64,{base64_image})'

    def create_dataframe(self, json_data):
        df = pd.DataFrame(json_data)
        logger.info(f'DataFrame created with columns: {df.columns.tolist()}')
        logger.info(f'DataFrame : {df}')
        return df

    def find_chart_type(self, df) -> str:
        num_columns = len(df.columns)
        chart_type = {
            1: "PIE",
            2: "BAR",
            3: "SCATTER",
        }.get(num_columns, "SCATTER_MATRIX")  # Default case for more than 3 fields
        logger.info(f"Determined chart type: {chart_type} for columns count: {num_columns}")
        return chart_type


if __name__ == '__main__':
    data = {
        'Category': ['A', 'B', 'C'],
        'Values': [10, 20, 30]
    }
    df = pd.DataFrame(data)
    plot_charts = PlotCharts()
    markdown_image = plot_charts.generate_chart_and_save(df, ['Category', 'Values'], 'PIE')
    print(markdown_image)