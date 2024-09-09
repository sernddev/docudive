import pandas as pd
import numpy as np


class EvalResult:
    def __init__(self, hint, data=None, min_val=None, max_val=None, info=None, error=None):
        self.hint = hint
        self.data = data
        self.min_val = min_val
        self.max_val = max_val
        self.info = info
        self.error = error

    def is_successful(self):
        return self.error is None

    def has_min_max(self):
        return self.min_val is not None and self.max_val is not None

    def is_data_empty(self):
        return self.data.empty if isinstance(self.data, pd.DataFrame) else len(self.data) == 0

    def __repr__(self):
        if self.is_successful():
            return f"EvalResult(hint={self.hint}, min_val={self.min_val}, max_val={self.max_val}, info={self.info})"
        else:
            return f"EvalResult(hint={self.hint}, error={self.error})"


def eval_expres_simple_dynamic_df(dframe, hint, exp):
    # Use eval with locals() to inject dframe into the evaluated expression
    e = eval(exp, {"pd": pd}, {"df": dframe})  # Here we explicitly pass 'df' as 'dframe' to the eval
    print(f'{hint}, rows: {len(dframe)} : {e}')





def eval_expres(dframe, hint, exp):
    print("====" * 20)
    try:
        e = eval(exp, {"pd": pd}, {"df": dframe})
        if isinstance(e, pd.Series) and e.dtype != 'object':  # If the result is a single column of numeric values
            min_val = e.min()
            max_val = e.max()

            # Convert Series to DataFrame and append min and max
            df_e = e.to_frame(name='value')
            # df_e['min'] = min_val
            # df_e['max'] = max_val

            print(f'{hint}, rows: {len(dframe)} : min: {min_val}, max: {max_val} ==> {e}')
            print("====" * 20)
            return EvalResult(hint, data=df_e, min_val=min_val, max_val=max_val, info=f'Successfully executed {exp}')

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
        print(f'{hint}, rows: {len(dframe)} : min:{min_val}, max:{max_val}  ==> {e}')
        print("====" * 20)
        return (e, min_val, max_val)
    else:
        print(f'{hint}, rows: {len(dframe)} : {e}')
        print("====" * 20)
        return e


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

    result1 = eval_expres(dframe=df2, hint="What is the median salary by age?", exp="df.groupby('age')['salary'].median()")

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

    eval_expres(dframe=dfx,hint="all products sales between 6000-6500",exp= "df[(df['sales'] > 6000) & (df['sales'] < 6500)]")

    eval_expres(dframe=dfx,hint="all products sales between 6000-6500 and year range 2010 to 2011 where state is CA", exp="df[(df['sales'] > 6000) & (df['sales'] < 6500) & (df['year'] > 2010) & (df['year'] < 2012) & (df['state'] == 'CA')]")

    eval_expres(dframe=dfx, hint="all products sales between 6000-6500 where  state DC and year range 1990 to 2000", exp="df[(df['sales'] > 6000) & (df['sales'] < 6500) & (df['state'] == 'DC') & (df['year'] > 1990) & (df['year'] < 2001)]")

    eval_expres(dframe=dfx, hint="average sales of all products sales between 6000-6500 in state DC  and CA over the past 5 years",exp="df[(df['sales'] > 6000) & (df['sales'] < 6500) & (df['state'].isin(['DC', 'CA'])) & (df['year'] > df['year'].max() - 5)].groupby('product_name')['sales'].mean()")
    eval_expres(dframe=dfx, hint="display all unique product names", exp="df['product_name'].unique()")

    eval_expres(dframe=dfx, hint="display trending product names over the past 5 years based on sales", exp="df[df['year'] > df['year'].max() - 5].groupby('product_name')['sales'].sum().sort_values(ascending=False).index")

    eval_expres(dframe=dfx, hint="display top 5 trending product names over the past 5 years based on sales",exp="df[df['year'] > df['year'].max() - 5].groupby('product_name')['sales'].sum().sort_values(ascending=False).head(5).index")