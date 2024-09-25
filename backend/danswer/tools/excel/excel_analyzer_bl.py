import pandas as pd
import numpy as np


class EvalResult:
    def __init__(self, hint, data=None, stats_info=None, info=None, error=None):
        self.hint = hint
        self.data = data
        self.stats_info = stats_info
        self.info = info
        self.error = error

    def is_successful(self):
        return self.error is None

    def has_min_max(self):
        return (
                self.stats_info is not None and
                'min' in self.stats_info and
                'max' in self.stats_info and
                self.stats_info['min'] is not None and
                self.stats_info['max'] is not None and
                self.stats_info['min'] > 0 and
                self.stats_info['max'] > 0
        )

    def is_data_empty(self):
        return self.data.empty if isinstance(self.data, pd.DataFrame) else len(self.data) == 0

    def __repr__(self):
        if self.is_successful():
            return f"EvalResult(hint={self.hint}, stats_info={self.stats_info}, info={self.info})"
        else:
            return f"EvalResult(hint={self.hint}, error={self.error})"


def eval_expres_simple_dynamic_df(dframe, hint, exp):
    # Use eval with locals() to inject dframe into the evaluated expression
    e = eval(exp, {"pd": pd}, {"df": dframe})  # Here we explicitly pass 'df' as 'dframe' to the eval
    print(f'{hint}, rows: {len(dframe)} : {e}')

def load_and_convert_numeric( df):
    if df is None or df.empty:
        print("DataFrame is None or empty.")
        return df

    # Regex pattern to identify and clean numeric-like values, including currency symbols and commas
    numeric_pattern = r'^\s*[\$₹€£]?\s*[\d,]+(\.\d+)?\s*$'

    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                # Apply regex filter only to rows that match the numeric pattern
                is_numeric_like = df[col].str.match(numeric_pattern)

                if is_numeric_like.sum() > 0.5 * len(df):
                    # Remove commas and currency symbols, then convert to float
                    df[col] = df[col].str.replace(r'[^\d.-]', '', regex=True).astype(float)
            except Exception as e:
                print(f"Error converting column {col} to numeric: {e}")

    return df

def load_and_convert_types(df):
    if df is None or df.empty:
        print("DataFrame is None or empty.")
        return df

    # Regex pattern to identify and clean numeric-like values, including currency symbols and commas
    numeric_pattern = r'^\s*[\$₹€£]?\s*[\d,]+(\.\d+)?\s*$'

    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                # Try converting the column to numeric first
                is_numeric_like = df[col].str.match(numeric_pattern)

                if is_numeric_like.sum() > 0.5 * len(df):
                    # Remove commas and currency symbols, then convert to float
                    df[col] = df[col].str.replace(r'[^\d.-]', '', regex=True).astype(float)
                else:
                    # Try converting the column to datetime if numeric conversion is not applicable
                    converted_col = pd.to_datetime(df[col], errors='coerce')

                    if converted_col.notna().sum() > 0.5 * len(df):
                        df[col] = converted_col  # Keep the datetime conversion
            except Exception as e:
                print(f"Error converting column {col}: {e}")

    return df


def eval_expres(dframe, hint, exp):
    print("====" * 20)
    try:
        e = eval(exp, {"pd": pd}, {"df": dframe})
        if isinstance(e, pd.Series) and e.dtype != 'object':  # If the result is a single column of numeric values
            min_val = e.min()
            max_val = e.max()
            mean_val = e.mean()
            median_val = e.median()
            std_dev = e.std()
            q1 = e.quantile(0.25)
            q3 = e.quantile(0.75)
            variance = e.var()
            skewness = e.skew()
            kurtosis = e.kurt()
            stats_info = {
                'min': min_val,
                'max': max_val,
                'mean': mean_val,
                'median': median_val,
                'std_dev': std_dev,
                'q1 (25%)': q1,
                'q3 (75%)': q3,
                'variance': variance,
                'skewness': skewness,
                'kurtosis': kurtosis
            }
            # Convert Series to DataFrame and append min and max
            df_e =  e.reset_index(name='value') #e.to_frame(name='value')
            # df_e['min'] = min_val
            # df_e['max'] = max_val

            print(f'{hint}, rows: {len(dframe)} ::stats: {stats_info} ==> {e}')
            print("====" * 20)
            return EvalResult(hint, data=df_e, stats_info=stats_info, info=f'Successfully executed {exp}')

        else:
            print(f'{hint}, rows: {len(dframe)} : {e}')
            print("====" * 20)
            return EvalResult(hint, data=e, info=f'Successfully executed {exp}')

    except Exception as ex:
        print(f"Error while executing: {hint} ==> {ex}")
        print("====" * 20)
        return EvalResult(hint, error=str(ex))



