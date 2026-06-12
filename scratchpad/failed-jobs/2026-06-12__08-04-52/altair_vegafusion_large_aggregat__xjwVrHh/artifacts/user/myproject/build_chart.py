import altair as alt
import pandas as pd
import random
import os

def main():
    # Set up random seed
    random.seed(42)
    
    # Generate data
    n_rows = 60000
    x = [random.randint(0, 99) for _ in range(n_rows)]
    y = [random.randint(0, 49) for _ in range(n_rows)]
    z = [random.random() for _ in range(n_rows)]
    
    df = pd.DataFrame({'x': x, 'y': y, 'z': z})
    
    # Enable vegafusion
    alt.data_transformers.enable('vegafusion')
    
    # Build chart
    chart = alt.Chart(df).mark_rect().encode(
        x=alt.X('x:Q', bin=alt.Bin(maxbins=20)),
        y=alt.Y('y:Q', bin=alt.Bin(maxbins=20)),
        color=alt.Color('z:Q', aggregate='mean', scale=alt.Scale(scheme='magma'))
    )
    
    # Save chart
    chart.save('/home/user/myproject/chart.html')
    
    # Extract transformed data
    transformed_df = chart.transformed_data()
    
    # Save transformed data to CSV
    transformed_df.to_csv('/home/user/myproject/transformed_data.csv', index=False)

if __name__ == '__main__':
    main()
