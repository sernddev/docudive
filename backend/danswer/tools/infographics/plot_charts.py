import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import base64
import plotly.io as pio
from danswer.configs.app_configs import STATIC_DIRECTORY
from danswer.utils.logger import setup_logger
import uuid
import os

logger = setup_logger()
IMAGE_EXTENSION = '.jpg'
IMAGE_DIRECTORY = os.path.join(STATIC_DIRECTORY, 'images')

def format_image_url(file_name, image_title="title image") -> str:
    image_url = f"![{image_title}]({STATIC_DIRECTORY}/images/{file_name})"
    logger.info(f'Formatted image url: {image_url}')
    return image_url


def generate_chart_and_save(dataframe, field_names, chart_type) -> str:
    """ Generate specified chart and convert to markdown with base64 image. """

    try:
        # Create the image directory if it doesn't exist
        os.makedirs(IMAGE_DIRECTORY, exist_ok=True)
        logger.info(f'Image directory verified at: {IMAGE_DIRECTORY}')

        # Generate the Plotly figure
        figure = PlotFactory.create_chart(chart_type, dataframe, field_names)
        if figure is not None:
            # Generate a unique filename
            file_name = f"{uuid.uuid4()}{IMAGE_EXTENSION}"
            image_path = os.path.join(IMAGE_DIRECTORY, file_name)
            
            # Save the figure as an image
            figure.write_image(image_path)
            logger.info(f'Plotly figure saved to {image_path}')
            
            # Return the formatted image URL (implement this function as needed)
            return format_image_url(file_name=file_name)
        else:
            logger.warning('Plotly figure was None. No image saved.')

    except Exception as e:
        logger.error(f'Failed to generate chart: {e}')
    return 'No chart generated'


def find_chart_type(df) -> str:
    num_columns = len(df.columns)
    chart_type = {
        1: "PIE",
        2: "BAR",
        3: "SCATTER",
    }.get(num_columns, "SCATTER_MATRIX")  # Default case for more than 3 fields
    logger.info(f"Determined chart type: {chart_type} for columns count: {num_columns}")
    return chart_type


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
                "SCATTER_MATRIX": lambda: px.scatter(df, x=column_names['x'], y=column_names['y'],
                                                     color=column_names['color'],
                                                     size=column_names['size'], title='Scatter Chart')
            }
            figure = charts.get(chart_type, lambda: logger.error("Unsupported chart type"))()
            logger.info(f'figure: {figure} generated for {chart_type} and dataframe: {df.dtypes}')
            return figure
        except Exception as e:
            logger.error(f"Error creating chart: {e}")
            return None


class PlotCharts:
    """ Main class to handle plotting operations. """

    def __init__(self):
        logger.info('Initializing PlotCharts')

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


if __name__ == '__main__':
    data = {
        'Category': ['A', 'B', 'C'],
        'Values': [10, 20, 30]
    }
    df = pd.DataFrame(data)
    plot_charts = PlotCharts()
    markdown_image = generate_chart_and_save(df, ['Category', 'Values'], 'PIE')
    print(markdown_image)