def eval_expres_advanced(dframe, hint, exp):
    print("====" * 20)
    e = eval(exp)
    if isinstance(e, pd.Series) and e.dtype != 'object':  # If the result is a single column of numeric values
        min_val = e.min()
        max_val = e.max()
        mean_val = e.mean()
        median_val = e.median()
        std_dev = e.std()
        q1 = e.quantile(0.25)
        q3 = e.quantile(0.75)
        variance = e.var()
        skewness = e.skew()
        kurtosis = e.kurt()
        stats_info = {
            'min': min_val,
            'max': max_val,
            'mean': mean_val,
            'median': median_val,
            'std_dev': std_dev,
            'q1 (25%)': q1,
            'q3 (75%)': q3,
            'variance': variance,
            'skewness': skewness,
            'kurtosis': kurtosis
        }
        print(f'{hint}, rows: {len(dframe)} :stats: {stats_info}  ==> {e}')
        print("====" * 20)
        return stats_info
    else:
        print(f'{hint}, rows: {len(dframe)} : {e}')
        print("====" * 20)
        return e


def dataframe_to_markdown_bold_header(df: pd.DataFrame):
        """
        Convert a Pandas DataFrame into a Markdown table format with bold headers.

        :param df: Pandas DataFrame
        :return: String in Markdown table format with bold headers
        """
        # Create the header row with bold headers
        header = '| ' + ' | '.join(f"**{col}**" for col in df.columns) + ' |'
        separator = '| ' + ' | '.join(['---'] * len(df.columns)) + ' |'

        # Create the data rows
        rows = df.apply(lambda row: '| ' + ' | '.join(map(str, row)) + ' |', axis=1).tolist()

        # Combine everything into a markdown table
        markdown_table = '\n'.join([header, separator] + rows)

        return markdown_table



def load_and_convert_dates(df):
    if df is None or df.empty:
        print("DataFrame is None or empty.")
        return df
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                # Try converting the column to datetime
                converted_col = pd.to_datetime(df[col], errors='coerce')

                if converted_col.notna().sum() > 0.5 * len(df):
                    df[col] = converted_col  # Keep the datetime conversion
                else:
                    df[col] = df[col]  # Revert back to the original column
            except Exception as e:
                print(f"Error converting column {col} to datetime: {e}")

    return df


def eval_expres_simple(dframe, hint, exp):
    e = eval(exp)
    print(f'{hint}, rows: {len(dframe)} : {e}')


