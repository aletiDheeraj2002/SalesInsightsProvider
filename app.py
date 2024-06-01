from flask import Flask, render_template, request, send_file


app = Flask(__name__)
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download')
def download_file():
    file_path = 'templates/random_data.csv'
    return send_file(file_path, as_attachment=True, download_name='data.csv')

@app.route('/analyze', methods=['POST'])
def analyze():
    import pandas as pd
    import plotly.graph_objects as go
    import plotly.express as px
    import matplotlib
    matplotlib.use('Agg')
    uploaded_file = request.files['csv_file']
    if uploaded_file.filename != '':
        all_data = pd.read_csv(uploaded_file)
    all_data.head()
    all_data = all_data.dropna(how='all')
    all_data.head()
    all_data = all_data[all_data['Order Date'].str[0:2]!='Or']
    all_data['Quantity Ordered'] = pd.to_numeric(all_data['Quantity Ordered'])
    all_data['Price Each'] = pd.to_numeric(all_data['Price Each'])
    all_data['Month']=all_data['Order Date'].str[0:2]
    all_data['Month'] = all_data['Month'].astype('int32')
    all_data.head()
    all_data['Month 2'] = pd.to_datetime(all_data['Order Date'], format='%m/%d/%y %H:%M').dt.month
    all_data.head()
    all_data['City'] = all_data['Purchase Address']
    all_data['Sales'] = all_data['Quantity Ordered'].astype('int') * all_data['Price Each'].astype('float')
    monthly_sales = all_data.groupby(['Month']).sum()
    fig1 = px.bar(monthly_sales, x=monthly_sales.index, y='Sales',
                title='Total Sales as per month', labels={'x':'Month number', 'y':'Sales in Rupees'})
    html_fig1 = fig1.to_html()
    city_sales = all_data.groupby('City').sum()['Sales']
    fig2 = px.bar(x=city_sales.index, y=city_sales.values,
                title='Total Sales by City',
                labels={'x':'City', 'y':'Total Sales'})
    fig2.update_layout(xaxis_tickangle=-45)
    html_fig2 = fig2.to_html()
    all_data['Order Date'] = pd.to_datetime(all_data['Order Date'], format='%m/%d/%y %H:%M')
    all_data['Hour'] = all_data['Order Date'].dt.hour
    all_data['Minute'] = all_data['Order Date'].dt.minute
    orders_per_hour = all_data.groupby('Hour').size().reset_index(name='Count')
    fig3 = px.bar(orders_per_hour, x='Hour', y='Count',
                labels={'x':'Hour', 'y':'Number of Orders'},
                title='Number of Orders at Each Hour')
    fig3.update_layout(xaxis=dict(tickvals=list(range(24))))
    html_fig3 = fig3.to_html()
    product_group = all_data.groupby('Product')
    keys = [str(pair) for pair, df in product_group]
    all_data['Order Date'] = pd.to_datetime(all_data['Order Date'], format='%m/%d/%y %H:%M')
    all_data['Quantity Ordered'] = pd.to_numeric(all_data['Quantity Ordered'], errors='coerce')
    all_data = all_data.dropna(subset=['Quantity Ordered'])
    quantity_ordered = all_data.groupby('Product')['Quantity Ordered'].sum().reset_index()
    fig = px.bar(quantity_ordered, 
                x='Product', 
                y='Quantity Ordered',
                title='Quantity Ordered by Product',
                color='Product',
                color_discrete_sequence=['skyblue'] * len(quantity_ordered))
    fig.update_layout(xaxis_tickangle=-45)
    html_fig4 = fig.to_html()
    all_data['Quantity Ordered'] = pd.to_numeric(all_data['Quantity Ordered'])
    all_data['Price Each'] = pd.to_numeric(all_data['Price Each'])
    all_data['Profit'] = all_data['Quantity Ordered'] * all_data['Price Each']
    product_profit = all_data.groupby('Product')['Profit'].sum().reset_index()
    top_10_products = product_profit.nlargest(10, 'Profit')
    fig = px.bar(top_10_products, 
                x='Product', 
                y='Profit',
                title='Products by Profit',
                color='Product',
                color_discrete_sequence=['skyblue'] * 10)
    fig.update_layout(xaxis_tickangle=-45)
    html_fig6 = fig.to_html()
    all_data['Quantity Ordered'] = pd.to_numeric(all_data['Quantity Ordered'])
    category_sales = all_data.groupby('Category')['Quantity Ordered'].sum().reset_index()
    fig = px.pie(category_sales, 
                names='Category', 
                values='Quantity Ordered',
                title='Most Selling Category',
                color_discrete_sequence=['skyblue', 'lightcoral', 'lightgreen'],
                hole=0.3)

    plot7 = fig.to_html()

    prices = all_data.groupby('Product')['Price Each'].mean().reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=keys,
        y=all_data['Quantity Ordered'],
        name='Quantity Ordered',
        marker=dict(color='skyblue')
    ))
    fig.add_trace(go.Scatter(
        x=keys,
        y=prices['Price Each'],
        name='Price ($)',
        mode='lines',
        yaxis='y2',
        line=dict(color='blue')
    ))
    fig.update_layout(
        title='Quantity Ordered and Price by Product',
        xaxis=dict(title='Product Name', tickvals=list(range(len(keys))), ticktext=keys),
        yaxis=dict(title='Quantity Ordered', side='left', color='skyblue', showgrid=False),
        yaxis2=dict(title='Price ($)', overlaying='y', side='right', color='blue', showgrid=False),
        legend=dict(x=0, y=1, traceorder='normal')
    )
    html_fig5 = fig.to_html()
    df = all_data[all_data['Order ID'].duplicated(keep=False)]
    df.loc[:, 'Grouped'] = df.groupby('Order ID')['Product'].transform(lambda x: ','.join(x))
    df2 = df[['Order ID', 'Grouped']].drop_duplicates()
    from itertools import combinations
    from collections import Counter
    count = Counter()
    for row in df2['Grouped']:
        row_list = row.split(',')
        count.update(Counter(combinations(row_list, 2)))
    df = pd.DataFrame(count.items(), columns=['Product Pair', 'Count'])
    df[['Product 1', 'Product 2']] = pd.DataFrame(df['Product Pair'].tolist(), index=df.index)
    df.drop(columns=['Product Pair'], inplace=True)
    fig = go.Figure(data=[go.Scatter(x=df['Product 1'],
                                    y=df['Product 2'],
                                    mode='markers',
                                    marker=dict(size=10 * df['Count']))])
    fig.update_layout(title='Products Frequently Purchased Together',
                    xaxis_title='Product 1',
                    yaxis_title='Product 2')
    html_fig8 = fig.to_html()
    return render_template('result.html', plot=html_fig1,plot2=html_fig2, plot3=html_fig3,plot4=html_fig4,plot8=html_fig8,plot5=html_fig5,plot6=html_fig6,plot7=plot7)

if __name__ == '__main__':
    app.run()