if __name__ == '__main__':

    # Example 1
    dfx = pd.read_csv('employee_salary.csv')
    eval_expres_simple_dynamic_df(dframe=dfx, hint="Who is having less salary?", exp="df.loc[df['salary'].idxmin()]")

    # Example 2
    df2 = pd.read_csv("products.csv")
    eval_expres_simple_dynamic_df(dframe=df2, hint="Which product had highest sales?",
                                  exp="df.loc[df['sales'].idxmax()]['product_name']")

    df2 = pd.read_csv('employee_salary.csv')
    print(df2.head())
    expes = "df.groupby('country')['salary'].mean()"

    eval_expres(dframe=df2, hint="show me average salary distribution",
                exp="df.groupby('salary')['salary'].count() / len(df)")

    eval_expres(dframe=df2, hint="show me top 10 salaries", exp="df.nlargest(10, 'salary')")

    eval_expres(dframe=df2, hint="show me top 10 salaries group by country order by age",
                exp="df.sort_values(by=['country', 'age'], ascending=True).groupby('country')['salary'].nlargest(10)")

    eval_expres(dframe=df2, hint="Which country has the most employees?", exp="df['country'].value_counts().index[0]")

    eval_expres(dframe=df2, hint="Which country has the least employees?", exp="df['country'].value_counts().index[-1]")

    eval_expres(dframe=df2, hint="Can you compare salaries by gender?", exp="df.groupby('gender')['salary'].mean()")

    eval_expres(dframe=df2, hint="What is the median salary by age?", exp="df.groupby('age')['salary'].median()")
    eval_expres(dframe=df2, hint="What is the salary trend by age?", exp="df.groupby('age')['salary'].mean()")

    eval_expres(dframe=df2, hint="who is having max salary?", exp="df.loc[df['salary'].idxmax()]")

    eval_expres(dframe=df2, hint="who is having less salary?", exp="df.loc[df['salary'].idxmin()]")

    result1 = eval_expres(dframe=df2, hint="What is the median salary by age?",
                          exp="df.groupby('age')['salary'].median()")

    # Check the result structure
    if result1.is_successful():
        if result1.has_min_max():
            print(f"Min: {result1.min_val}, Max: {result1.max_val}")
        if not result1.is_data_empty():
            print(f"Data: {result1.data}")
    else:
        print(f"Error: {result1.error}")

    dfx = pd.read_csv("products.csv")
    eval_expres(dframe=dfx, hint="Which product had highest sales?", exp="df.loc[df['sales'].idxmax()]['product_name']")

    eval_expres(dframe=dfx, hint="all products sales between 6000-6500",
                exp="df[(df['sales'] > 6000) & (df['sales'] < 6500)]")

    eval_expres(dframe=dfx, hint="all products sales between 6000-6500 and year range 2010 to 2011 where state is CA",
                exp="df[(df['sales'] > 6000) & (df['sales'] < 6500) & (df['year'] > 2010) & (df['year'] < 2012) & (df['state'] == 'CA')]")

    eval_expres(dframe=dfx, hint="all products sales between 6000-6500 where  state DC and year range 1990 to 2000",
                exp="df[(df['sales'] > 6000) & (df['sales'] < 6500) & (df['state'] == 'DC') & (df['year'] > 1990) & (df['year'] < 2001)]")

    eval_expres(dframe=dfx,
                hint="average sales of all products sales between 6000-6500 in state DC  and CA over the past 5 years",
                exp="df[(df['sales'] > 6000) & (df['sales'] < 6500) & (df['state'].isin(['DC', 'CA'])) & (df['year'] > df['year'].max() - 5)].groupby('product_name')['sales'].mean()")
    eval_expres(dframe=dfx, hint="display all unique product names", exp="df['product_name'].unique()")

    eval_expres(dframe=dfx, hint="display trending product names over the past 5 years based on sales",
                exp="df[df['year'] > df['year'].max() - 5].groupby('product_name')['sales'].sum().sort_values(ascending=False).index")

    eval_expres(dframe=dfx, hint="display top 5 trending product names over the past 5 years based on sales",
                exp="df[df['year'] > df['year'].max() - 5].groupby('product_name')['sales'].sum().sort_values(ascending=False).head(5).index")

    dfy = pd.read_excel('visitors_new.xlsx', engine='openpyxl')
    dfy = load_and_convert_dates(dfy)
    eval_expres(dframe=dfy, hint="display top 5 trending product names over the past 5 years based on sales",
                exp="df[(df['City'] == 'Fresno') & (df['Date'].dt.year > 2020)].shape[0]")

    dfz = pd.read_csv("Restaurant_Orders.csv")
    dfz = load_and_convert_types(df= dfz)

    eval_expres(dframe=dfz, hint="what is the total amount of revenue generated through the sales of  Sandwich?",exp=" df[df['Item Name'] == 'Sandwich']['Total Price (INR)'].sum() ")
